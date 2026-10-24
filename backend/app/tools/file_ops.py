import os
import glob
from pathlib import Path
from typing import Dict, Any, List

# Allowed directory roots for safety
DEFAULT_ALLOWED_ROOTS = [
    Path(os.getcwd()).resolve(),
    (Path.home() / "Documents").resolve(),
    (Path.home() / "Desktop").resolve(),
]


def _is_safe_path(path: Path, allowed_roots: List[Path] = None) -> bool:
    """Check if the given path is within one of the approved root directories."""
    roots = allowed_roots or DEFAULT_ALLOWED_ROOTS
    try:
        resolved = path.resolve()
        for root in roots:
            if root == resolved or root in resolved.parents:
                return True
        return False
    except Exception:
        return False


def search_allowed_files(query: str, root_dir: str = ".") -> Dict[str, Any]:
    """Search for files matching a pattern in allowed project directories."""
    target_root = Path(root_dir).resolve()
    if not _is_safe_path(target_root):
        return {
            "success": False,
            "error": f"Access denied: directory '{root_dir}' is outside authorized directories."
        }

    matches = []
    # Search for files matching the pattern
    clean_query = query.strip()
    if not clean_query.startswith("*") and not "*" in clean_query:
        search_pattern = f"*{clean_query}*"
    else:
        search_pattern = clean_query

    for path in target_root.rglob(search_pattern):
        # Exclude hidden files, venv, and node_modules
        str_path = str(path)
        if any(ignored in str_path for ignored in [".git", ".venv", "node_modules", "__pycache__"]):
            continue
        if path.is_file():
            matches.append({
                "name": path.name,
                "path": str(path),
                "size_kb": round(path.stat().st_size / 1024, 2),
                "modified": path.stat().st_mtime
            })
        if len(matches) >= 30:
            break

    return {
        "success": True,
        "query": query,
        "root": str(target_root),
        "count": len(matches),
        "files": matches
    }


def read_selected_file(file_path: str, max_chars: int = 4000) -> Dict[str, Any]:
    """Read contents of an approved file."""
    path = Path(file_path).resolve()
    if not _is_safe_path(path):
        return {
            "success": False,
            "error": f"Security restriction: access to file '{file_path}' is denied. Outside allowed roots."
        }

    if not path.is_file():
        return {
            "success": False,
            "error": f"File '{file_path}' does not exist or is a directory."
        }

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars + 1)

        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars]

        return {
            "success": True,
            "file_name": path.name,
            "path": str(path),
            "content": content,
            "truncated": truncated,
            "size_bytes": path.stat().st_size
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}"
        }


def create_note(title: str, content: str, folder: str = "notes") -> Dict[str, Any]:
    """Create a note or document in the approved notes directory."""
    target_dir = (Path.cwd() / folder).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    if not _is_safe_path(target_dir):
        return {
            "success": False,
            "error": "Cannot create note: target directory is outside approved paths."
        }

    # Sanitize title for filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()
    if not safe_title:
        safe_title = "note"
    filename = f"{safe_title.replace(' ', '_')}.md"
    file_path = target_dir / filename

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{content}\n")

        return {
            "success": True,
            "title": title,
            "file_path": str(file_path),
            "file_name": filename
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write note: {str(e)}"
        }
