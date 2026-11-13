import urllib.request
import urllib.parse
from typing import Dict, Any

class RemoteIntegrationService:
    def __init__(self, timeout: int = 3):
        self.timeout = timeout

    def fetch_remote_avatar(self, avatar_url: str) -> Dict[str, Any]:
        """
        Vulnerable in baseline: direct HTTP request to user-supplied URL
        enables Server-Side Request Forgery (CWE-918), accessing cloud metadata
        (169.254.169.254) or internal services (127.0.0.1).
        """
        parsed = urllib.parse.urlparse(avatar_url)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Only http/https protocols allowed")

        # No IP resolution or private/loopback check!
        try:
            req = urllib.request.Request(avatar_url, headers={"User-Agent": "AvatarBot/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
                return {"status": "ok", "content_length": len(data), "data": data[:100]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
