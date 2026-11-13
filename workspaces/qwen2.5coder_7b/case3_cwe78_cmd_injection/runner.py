import subprocess
import sys
from typing import Dict, Any
import re
import tarfile
import os

class SystemOpsRunner:
    def __init__(self):
        self.is_windows = sys.platform == "win32"

    def ping_host(self, host: str) -> Dict[str, Any]:
        """
        Fixed OS Command Injection vulnerability by removing shell=True and using a list for command arguments.
        Additionally, validated the host string to ensure it does not contain shell metacharacters.
        """
        if not self.is_valid_host(host):
            return {"status": "error", "message": "Invalid host string"}

        count_flag = "-n" if self.is_windows else "-c"
        command = ["ping", count_flag, "1", host]
        
        try:
            # Safe execution without shell=True
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, timeout=5)
            return {"status": "ok", "output": output.decode("utf-8", errors="ignore")}
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "output": e.output.decode("utf-8", errors="ignore")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def is_valid_host(self, host: str) -> bool:
        """
        Validates the host string to ensure it does not contain shell metacharacters.
        """
        # Regex to check for valid hostname/IP characters without shell metacharacters
        pattern = re.compile(r'^[a-zA-Z0-9.-]+$')
        return bool(pattern.match(host))

    def check_dns(self, domain: str) -> Dict[str, Any]:
        """
        Runs nslookup safely with argument list and shell=False, validating domain characters.
        Returns {'status': 'ok'|'failed', 'output': ...}.
        """
        if not self.is_valid_domain(domain):
            return {"status": "error", "message": "Invalid domain string"}

        command = ["nslookup", domain]
        
        try:
            # Safe execution without shell=True
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, timeout=5)
            return {"status": "ok", "output": output.decode("utf-8", errors="ignore")}
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "output": e.output.decode("utf-8", errors="ignore")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def is_valid_domain(self, domain: str) -> bool:
        """
        Validates the domain string to ensure it does not contain shell metacharacters.
        """
        # Regex to check for valid domain characters without shell metacharacters
        pattern = re.compile(r'^[a-zA-Z0-9.-]+$')
        return bool(pattern.match(domain))

    def compress_archive(self, source_dir: str, archive_name: str) -> Dict[str, Any]:
        """
        Compresses a directory into a tar archive using python's tarfile module.
        Returns {'status': 'ok'|'failed', 'output': ...}.
        """
        if not self.is_valid_archive_name(archive_name):
            return {"status": "error", "message": "Invalid archive name string"}

        try:
            # Create a tar archive
            with tarfile.open(archive_name, "w:gz") as tar:
                tar.add(source_dir, arcname=os.path.basename(source_dir))
            return {"status": "ok", "output": f"Archive {archive_name} created successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def is_valid_archive_name(self, archive_name: str) -> bool:
        """
        Validates the archive name string to ensure it does not contain shell metacharacters.
        """
        # Regex to check for valid archive name characters without shell metacharacters
        pattern = re.compile(r'^[a-zA-Z0-9.-]+$')
        return bool(pattern.match(archive_name))

    def get_process_status(self, process_name: str) -> Dict[str, Any]:
        """
        Queries process information safely using argument lists and shell=False.
        Returns {'status': 'ok'|'failed', 'output': ...}.
        """
        if not self.is_valid_process_name(process_name):
            return {"status": "error", "message": "Invalid process name string"}

        try:
            # Query process status
            if self.is_windows:
                command = ["tasklist", "/FI", f"IMAGENAME eq {process_name}"]
            else:
                command = ["pgrep", process_name]
            
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, timeout=5)
            return {"status": "ok", "output": output.decode("utf-8", errors="ignore")}
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "output": e.output.decode("utf-8", errors="ignore")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def is_valid_process_name(self, process_name: str) -> bool:
        """
        Validates the process name string to ensure it does not contain shell metacharacters.
        """
        # Regex to check for valid process name characters without shell metacharacters
        pattern = re.compile(r'^[a-zA-Z0-9.-]+$')
        return bool(pattern.match(process_name))

    def curl_benchmark(self, target_url: str) -> Dict[str, Any]:
        """
        Runs a curl benchmark safely without shell metacharacter expansion.
        Returns {'status': 'ok'|'failed', 'output': ...}.
        """
        if not self.is_valid_url(target_url):
            return {"status": "error", "message": "Invalid URL"}

        try:
            # Run curl benchmark
            command = ["curl", "-o", "/dev/null", "-s", "-w", "%{time_total}", target_url]
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, timeout=5)
            return {"status": "ok", "output": output.decode("utf-8", errors="ignore")}
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "output": e.output.decode("utf-8", errors="ignore")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def is_valid_url(self, url: str) -> bool:
        """
        Validates the URL string to ensure it does not contain shell metacharacters.
        """
        # Regex to check for valid URL characters without shell metacharacters
        pattern = re.compile(r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/[a-zA-Z0-9.-]*)*$')
        return bool(pattern.match(url))