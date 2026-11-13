import os
from storage import FileStorageService

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "uploaded_data")
service = FileStorageService(STORAGE_DIR)

def upload_handler(filename: str, content: bytes) -> dict:
    try:
        saved_path = service.save_file(filename, content)
        return {"status": "success", "path": saved_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_handler() -> list[str]:
    return service.list_files()
