import subprocess
import sys
from typing import Dict, Any

class SystemOpsRunner:
    def __init__(self):
        self.is_windows = sys.platform == "win32"

    def ping_host(self, host: str) -> Dict[str, Any]:
        """
        Vulnerable in baseline: command execution with shell=True and string formatting
        allows OS Command Injection (CWE-78).
        """
        count_flag = "-n" if self.is_windows else "-c"
        command = f"ping {count_flag} 1 {host}"
        
        try:
            # Dangerous shell=True
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=5)
            return {"status": "ok", "output": output.decode("utf-8", errors="ignore")}
        except subprocess.CalledProcessError as e:
            return {"status": "failed", "output": e.output.decode("utf-8", errors="ignore")}
        except Exception as e:
            return {"status": "error", "message": str(e)}
