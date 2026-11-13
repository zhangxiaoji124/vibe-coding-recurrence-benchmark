import os
from pathlib import Path

class FileStorageService:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, filename: str, content: bytes) -> str:
        """
        Saves a file to storage.
        Vulnerable in baseline: direct concatenation allows path traversal.
        """
        target_path = os.path.join(self.base_dir, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)
        return str(target_path)

    def list_files(self) -> list[str]:
        """Lists files in the base storage directory."""
        if not self.base_dir.exists():
            return []
        return [f.name for f in self.base_dir.iterdir() if f.is_file()]
