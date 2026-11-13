import os
import re
import subprocess
import sys
from typing import Any, Dict
from urllib.parse import urlparse


class SystemOpsRunner:
    _HOST_PATTERN = re.compile(r"[A-Za-z0-9_.:-]+")
    _DOMAIN_PATTERN = re.compile(r"[A-Za-z0-9.-]+")
    _PROCESS_PATTERN = re.compile(r"[A-Za-z0-9_.-]+")

    _MAX_HOST_LENGTH = 253
    _MAX_DOMAIN_LENGTH = 253
    _MAX_PROCESS_LENGTH = 255
    _MAX_URL_LENGTH = 2048

    def __init__(self):
        self.is_windows = sys.platform == "win32"

    def _validate_host(self, host: str) -> None:
        if not isinstance(host, str):
            raise ValueError("Host must be a string")

        if not host or len(host) > self._MAX_HOST_LENGTH:
            raise ValueError("Invalid host")

        if host.startswith("-") or not self._HOST_PATTERN.fullmatch(host):
            raise ValueError("Invalid host")

    def _validate_domain(self, domain: str) -> None:
        if not isinstance(domain, str):
            raise ValueError("Domain must be a string")

        if not domain or len(domain) > self._MAX_DOMAIN_LENGTH:
            raise ValueError("Invalid domain")

        if domain.startswith("-") or domain.endswith("-"):
            raise ValueError("Invalid domain")

        if not self._DOMAIN_PATTERN.fullmatch(domain):
            raise ValueError("Invalid domain")

    def _validate_process_name(self, process_name: str) -> None:
        if not isinstance(process_name, str):
            raise ValueError("Process name must be a string")

        if not process_name or len(process_name) > self._MAX_PROCESS_LENGTH:
            raise ValueError("Invalid process name")

        if process_name.startswith("-"):
            raise ValueError("Invalid process name")

        if not self._PROCESS_PATTERN.fullmatch(process_name):
            raise ValueError("Invalid process name")

    def _validate_url(self, target_url: str) -> None:
        if not isinstance(target_url, str):
            raise ValueError("URL must be a string")

        if not target_url or len(target_url) > self._MAX_URL_LENGTH:
            raise ValueError("Invalid URL")

        # Reject argument-injection attempts (leading dash) and control chars
        # that could confuse downstream tooling. Using shell=False means no
        # shell metacharacter expansion occurs, but we still guard in depth.
        if target_url.startswith("-"):
            raise ValueError("Invalid URL")

        if any(ch in target_url for ch in ("\x00", "\n", "\r", "\t", " ")):
            raise ValueError("Invalid URL")

        try:
            parsed = urlparse(target_url)
        except Exception:
            raise ValueError("Invalid URL")

        if parsed.scheme not in ("http", "https"):
            raise ValueError("Invalid URL scheme")

        if not parsed.netloc:
            raise ValueError("Invalid URL")

    @staticmethod
    def _decode_output(output: Any) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="ignore")
        return str(output)

    def ping_host(self, host: str) -> Dict[str, Any]:
        """
        Ping a host without using shell=True. The host is validated against
        hostname/IP-friendly characters and cannot start with '-', preventing
        shell metacharacter injection and ping option injection.
        """
        try:
            self._validate_host(host)

            count_flag = "-n" if self.is_windows else "-c"
            command = ["ping", count_flag, "1", host]

            output = subprocess.check_output(
                command,
                shell=False,
                stderr=subprocess.STDOUT,
                timeout=5,
            )
            return {"status": "ok", "output": self._decode_output(output)}
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "output": self._decode_output(e.output)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_dns(self, domain: str) -> Dict[str, Any]:
        """
        Perform a DNS lookup using nslookup with an argument list and shell=False.
        The domain is validated to prevent shell metacharacter and option injection.
        """
        try:
            self._validate_domain(domain)

            command = ["nslookup", domain]
            output = subprocess.check_output(
                command,
                shell=False,
                stderr=subprocess.STDOUT,
                timeout=5,
            )
            return {"status": "ok", "output": self._decode_output(output)}
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "output": self._decode_output(e.output)}
        except ValueError as e:
            return {"status": "failed", "output": str(e)}
        except Exception as e:
            return {"status": "failed", "output": str(e)}

    def get_process_status(self, process_name: str) -> Dict[str, Any]:
        """
        Query process information using ps/tasklist via an argument list and
        shell=False. The process name is validated to prevent option injection
        and shell metacharacter abuse.
        """
        try:
            self._validate_process_name(process_name)

            if self.is_windows:
                command = ["tasklist", "/FI", f"IMAGENAME eq {process_name}"]
            else:
                command = ["ps", "-A", "-o", "pid,comm"]

            output = subprocess.check_output(
                command,
                shell=False,
                stderr=subprocess.STDOUT,
                timeout=5,
            )
            text = self._decode_output(output)

            # On POSIX, ps doesn't let us filter by name via an option safely,
            # so filter the results ourselves.
            if not self.is_windows:
                matches = [
                    line
                    for line in text.splitlines()
                    if process_name.lower() in line.lower()
                ]
                text = "\n".join(matches)

            running = bool(text.strip()) and (
                "no tasks" not in text.lower()
                if self.is_windows
                else bool(text.strip())
            )

            return {
                "status": "ok",
                "running": running,
                "output": text,
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "failed",
                "running": False,
                "output": self._decode_output(e.output),
            }
        except ValueError as e:
            return {"status": "failed", "running": False, "output": str(e)}
        except Exception as e:
            return {
                "status": "error",
                "running": False,
                "output": str(e),
            }

    def curl_benchmark(self, target_url: str) -> Dict[str, Any]:
        """
        Benchmark an HTTP(S) endpoint using curl with an argument list and
        shell=False. The URL is validated (scheme, structure, no control
        characters, no leading dash) to prevent option injection. Because
        shell=False is used, shell metacharacter expansion cannot occur.
        """
        try:
            self._validate_url(target_url)

            command = [
                "curl",
                "--silent",
                "--show-error",
                "--output", os.devnull,
                "--write-out",
                (
                    "http_code=%{http_code}\n"
                    "time_namelookup=%{time_namelookup}\n"
                    "time_connect=%{time_connect}\n"
                    "time_starttransfer=%{time_starttransfer}\n"
                    "time_total=%{time_total}\n"
                ),
                "--max-time", "10",
                target_url,
            ]

            output = subprocess.check_output(
                command,
                shell=False,
                stderr=subprocess.STDOUT,
                timeout=15,
            )
            return {"status": "ok", "output": self._decode_output(output)}
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "output": self._decode_output(e.output)}
        except ValueError as e:
            return {"status": "failed", "output": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}