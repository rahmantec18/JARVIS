import json
import uuid
import time
from pathlib import Path
from typing import Dict, Any, Optional

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> Dict[str, Any]:
    if CONFIG_PATH.is_file():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "host": "127.0.0.1",
        "port": 8001,
        "auth_token": "jarvis-desktop-secret-token-change-in-production",
        "full_access_mode": True,
        "approved_apps": {},
        "allowed_directories": ["C:\\", "D:\\", "E:\\", "C:\\Users\\abdur"]
    }


class Authorizer:
    def __init__(self):
        self.config = load_config()
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}

    def reload(self):
        self.config = load_config()

    def verify_token(self, token: str) -> bool:
        expected = self.config.get("auth_token", "")
        if not expected:
            return True
        # Bearer prefix strip
        clean_token = token.replace("Bearer ", "").strip()
        return clean_token == expected

    def is_app_approved(self, app_id: str) -> bool:
        return app_id.lower().strip() in self.config.get("approved_apps", {})

    def get_app_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        return self.config.get("approved_apps", {}).get(app_id.lower().strip())

    def is_path_allowed(self, target_path: Path) -> bool:
        if self.config.get("full_access_mode", True):
            return True
        try:
            resolved = target_path.resolve()
            allowed = self.config.get("allowed_directories", [])
            for root_str in allowed:
                root = Path(root_str).resolve()
                if root == resolved or root in resolved.parents:
                    return True
            return False
        except Exception:
            return False

    def create_pending_approval(self, action: str, parameters: Dict[str, Any]) -> str:
        approval_id = str(uuid.uuid4())
        self.pending_approvals[approval_id] = {
            "action": action,
            "parameters": parameters,
            "timestamp": time.time(),
            "expires_at": time.time() + 300  # 5 minutes
        }
        return approval_id

    def resolve_approval(self, approval_id: str, approved: bool) -> Optional[Dict[str, Any]]:
        record = self.pending_approvals.pop(approval_id, None)
        if not record:
            return None
        if time.time() > record["expires_at"]:
            return None
        record["approved"] = approved
        return record


authorizer = Authorizer()
