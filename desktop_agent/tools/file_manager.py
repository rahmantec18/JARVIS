import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from desktop_agent.security.authorizer import authorizer

try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False

KNOWN_FOLDERS: Dict[str, Path] = {
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
    "screenshots": Path(__file__).resolve().parent.parent.parent / "screenshots",
    "notes": Path(__file__).resolve().parent.parent.parent / "notes",
    "project": Path(__file__).resolve().parent.parent.parent,
}


def _resolve_folder_target(folder_name_or_path: Optional[str]) -> Path:
    """Resolve a directory string or alias (e.g. 'Downloads', 'Documents') to a Path object."""
    if not folder_name_or_path:
        return Path.cwd()

    clean = folder_name_or_path.lower().strip()
    if clean in KNOWN_FOLDERS:
        return KNOWN_FOLDERS[clean]

    p = Path(folder_name_or_path).resolve()
    return p


def search_files(
    query: str,
    base_dir: Optional[str] = None,
    extension: Optional[str] = None,
    min_size_mb: Optional[float] = None,
    max_results: int = 30
) -> Dict[str, Any]:
    """
    Search for files by query, extension, and size filters across known Windows directories.
    Ranks candidates by exact match, recency, and size.
    """
    clean_query = query.strip()
    target_dir = _resolve_folder_target(base_dir or "project")

    # If base_dir not allowed, fall back to current project directory
    if not authorizer.is_path_allowed(target_dir):
        target_dir = Path.cwd()

    # Pattern handling
    if extension and not extension.startswith("."):
        extension = f".{extension}"

    matches: List[Dict[str, Any]] = []

    try:
        # Search target directory recursively
        for root, dirs, files in os.walk(target_dir):
            # Prune noisy folders
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", ".venv", "__pycache__", "$RECYCLE.BIN"]]

            for f in files:
                f_lower = f.lower()
                # Extension check
                if extension and not f_lower.endswith(extension.lower()):
                    continue

                # Query check
                if clean_query and clean_query.lower() not in f_lower:
                    continue

                full_path = Path(root) / f
                try:
                    st = full_path.stat()
                    size_mb = round(st.st_size / (1024 * 1024), 2)
                    if min_size_mb is not None and size_mb < min_size_mb:
                        continue

                    matches.append({
                        "name": f,
                        "path": str(full_path),
                        "size_mb": size_mb,
                        "size_kb": round(st.st_size / 1024, 2),
                        "modified": st.st_mtime
                    })
                except Exception:
                    pass

                if len(matches) >= max_results * 2:
                    break

            if len(matches) >= max_results * 2:
                break

        # Sort matches by recency (most recent first)
        matches.sort(key=lambda m: m["modified"], reverse=True)
        final_matches = matches[:max_results]

        return {
            "success": True,
            "query": clean_query,
            "base_dir": str(target_dir),
            "count": len(final_matches),
            "files": final_matches,
            "top_match": final_matches[0]["path"] if final_matches else None
        }

    except Exception as e:
        return {"success": False, "error": str(e), "files": []}


