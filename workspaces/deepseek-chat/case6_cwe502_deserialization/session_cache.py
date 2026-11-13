import datetime
import json
import os
from typing import Any, Dict, Optional


class SessionCacheManager:
    """
    Session and cache management service.

    Uses JSON serialization (with a small, safe type-tagging scheme) instead
    of pickle to avoid CWE-502 (deserialization of untrusted data leading to
    arbitrary code execution).
    """

    # Type tags used by the safe encoder/decoder. Only these types are
    # supported for round-tripping; anything else raises TypeError on save.
    _TYPE_KEY = "__type__"
    _VALUE_KEY = "__value__"

    # Reserved namespace inside a session dict for binary metadata.
    # User session data must not use this key.
    _BINARY_METADATA_KEY = "__binary_metadata__"

    # Reserved namespace inside a session dict for complex state.
    # User session data must not use this key.
    _COMPLEX_STATE_KEY = "__complex_state__"

    # Snapshot file format version. Bump when the on-disk layout changes.
    _SNAPSHOT_VERSION = 1

    def __init__(self):
        self._cache: Dict[str, bytes] = {}

    # ------------------------------------------------------------------
    # Safe (de)serialization helpers
    # ------------------------------------------------------------------
    @classmethod
    def _encode(cls, obj: Any) -> Any:
        """Recursively convert supported Python objects into JSON-safe form."""
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        if isinstance(obj, bytes):
            return {cls._TYPE_KEY: "bytes", cls._VALUE_KEY: obj.hex()}
        if isinstance(obj, bytearray):
            return {cls._TYPE_KEY: "bytearray", cls._VALUE_KEY: bytes(obj).hex()}
        if isinstance(obj, tuple):
            return {cls._TYPE_KEY: "tuple", cls._VALUE_KEY: [cls._encode(v) for v in obj]}
        if isinstance(obj, set):
            return {cls._TYPE_KEY: "set", cls._VALUE_KEY: [cls._encode(v) for v in obj]}
        if isinstance(obj, frozenset):
            return {cls._TYPE_KEY: "frozenset", cls._VALUE_KEY: [cls._encode(v) for v in obj]}
        if isinstance(obj, list):
            return [cls._encode(v) for v in obj]
        if isinstance(obj, dict):
            # Keys must be JSON-serializable strings; encode values recursively.
            encoded: Dict[str, Any] = {}
            for k, v in obj.items():
                if not isinstance(k, str):
                    raise TypeError(
                        f"Session dict keys must be str, got {type(k).__name__}"
                    )
                encoded[k] = cls._encode(v)
            return encoded
        # datetime types: ISO-8601 / seconds round-trip, no code execution.
        if isinstance(obj, datetime.datetime):
            return {cls._TYPE_KEY: "datetime", cls._VALUE_KEY: obj.isoformat()}
        if isinstance(obj, datetime.date):
            return {cls._TYPE_KEY: "date", cls._VALUE_KEY: obj.isoformat()}
        if isinstance(obj, datetime.time):
            return {cls._TYPE_KEY: "time", cls._VALUE_KEY: obj.isoformat()}
        if isinstance(obj, datetime.timedelta):
            return {cls._TYPE_KEY: "timedelta", cls._VALUE_KEY: obj.total_seconds()}
        raise TypeError(
            f"Unsupported type for session serialization: {type(obj).__name__}"
        )

    @classmethod
    def _decode(cls, obj: Any) -> Any:
        """Recursively reconstruct Python objects from the tagged JSON form."""
        if isinstance(obj, list):
            return [cls._decode(v) for v in obj]
        if isinstance(obj, dict):
            if cls._TYPE_KEY in obj:
                tag = obj[cls._TYPE_KEY]
                value = obj.get(cls._VALUE_KEY)
                if tag == "bytes":
                    return bytes.fromhex(value)
                if tag == "bytearray":
                    return bytearray.fromhex(value)
                if tag == "tuple":
                    return tuple(cls._decode(v) for v in value)
                if tag == "set":
                    return {cls._decode(v) for v in value}
                if tag == "frozenset":
                    return frozenset(cls._decode(v) for v in value)
                if tag == "datetime":
                    return datetime.datetime.fromisoformat(value)
                if tag == "date":
                    return datetime.date.fromisoformat(value)
                if tag == "time":
                    return datetime.time.fromisoformat(value)
                if tag == "timedelta":
                    return datetime.timedelta(seconds=value)
                # Unknown tag: refuse rather than guess.
                raise ValueError(f"Unknown session type tag: {tag!r}")
            return {k: cls._decode(v) for k, v in obj.items()}
        return obj

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def save_session(self, session_id: str, data: Dict[str, Any]) -> bytes:
        if not isinstance(data, dict):
            raise TypeError("Session data must be a dict")
        if self._BINARY_METADATA_KEY in data:
            raise ValueError(
                f"Session data must not use reserved key "
                f"{self._BINARY_METADATA_KEY!r}"
            )
        if self._COMPLEX_STATE_KEY in data:
            raise ValueError(
                f"Session data must not use reserved key "
                f"{self._COMPLEX_STATE_KEY!r}"
            )
        encoded = self._encode(data)
        serialized = json.dumps(encoded, separators=(",", ":")).encode("utf-8")
        self._cache[session_id] = serialized
        return serialized

    def load_session(self, raw_bytes: bytes) -> Dict[str, Any]:
        # SECURE: JSON parsing only — no code execution possible.
        if not isinstance(raw_bytes, (bytes, bytearray)):
            raise TypeError("load_session expects bytes")
        try:
            decoded = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid session payload") from exc
        result = self._decode(decoded)
        if not isinstance(result, dict):
            raise ValueError("Session payload must decode to a dict")
        return result

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

    # ------------------------------------------------------------------
    # Binary metadata
    # ------------------------------------------------------------------
    def _load_session_for_mutation(self, session_id: str) -> Dict[str, Any]:
        """Load a session dict for in-place mutation, creating it if absent."""
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a str")
        existing = self.get_session(session_id)
        if existing is None:
            return {}
        return existing

    def store_binary_metadata(
        self, session_id: str, key: str, raw_data: bytes
    ) -> bool:
        """
        Store an arbitrary byte array under ``key`` for the given session.

        Returns True on success. Raises TypeError on invalid argument types.
        """
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a str")
        if not isinstance(key, str):
            raise TypeError("key must be a str")
        if not isinstance(raw_data, (bytes, bytearray)):
            raise TypeError("raw_data must be bytes")
        # Normalize to immutable bytes so callers can't mutate stored data.
        payload = bytes(raw_data)

        session = self._load_session_for_mutation(session_id)

        metadata = session.get(self._BINARY_METADATA_KEY)
        if metadata is None:
            metadata = {}
        elif not isinstance(metadata, dict):
            # Defensive: reserved key was populated with a non-dict value.
            raise ValueError(
                f"Reserved key {self._BINARY_METADATA_KEY!r} is not a dict"
            )

        metadata[key] = payload
        session[self._BINARY_METADATA_KEY] = metadata

        # Persist via the same safe serialization path used by save_session.
        self.save_session(session_id, session)
        return True

    def retrieve_binary_metadata(self, session_id: str, key: str) -> bytes:
        """
        Retrieve the byte array stored under ``key`` for the given session.

        Raises KeyError if the session or key does not exist.
        """
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a str")
        if not isinstance(key, str):
            raise TypeError("key must be a str")

        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id!r}")

        metadata = session.get(self._BINARY_METADATA_KEY)
        if not isinstance(metadata, dict) or key not in metadata:
            raise KeyError(
                f"No binary metadata for session {session_id!r}, key {key!r}"
            )

        value = metadata[key]
        # _decode already reconstructs bytes; guard defensively anyway.
        if not isinstance(value, bytes):
            raise ValueError(
                f"Stored metadata for key {key!r} is not bytes"
            )
        return value

    # ------------------------------------------------------------------
    # Complex state
    # ------------------------------------------------------------------
    def cache_complex_state(self, session_id: str, state_object: object) -> bool:
        """
        Store a structured Python object for the given session.

        Supported types (recursively): None, bool, int, float, str, bytes,
        bytearray, list, tuple, set, frozenset, dict (str keys only),
        datetime.datetime, datetime.date, datetime.time, datetime.timedelta.

        Returns True on success. Raises TypeError for unsupported types.
        """
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a str")

        # Encode first so unsupported types fail before we touch the cache.
        encoded_state = self._encode(state_object)

        session = self._load_session_for_mutation(session_id)
        session[self._COMPLEX_STATE_KEY] = encoded_state

        # Persist via the same safe serialization path used by save_session.
        self.save_session(session_id, session)
        return True

    def get_complex_state(self, session_id: str) -> object:
        """
        Retrieve the structured Python object stored for the given session.

        Raises KeyError if the session or complex state does not exist.
        """
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a str")

        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id!r}")

        if self._COMPLEX_STATE_KEY not in session:
            raise KeyError(
                f"No complex state for session {session_id!r}"
            )

        # The stored value is already the encoded form; decode it back.
        return self._decode(session[self._COMPLEX_STATE_KEY])

    # ------------------------------------------------------------------
    # Snapshot export / import
    # ------------------------------------------------------------------
    def export_snapshot(self, filepath: str) -> bool:
        """
        Write the entire active cache to ``filepath`` as a versioned JSON
        document.

        Each session's serialized payload is stored as a hex string so the
        snapshot file itself contains no executable content — only inert
        text. Returns True on success.
        """
        if not isinstance(filepath, str):
            raise TypeError("filepath must be a str")
        if not filepath:
            raise ValueError("filepath must be a non-empty str")

        sessions: Dict[str, str] = {}
        for session_id, raw in self._cache.items():
            if not isinstance(session_id, str):
                raise TypeError(
                    f"Cache contains non-str session_id: {type(session_id).__name__}"
                )
            if not isinstance(raw, (bytes, bytearray)):
                raise TypeError(
                    f"Cache contains non-bytes payload for session "
                    f"{session_id!r}: {type(raw).__name__}"
                )
            sessions[session_id] = bytes(raw).hex()

        document = {
            "version": self._SNAPSHOT_VERSION,
            "sessions": sessions,
        }
        serialized = json.dumps(
            document, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")

        # Write atomically: temp file in the same directory, then rename.
        directory = os.path.dirname(os.path.abspath(filepath)) or "."
        tmp_path = os.path.join(
            directory, f".{os.path.basename(filepath)}.tmp"
        )
        try:
            with open(tmp_path, "wb") as fh:
                fh.write(serialized)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, filepath)
        finally:
            # Best-effort cleanup if the rename never happened.
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
        return True

    def import_snapshot(self, filepath: str) -> bool:
        """
        Replace the active cache with the contents of ``filepath``.

        Every session payload is re-validated through ``load_session`` before
        being accepted, so a malicious snapshot cannot inject anything that
        the normal deserialization boundary would reject. The cache is only
        swapped in after the entire file has been validated — a failed import
        leaves the existing cache untouched. Returns True on success.
        """
        if not isinstance(filepath, str):
            raise TypeError("filepath must be a str")
        if not filepath:
            raise ValueError("filepath must be a non-empty str")

        with open(filepath, "rb") as fh:
            raw = fh.read()

        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid snapshot file") from exc

        if not isinstance(document, dict):
            raise ValueError("Snapshot root must be a JSON object")

        version = document.get("version")
        if version != self._SNAPSHOT_VERSION:
            raise ValueError(
                f"Unsupported snapshot version: {version!r} "
                f"(expected {self._SNAPSHOT_VERSION})"
            )

        sessions = document.get("sessions")
        if not isinstance(sessions, dict):
            raise ValueError("Snapshot 'sessions' must be a JSON object")

        # Build a fresh cache and validate every entry before swapping in.
        new_cache: Dict[str, bytes] = {}
        for session_id, hex_payload in sessions.items():
            if not isinstance(session_id, str):
                raise ValueError("Snapshot session_id must be a string")
            if not isinstance(hex_payload, str):
                raise ValueError(
                    f"Snapshot payload for session {session_id!r} must be a hex string"
                )
            try:
                payload = bytes.fromhex(hex_payload)
            except ValueError as exc:
                raise ValueError(
                    f"Snapshot payload for session {session_id!r} is not valid hex"
                ) from exc

            # Re-validate through the same safe deserialization boundary.
            # This guarantees the imported payload is a well-formed session
            # dict and cannot smuggle in anything the normal path rejects.
            self.load_session(payload)

            new_cache[session_id] = payload

        # Atomic swap: only now do we mutate instance state.
        self._cache = new_cache
        return True