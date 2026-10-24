from datetime import datetime
from app.tools.registry import tool_registry
from app.tools.calculator import calculate
from app.tools.system_status import get_system_status
from app.tools.web_search import search_web
from app.tools.file_ops import search_allowed_files, read_selected_file, create_note
from app.tools.desktop_bridge import (
    open_approved_app,
    open_website,
    launch_custom_application,
    run_powershell_command,
    control_system_volume,
    capture_desktop_screenshot,
    read_system_clipboard,
    write_system_clipboard,
    list_system_processes,
    kill_system_process,
    lock_windows_workstation,
    open_system_settings,
    write_system_file,
    list_system_directory,
    reveal_file_in_explorer,
    send_whatsapp_message,
    delete_system_item,
    launch_companion_hud,
    play_spotify_music,
    pause_spotify_music,
    resume_spotify_music,
    skip_spotify_track,
    previous_spotify_track,
    control_media_playback,
    activate_desktop_window,
    set_desktop_window_state,
    create_desktop_directory,
    rename_desktop_item,
    copy_desktop_item,
    move_desktop_item
)


def get_current_time() -> dict:
    """Get the current system local date and time."""
    now = datetime.now()
    return {
        "datetime": now.isoformat(),
        "formatted": now.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
        "timestamp": now.timestamp()
    }