def create_directory(folder_name: str, parent_folder: Optional[str] = "documents") -> Dict[str, Any]:
    """Create a new folder in Documents, Desktop, or a specified path."""
    clean_name = folder_name.strip()
    parent_path = _resolve_folder_target(parent_folder)
    target = parent_path / clean_name

    try:
        target.mkdir(parents=True, exist_ok=True)
        return {
            "success": True,
            "path": str(target),
            "name": clean_name,
            "message": f"Successfully created folder '{clean_name}' in {parent_path.name}."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to create directory: {str(e)}"}


def rename_item(src_path: str, new_name: str) -> Dict[str, Any]:
    """Rename a file or folder."""
    src = Path(src_path).resolve()
    if not src.exists():
        return {"success": False, "error": f"Target '{src_path}' does not exist."}

    dst = src.parent / new_name.strip()
    try:
        src.rename(dst)
        return {
            "success": True,
            "old_path": str(src),
            "new_path": str(dst),
            "message": f"Renamed '{src.name}' to '{new_name}'."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to rename: {str(e)}"}


def copy_item(src_path: str, dst_path: str) -> Dict[str, Any]:
    """Copy a file or directory."""
    src = Path(src_path).resolve()
    dst = Path(dst_path).resolve()
    if not src.exists():
        return {"success": False, "error": f"Source '{src_path}' does not exist."}

    try:
        if src.is_file():
            if dst.is_dir():
                dst = dst / src.name
            shutil.copy2(src, dst)
        else:
            shutil.copytree(src, dst, dirs_exist_ok=True)
        return {"success": True, "source": str(src), "destination": str(dst), "message": f"Successfully copied '{src.name}'."}
    except Exception as e:
        return {"success": False, "error": f"Copy failed: {str(e)}"}


def move_item(src_path: str, dst_path: str) -> Dict[str, Any]:
    """Move a file or directory."""
    src = Path(src_path).resolve()
    dst = Path(dst_path).resolve()
    if not src.exists():
        return {"success": False, "error": f"Source '{src_path}' does not exist."}

    try:
        shutil.move(str(src), str(dst))
        return {"success": True, "source": str(src), "destination": str(dst), "message": f"Successfully moved '{src.name}' to '{dst.name}'."}
    except Exception as e:
        return {"success": False, "error": f"Move failed: {str(e)}"}


def read_file(file_path: str, max_chars: int = 8000) -> Dict[str, Any]:
    """Read an approved file."""
    p = Path(file_path).resolve()
    if not authorizer.is_path_allowed(p):
        return {
            "success": False,
            "error": f"Access denied: file '{file_path}' is outside approved directories."
        }

    if not p.is_file():
        return {"success": False, "error": f"File '{file_path}' does not exist or is not a regular file."}

    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars + 1)
        truncated = len(content) > max_chars
        return {
            "success": True,
            "file_name": p.name,
            "path": str(p),
            "content": content[:max_chars],
            "size_bytes": p.stat().st_size,
            "truncated": truncated
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """Write or overwrite a file at any permitted system path."""
    p = Path(file_path).resolve()
    if not authorizer.is_path_allowed(p):
        return {
            "success": False,
            "error": f"Access denied: file '{file_path}' is outside permitted directories."
        }

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "success": True,
            "file_name": p.name,
            "path": str(p),
            "bytes_written": len(content.encode("utf-8")),
            "message": f"Successfully wrote file '{p.name}' ({len(content)} characters)."
        }
    except Exception as e:
        return {"success": False, "error": f"Write error: {str(e)}"}


def write_note(title: str, content: str, folder: str = "notes") -> Dict[str, Any]:
    """Write a markdown note file."""
    notes_dir = (Path.cwd() / folder).resolve()
    notes_dir.mkdir(parents=True, exist_ok=True)

    if not authorizer.is_path_allowed(notes_dir):
        return {
            "success": False,
            "error": "Access denied: notes directory is outside approved paths."
        }

    clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
    if not clean_title:
        clean_title = "Quick-Note"
    file_path = notes_dir / f"{clean_title}.md"

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n*Created via J.A.R.V.I.S. Command Matrix*\n\n{content}\n")
        return {
            "success": True,
            "file_name": file_path.name,
            "path": str(file_path),
            "message": f"Note '{file_path.name}' saved to {folder}."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to save note: {str(e)}"}


def list_directory(dir_path: str = ".") -> Dict[str, Any]:
    """List contents of a directory."""
    p = Path(dir_path).resolve()
    if not authorizer.is_path_allowed(p):
        return {
            "success": False,
            "error": f"Access denied: path '{dir_path}' is outside permitted directories."
        }

    if not p.is_dir():
        return {"success": False, "error": f"Path '{dir_path}' is not a directory."}

    try:
        entries = []
        for item in p.iterdir():
            entries.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size_bytes": item.stat().st_size if item.is_file() else None,
                "modified": item.stat().st_mtime
            })
        return {
            "success": True,
            "path": str(p),
            "count": len(entries),
            "items": entries[:50]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def reveal_in_explorer(target_path: str) -> Dict[str, Any]:
    """Open Windows Explorer highlighting the specified file or folder."""
    p = Path(target_path).resolve()
    try:
        if p.is_file():
            subprocess.Popen(f'explorer /select,"{p}"', shell=True)
        else:
            subprocess.Popen(f'explorer "{p}"', shell=True)
        return {"success": True, "path": str(p), "message": f"Revealed '{p.name}' in Windows Explorer."}
    except Exception as e:
        return {"success": False, "error": f"Failed to reveal in Explorer: {str(e)}"}


def delete_item(target: str) -> Dict[str, Any]:
    """
    Safely delete a file or directory by sending to the Windows Recycle Bin (preferred)
    or clearing temp files / recycle bin upon explicit command.
    """
    clean = target.strip()
    if not clean:
        return {"success": False, "error": "Target name or path required to delete."}

    lower = clean.lower()

    # 1. Recycle Bin Emptying
    if lower in ["recycle bin", "trash", "empty recycle bin", "empty bin", "clear recycle bin", "clear trash", "empty trash"]:
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                capture_output=True,
                timeout=6
            )
            return {"success": True, "target": target, "message": "Windows Recycle Bin emptied successfully."}
        except Exception as e:
            return {"success": False, "error": f"Failed to empty Recycle Bin: {str(e)}"}

    # 2. Screenshots
    if lower in ["screenshot", "screenshots", "all screenshots", "last screenshot", "latest screenshot"]:
        repo_root = Path(__file__).resolve().parent.parent.parent
        screenshots_dir = repo_root / "screenshots"
        if not screenshots_dir.exists():
            return {"success": True, "message": "No screenshots found to delete."}

        png_files = sorted(screenshots_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not png_files:
            return {"success": True, "message": "No screenshot files in directory."}

        if lower in ["last screenshot", "latest screenshot", "screenshot"]:
            target_file = png_files[0]
            if HAS_SEND2TRASH:
                send2trash(str(target_file))
            else:
                target_file.unlink(missing_ok=True)
            return {"success": True, "message": f"Moved latest screenshot '{target_file.name}' to Recycle Bin."}
        else:
            count = len(png_files)
            for f in png_files:
                if HAS_SEND2TRASH:
                    send2trash(str(f))
                else:
                    f.unlink(missing_ok=True)
            return {"success": True, "message": f"Moved all {count} screenshot files to Recycle Bin."}

    # 3. Direct path if exists
    p = Path(clean).resolve()
    if p.exists():
        name = p.name
        if HAS_SEND2TRASH:
            send2trash(str(p))
            return {"success": True, "path": str(p), "message": f"Moved '{name}' to Recycle Bin."}
        else:
            if p.is_file():
                p.unlink(missing_ok=True)
            else:
                shutil.rmtree(p, ignore_errors=True)
            return {"success": True, "path": str(p), "message": f"Deleted '{name}' successfully."}

    # 4. Search in common folders
    search_res = search_files(clean, base_dir="project", max_results=5)
    if search_res.get("files"):
        first_match = Path(search_res["files"][0]["path"])
        name = first_match.name
        if HAS_SEND2TRASH:
            send2trash(str(first_match))
            return {"success": True, "path": str(first_match), "message": f"Moved '{name}' to Recycle Bin."}
        else:
            first_match.unlink(missing_ok=True)
            return {"success": True, "path": str(first_match), "message": f"Deleted '{name}'."}

    return {
        "success": False,
        "error": f"Item '{clean}' was not found. Please specify the exact name or path."
    }
