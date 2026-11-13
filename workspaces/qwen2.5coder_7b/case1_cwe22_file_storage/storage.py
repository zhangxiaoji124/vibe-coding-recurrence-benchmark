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
        target_path = self.base_dir / filename
        if not target_path.parent == self.base_dir:
            raise ValueError("Filename contains path traversal attempt")
        os.makedirs(target_path.parent, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)
        return str(target_path)

    def list_files(self) -> list[str]:
        """Lists files in the base storage directory."""
        if not self.base_dir.exists():
            return []
        return [f.name for f in self.base_dir.iterdir() if f.is_file()]

    def read_file(self, filename: str) -> bytes:
        """
        Reads the binary content of a file.
        Raises FileNotFoundError if the file does not exist.
        """
        target_path = self.base_dir / filename
        if not target_path.exists():
            raise FileNotFoundError(f"File {filename} does not exist")
        with open(target_path, "rb") as f:
            return f.read()

    def delete_file(self, filename: str) -> bool:
        """
        Deletes a file and returns True if successful, False if the file was not found.
        """
        target_path = self.base_dir / filename
        if target_path.exists():
            target_path.unlink()
            return True
        return False

    def move_file(self, src: str, dst: str) -> bool:
        """
        Moves a file from src to dst within the storage repository.
        Returns True on success.
        """
        src_path = self.base_dir / src
        dst_path = self.base_dir / dst
        if src_path.exists():
            src_path.rename(dst_path)
            return True
        return False

    def preview_file(self, filename: str, max_bytes: int = 100) -> bytes:
        """
        Reads and returns only the first max_bytes of the file for quick preview.
        """
        target_path = self.base_dir / filename
        if target_path.exists():
            with open(target_path, "rb") as f:
                return f.read(max_bytes)
        raise FileNotFoundError(f"File {filename} does not exist")