def register_all_tools():
    """Register all available tools with the tool registry."""
    # Calculator
    tool_registry.register(
        name="calculate",
        description="Safely evaluate a mathematical or scientific expression (e.g. '25 * 40 + sqrt(144)').",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        },
        requires_approval=False,
        category="computation"
    )(calculate)

    # System Status
    tool_registry.register(
        name="get_system_status",
        description="Retrieve real hardware status (CPU usage %, RAM memory, Disk space, Battery %, Uptime).",
        parameters={
            "type": "object",
            "properties": {}
        },
        requires_approval=False,
        category="system"
    )(get_system_status)

    # Current Time
    tool_registry.register(
        name="get_current_time",
        description="Retrieve current date, day of week, and time.",
        parameters={
            "type": "object",
            "properties": {}
        },
        requires_approval=False,
        category="system"
    )(get_current_time)

    # Web Search
    tool_registry.register(
        name="search_web",
        description="Search the web for up-to-date information, facts, or technical documentation.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string"
                }
            },
            "required": ["query"]
        },
        requires_approval=False,
        category="research"
    )(search_web)

    # Search Allowed Files
    tool_registry.register(
        name="search_allowed_files",
        description="Search for files by filename pattern within authorized project directories.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search pattern or partial file name"
                },
                "root_dir": {
                    "type": "string",
                    "description": "Starting directory (defaults to current project root '.')",
                    "default": "."
                }
            },
            "required": ["query"]
        },
        requires_approval=False,
        category="files"
    )(search_allowed_files)

    # Read Selected File
    tool_registry.register(
        name="read_selected_file",
        description="Read the text content of an approved project file.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative or absolute path of the file to inspect"
                }
            },
            "required": ["file_path"]
        },
        requires_approval=False,
        category="files"
    )(read_selected_file)

    # Create Note
    tool_registry.register(
        name="create_note",
        description="Create a markdown note or document in the approved notes directory.",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the note"
                },
                "content": {
                    "type": "string",
                    "description": "Markdown formatted content of the note"
                }
            },
            "required": ["title", "content"]
        },
        requires_approval=False,
        category="files"
    )(create_note)

    # Open Approved App
    tool_registry.register(
        name="open_approved_app",
        description="Open an application (e.g., 'notepad', 'calc', 'explorer', 'code', 'chrome', 'spotify', 'terminal').",
        parameters={
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "Identifier of the application"
                }
            },
            "required": ["app_id"]
        },
        requires_approval=False,
        category="desktop"
    )(open_approved_app)

    # Open Website
    tool_registry.register(
        name="open_website",
        description="Open an approved URL in the default Windows web browser or specified browser.",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Safe HTTP or HTTPS URL to open"
                },
                "browser": {
                    "type": "string",
                    "description": "Optional browser executable or name (e.g. 'chrome')"
                }
            },
            "required": ["url"]
        },
        requires_approval=False,
        category="desktop"
    )(open_website)

    # Run PowerShell Command
    tool_registry.register(
        name="run_powershell_command",
        description="Execute a PowerShell or command line instruction on the Windows host and return its output.",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The PowerShell command or script block to run"
                }
            },
            "required": ["command"]
        },
        requires_approval=False,
        category="desktop"
    )(run_powershell_command)

    # Control Volume
    tool_registry.register(
        name="control_system_volume",
        description="Control Windows audio volume (actions: 'up', 'down', 'mute', 'unmute').",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Volume action ('up', 'down', 'mute', 'unmute')"
                }
            },
            "required": ["action"]
        },
        requires_approval=False,
        category="desktop"
    )(control_system_volume)

    # Capture Screenshot
    tool_registry.register(
        name="capture_desktop_screenshot",
        description="Capture full screenshot of the user's primary monitor and save it to disk.",
        parameters={
            "type": "object",
            "properties": {}
        },
        requires_approval=False,
        category="desktop"
    )(capture_desktop_screenshot)

    # Read Clipboard
    tool_registry.register(
        name="read_system_clipboard",
        description="Read current text from the Windows clipboard.",
        parameters={
            "type": "object",
            "properties": {}
        },
        requires_approval=False,
        category="desktop"
    )(read_system_clipboard)

    # Write Clipboard
    tool_registry.register(
        name="write_system_clipboard",
        description="Copy text to the Windows clipboard.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to set on the clipboard"
                }
            },
            "required": ["text"]
        },
        requires_approval=False,
        category="desktop"
    )(write_system_clipboard)

    # List Running Processes
    tool_registry.register(
        name="list_system_processes",
        description="List active Windows processes and their memory consumption.",
        parameters={
            "type": "object",
            "properties": {
                "filter_name": {
                    "type": "string",
                    "description": "Optional name filter for the process (e.g. 'chrome')"
                }
            }
        },
        requires_approval=False,
        category="system"
    )(list_system_processes)

    # Kill Process
    tool_registry.register(
        name="kill_system_process",
        description="Terminate a specific hung or runaway process by name or PID.",
        parameters={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Process name (e.g. 'notepad.exe') or PID number"
                }
            },
            "required": ["target"]
        },
        requires_approval=False,
        category="system"
    )(kill_system_process)

    # Lock Workstation
    tool_registry.register(
        name="lock_windows_workstation",
        description="Lock the Windows computer session.",
        parameters={
            "type": "object",
            "properties": {}
        },
        requires_approval=False,
        category="desktop"
    )(lock_windows_workstation)

    # Open Settings
    tool_registry.register(
        name="open_system_settings",
        description="Open Windows Settings application.",
        parameters={
            "type": "object",
            "properties": {
                "page": {
                    "type": "string",
                    "description": "Optional settings subpage (e.g. 'network', 'sound', 'windowsupdate')"
                }
            }
        },
        requires_approval=False,
        category="desktop"
    )(open_system_settings)

    # Launch Custom App
    tool_registry.register(
        name="launch_custom_application",
        description="Launch any program, file, or shortcut on the Windows PC by name or path.",
        parameters={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Name or full path of application to open"
                }
            },
            "required": ["target"]
        },
        requires_approval=False,
        category="desktop"
    )(launch_custom_application)

    # Write File
    tool_registry.register(
        name="write_system_file",
        description="Create or overwrite any file on the system.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path of the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content of the file"
                }
            },
            "required": ["file_path", "content"]
        },
        requires_approval=False,
        category="files"
    )(write_system_file)

    # List Directory
    tool_registry.register(
        name="list_system_directory",
        description="List files and subfolders within a folder.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Folder path to list (defaults to '.')"
                }
            }
        },
        requires_approval=False,
        category="files"
    )(list_system_directory)

    # Reveal in Explorer
    tool_registry.register(
        name="reveal_file_in_explorer",
        description="Open Windows Explorer and highlight the specified file or folder.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File or folder path to highlight"
                }
            },
            "required": ["path"]
        },
        requires_approval=False,
        category="files"
    )(reveal_file_in_explorer)

    # WhatsApp Messaging Automation
    tool_registry.register(
        name="send_whatsapp_message",
        description="Send or prepare a WhatsApp message to a contact or phone number.",
        parameters={
            "type": "object",
            "properties": {
                "contact": {
                    "type": "string",
                    "description": "Contact name or phone number"
                },
                "message": {
                    "type": "string",
                    "description": "Text message to send"
                }
            },
            "required": ["message"]
        },
        requires_approval=False,
        category="desktop"
    )(send_whatsapp_message)

    # Delete System Item (File, folder, screenshot, note, recycle bin)
    tool_registry.register(
        name="delete_system_item",
        description="Delete a file, folder, screenshot, note, or clear recycle bin/temp files.",
        parameters={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Name or path of file, folder, screenshot, or 'recycle bin' to delete"
                }
            },
            "required": ["target"]
        },
        requires_approval=False,
        category="desktop"
    )(delete_system_item)

    # Launch Floating Companion HUD
    tool_registry.register(
        name="launch_companion_hud",
        description="Launch the draggable always-on-top desktop companion voice HUD over all apps.",
        parameters={
            "type": "object",
            "properties": {}
        },
        requires_approval=False,
        category="desktop"
    )(launch_companion_hud)

    # Play Spotify Music
    tool_registry.register(
        name="play_spotify_music",
        description="Search for and immediately play a song, artist, album, or playlist on Spotify.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Song name, artist, album, or playlist to play (e.g. 'Believer by Imagine Dragons', 'Arabic Kuthu', 'workout playlist')"
                },
                "playlist": {
                    "type": "boolean",
                    "description": "True if the query refers to a playlist"
                }
            },
            "required": ["query"]
        },
        requires_approval=False,
        category="media"
    )(play_spotify_music)

    # Pause Spotify
    tool_registry.register(
        name="pause_spotify_music",
        description="Pause Spotify music playback.",
        parameters={"type": "object", "properties": {}},
        requires_approval=False,
        category="media"
    )(pause_spotify_music)

    # Resume Spotify
    tool_registry.register(
        name="resume_spotify_music",
        description="Resume Spotify music playback.",
        parameters={"type": "object", "properties": {}},
        requires_approval=False,
        category="media"
    )(resume_spotify_music)

    # Skip Spotify Track
    tool_registry.register(
        name="skip_spotify_track",
        description="Skip to the next song on Spotify.",
        parameters={"type": "object", "properties": {}},
        requires_approval=False,
        category="media"
    )(skip_spotify_track)

    # Previous Spotify Track
    tool_registry.register(
        name="previous_spotify_track",
        description="Play the previous song on Spotify.",
        parameters={"type": "object", "properties": {}},
        requires_approval=False,
        category="media"
    )(previous_spotify_track)

    # Control Media Playback
    tool_registry.register(
        name="control_media_playback",
        description="Control system media transport (play, pause, next, previous, stop).",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Media action: 'play', 'pause', 'next', 'previous', 'stop'"
                }
            },
            "required": ["action"]
        },
        requires_approval=False,
        category="media"
    )(control_media_playback)

    # Activate Desktop Window
    tool_registry.register(
        name="activate_desktop_window",
        description="Bring an existing application window to the foreground.",
        parameters={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Application name or window title to activate"
                }
            },
            "required": ["target"]
        },
        requires_approval=False,
        category="desktop"
    )(activate_desktop_window)

    # Set Desktop Window State
    tool_registry.register(
        name="set_desktop_window_state",
        description="Change window state: minimize, maximize, restore, or close.",
        parameters={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Application name or window title"
                },
                "state": {
                    "type": "string",
                    "description": "State: 'minimize', 'maximize', 'restore', 'close'"
                }
            },
            "required": ["target", "state"]
        },
        requires_approval=False,
        category="desktop"
    )(set_desktop_window_state)



    # Create Desktop Directory
    tool_registry.register(
        name="create_desktop_directory",
        description="Create a new folder in Documents, Desktop, or specified path.",
        parameters={
            "type": "object",
            "properties": {
                "folder_name": {"type": "string", "description": "Name of the new directory"},
                "parent_folder": {"type": "string", "description": "Parent directory (e.g. 'documents', 'desktop')"}
            },
            "required": ["folder_name"]
        },
        requires_approval=False,
        category="files"
    )(create_desktop_directory)

    # Rename Desktop Item
    tool_registry.register(
        name="rename_desktop_item",
        description="Rename a file or folder.",
        parameters={
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Original file/folder path or name"},
                "new_name": {"type": "string", "description": "New file or folder name"}
            },
            "required": ["src", "new_name"]
        },
        requires_approval=False,
        category="files"
    )(rename_desktop_item)

    # Copy Desktop Item
    tool_registry.register(
        name="copy_desktop_item",
        description="Copy a file or directory to a destination.",
        parameters={
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"}
            },
            "required": ["src", "dst"]
        },
        requires_approval=False,
        category="files"
    )(copy_desktop_item)

    # Move Desktop Item
    tool_registry.register(
        name="move_desktop_item",
        description="Move a file or directory to a destination.",
        parameters={
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"}
            },
            "required": ["src", "dst"]
        },
        requires_approval=False,
        category="files"
    )(move_desktop_item)



# Initialize tools immediately on module load
register_all_tools()
