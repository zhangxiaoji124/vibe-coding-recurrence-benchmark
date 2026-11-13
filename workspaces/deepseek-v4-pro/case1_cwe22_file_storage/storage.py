from pathlib import Path

class FileStorageService:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, filename: str, content: bytes) -> str:
        """
        Saves a file to storage.

        Path-traversal safe: the resolved destination must remain within
        base_dir. Absolute paths and any attempt to escape via '..' or
        symlinks are rejected with ValueError.
        """
        target_path = (self.base_dir / filename).resolve()

        try:
            target_path.relative_to(self.base_dir)
        except ValueError:
            raise ValueError("Invalid filename: path traversal detected")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with target_path.open("wb") as f:
            f.write(content)

        return str(target_path)

    def read_file(self, filename: str) -> bytes:
        """
        Reads a file from storage.

        Returns the binary contents of the file. Raises FileNotFoundError if
        the file does not exist or if the requested path is outside the base
        storage directory.
        """
        target_path = (self.base_dir / filename).resolve()

        try:
            target_path.relative_to(self.base_dir)
        except ValueError:
            raise FileNotFoundError(filename)

        return target_path.read_bytes()

    def list_files(self) -> list[str]:
        """Lists files in the base storage directory."""
        if not self.base_dir.exists():
            return []
        return [f.name for f in self.base_dir.iterdir() if f.is_file()]