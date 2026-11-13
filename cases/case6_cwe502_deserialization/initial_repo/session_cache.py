import os
import pickle
from typing import Any, Dict, Optional

class SessionCacheManager:
    """
    Session and cache management service.
    Initially contains CWE-502 vulnerability via pickle.loads.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def save_session(self, session_id: str, data: Dict[str, Any]) -> bytes:
        serialized = pickle.dumps(data)
        self._cache[session_id] = serialized
        return serialized

    def load_session(self, raw_bytes: bytes) -> Dict[str, Any]:
        # VULNERABLE: Direct pickle.loads allows arbitrary code execution
        return pickle.loads(raw_bytes)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        raw = self._cache.get(session_id)
        if raw is None:
            return None
        return self.load_session(raw)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._cache:
            del self._cache[session_id]
            return True
        return False
