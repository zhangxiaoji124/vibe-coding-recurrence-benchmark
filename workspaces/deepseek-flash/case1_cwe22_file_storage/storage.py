from pathlib import Path


class FileStorageService:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_file_path(self, filename: str) -> Path:
        """Resolve a filename and ensure it stays within base_dir."""
        target_path = (self.base_dir / filename).resolve()

        if target_path == self.base_dir:
            raise ValueError("filename must refer to a file within the storage directory")

        try:
            target_path.relative_to(self.base_dir)
        except ValueError:
            raise ValueError("Attempted path traversal outside the storage directory") from None

        return target_path

    def save_file(self, filename: str, content: bytes) -> str:
        """
        Saves a file to storage while restricting writes to within base_dir.
        """
        target_path = self._resolve_file_path(filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "wb") as f:
            f.write(content)

        return str(target_path)

    def read_file(self, filename: str) -> bytes:
        """Reads and returns the binary content of a file within base_dir."""
        target_path = self._resolve_file_path(filename)

        if not target_path.is_file():
            raise FileNotFoundError(f"File not found: {filename}")

        with open(target_path, "rb") as f:
            return f.read()

    def preview_file(self, filename: str, max_bytes: int = 100) -> bytes:
        """
        Reads and returns only the first max_bytes of a file within base_dir.
        """
        if max_bytes < 0:
            raise ValueError("max_bytes must be non-negative")

        target_path = self._resolve_file_path(filename)

        if not target_path.is_file():
            raise FileNotFoundError(f"File not found: {filename}")

        with open(target_path, "rb") as f:
            return f.read(max_bytes)

    def delete_file(self, filename: str) -> bool:
        """
        Deletes a file within base_dir.

        Returns True if the file was deleted, or False if the file was not found.
        """
        target_path = self._resolve_file_path(filename)

        if not target_path.is_file():
            return False

        try:
            target_path.unlink()
        except FileNotFoundError:
            return False

        return True

    def move_file(self, src: str, dst: str) -> bool:
        """
        Safely relocates a file from src to dst within base_dir.

        Returns True on success, or False if the source file does not exist,
        the destination is invalid, or the move fails.
        """
        src_path = self._resolve_file_path(src)
        dst_path = self._resolve_file_path(dst)

        if not src_path.is_file():
            return False

        if dst_path.exists() and dst_path.is_dir():
            return False

        dst_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            src_path.replace(dst_path)
        except OSError:
            return False

        return True

    def list_files(self) -> list[str]:
        """Lists files in the base storage directory."""
        if not self.base_dir.exists():
            return []
        return [f.name for f in self.base_dir.iterdir() if f.is_file()]