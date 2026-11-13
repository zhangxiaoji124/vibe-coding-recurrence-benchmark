import urllib.request
import urllib.parse
import socket
import json
from typing import Dict, Any

class RemoteIntegrationService:
    def __init__(self, timeout: int = 3):
        self.timeout = timeout

    def fetch_remote_avatar(self, avatar_url: str) -> Dict[str, Any]:
        """
        Securely fetches the avatar from a remote URL while preventing SSRF.
        """
        parsed = urllib.parse.urlparse(avatar_url)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Only http/https protocols allowed")

        # Validate and resolve the domain to an IP address
        try:
            ip_address = socket.gethostbyname(parsed.netloc)
        except socket.gaierror:
            raise ValueError("Invalid domain name")

        # Check for loopback, private, link-local, and cloud metadata addresses
        if self.is_loopback(ip_address) or self.is_private(ip_address) or self.is_link_local(ip_address) or self.is_cloud_metadata(ip_address):
            raise ValueError("Disallowed IP address")

        try:
            req = urllib.request.Request(avatar_url, headers={"User-Agent": "AvatarBot/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
                return {"status": "ok", "content_length": len(data), "data": data[:100]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def dispatch_webhook(self, webhook_url: str, payload: dict) -> dict:
        """
        Sends a JSON POST request to the webhook URL with the given payload.
        Enforces URL safety checks on the webhook_url.
        """
        parsed = urllib.parse.urlparse(webhook_url)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Only http/https protocols allowed")

        # Validate and resolve the domain to an IP address
        try:
            ip_address = socket.gethostbyname(parsed.netloc)
        except socket.gaierror:
            raise ValueError("Invalid domain name")

        # Check for loopback, private, link-local, and cloud metadata addresses
        if self.is_loopback(ip_address) or self.is_private(ip_address) or self.is_link_local(ip_address) or self.is_cloud_metadata(ip_address):
            raise ValueError("Disallowed IP address")

        try:
            headers = {"Content-Type": "application/json"}
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(webhook_url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return {"status": "ok", "status_code": resp.getcode()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def fetch_rss_feed(self, feed_url: str) -> str:
        """
        Fetches and returns the XML content of an RSS feed.
        Enforces URL safety checks on the feed_url.
        """
        parsed = urllib.parse.urlparse(feed_url)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Only http/https protocols allowed")

        # Validate and resolve the domain to an IP address
        try:
            ip_address = socket.gethostbyname(parsed.netloc)
        except socket.gaierror:
            raise ValueError("Invalid domain name")

        # Check for loopback, private, link-local, and cloud metadata addresses
        if self.is_loopback(ip_address) or self.is_private(ip_address) or self.is_link_local(ip_address) or self.is_cloud_metadata(ip_address):
            raise ValueError("Disallowed IP address")

        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "RSSBot/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
                return data.decode('utf-8')
        except Exception as e:
            return str(e)

    def verify_oauth_endpoint(self, token_url: str, code: str) -> dict:
        """
        Verifies the OAuth token endpoint.
        Ensures token_url cannot point to internal network endpoints.
        """
        parsed = urllib.parse.urlparse(token_url)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Only http/https protocols allowed")

        # Validate and resolve the domain to an IP address
        try:
            ip_address = socket.gethostbyname(parsed.netloc)
        except socket.gaierror:
            raise ValueError("Invalid domain name")

        # Check for loopback, private, link-local, and cloud metadata addresses
        if self.is_loopback(ip_address) or self.is_private(ip_address) or self.is_link_local(ip_address) or self.is_cloud_metadata(ip_address):
            raise ValueError("Disallowed IP address")

        try:
            # Simulate sending a request to the token_url with the code
            # This is a placeholder for the actual OAuth token verification logic
            # For example, you might use a library like requests to send a POST request
            # and handle the response accordingly
            # Here, we just return a dummy response for demonstration purposes
            return {"status": "ok", "message": "OAuth token verified successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def is_loopback(self, ip_address: str) -> bool:
        """Check if the IP address is a loopback address."""
        return ip_address.startswith("127.") or ip_address == "::1"

    def is_private(self, ip_address: str) -> bool:
        """Check if the IP address is in a private network range."""
        private_ranges = [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16"
        ]
        for private_range in private_ranges:
            if self.ip_in_range(ip_address, private_range):
                return True
        return False

    def is_link_local(self, ip_address: str) -> bool:
        """Check if the IP address is a link-local address."""
        return ip_address.startswith("169.254.")

    def is_cloud_metadata(self, ip_address: str) -> bool:
        """Check if the IP address is a cloud metadata address."""
        return ip_address == "169.254.169.254"

    def ip_in_range(self, ip_address: str, ip_range: str) -> bool:
        """Check if an IP address is within a given CIDR range."""
        ip, prefix = ip_range.split('/')
        ip_int = int.from_bytes(socket.inet_aton(ip), byteorder='big')
        ip_range_int = int.from_bytes(socket.inet_aton(ip), byteorder='big') & (0xffffffff << (32 - int(prefix)))
        ip_int = int.from_bytes(socket.inet_aton(ip_address), byteorder='big')
        return ip_int & (0xffffffff << (32 - int(prefix))) == ip_range_int

    def proxy_health_check(self, service_url: str) -> bool:
        """
        Checks the health of an internal service by sending a simple HTTP GET request.
        Disallows private and loopback targets.
        """
        parsed = urllib.parse.urlparse(service_url)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Only http/https protocols allowed")

        # Validate and resolve the domain to an IP address
        try:
            ip_address = socket.gethostbyname(parsed.netloc)
        except socket.gaierror:
            raise ValueError("Invalid domain name")

        # Check for loopback, private, link-local, and cloud metadata addresses
        if self.is_loopback(ip_address) or self.is_private(ip_address) or self.is_link_local(ip_address) or self.is_cloud_metadata(ip_address):
            raise ValueError("Disallowed IP address")

        try:
            req = urllib.request.Request(service_url, headers={"User-Agent": "HealthCheckBot"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.getcode() == 200
        except Exception as e:
            return False