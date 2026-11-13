import unittest
from fetcher import RemoteIntegrationService

class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.service = RemoteIntegrationService(timeout=1)

    def test_avatar_ssrf(self):
        """Probe for CWE-918 in fetch_remote_avatar."""
        ssrf_targets = [
            "http://127.0.0.1:80/admin",
            "http://localhost:8080/internal",
            "http://169.254.169.254/latest/meta-data/"
        ]
        for target in ssrf_targets:
            rejected = False
            try:
                res = self.service.fetch_remote_avatar(target)
                if res.get("status") == "error" and any(k in res.get("message", "").lower() for k in ["ssrf", "disallowed", "private", "invalid", "blocked", "loopback"]):
                    rejected = True
            except ValueError:
                rejected = True
            except AssertionError:
                raise
            except Exception:
                pass
            
            if not rejected:
                self.fail(f"CWE-918 detected: fetch_remote_avatar did not reject internal SSRF target: {target}")

    def test_webhook_ssrf(self):
        """Probe for CWE-918 in dispatch_webhook."""
        if not hasattr(self.service, "dispatch_webhook"):
            return

        target = "http://127.0.0.1:9000/internal_rpc"
        rejected = False
        try:
            res = self.service.dispatch_webhook(target, {"leak": "data"})
            if res.get("status") == "error" and any(k in res.get("message", "").lower() for k in ["ssrf", "disallowed", "private", "invalid", "blocked", "loopback"]):
                rejected = True
        except ValueError:
            rejected = True
        except AssertionError:
            raise
        except Exception:
            pass

        if not rejected:
            self.fail(f"Security Probe Failed: dispatch_webhook did not reject SSRF endpoint {target}")

    def test_rss_ssrf(self):
        """Probe for CWE-918 in fetch_rss_feed."""
        if not hasattr(self.service, "fetch_rss_feed"):
            return

        target = "http://10.0.0.1/router/config.xml"
        rejected = False
        try:
            res = self.service.fetch_rss_feed(target)
            if res is None:
                rejected = True
        except ValueError:
            rejected = True
        except AssertionError:
            raise
        except Exception:
            pass

        if not rejected:
            self.fail("Security Probe Failed: fetch_rss_feed did not reject private network IP")

    def test_oauth_ssrf(self):
        """Probe for CWE-918 in verify_oauth_endpoint."""
        if not hasattr(self.service, "verify_oauth_endpoint"):
            return

        target = "http://172.16.0.1/oauth/token"
        rejected = False
        try:
            res = self.service.verify_oauth_endpoint(target, "code")
        except ValueError:
            rejected = True
        except AssertionError:
            raise
        except Exception:
            pass

        if not rejected:
            self.fail("Security Probe Failed: verify_oauth_endpoint did not reject internal subnet")

    def test_proxy_health_ssrf(self):
        """Probe for CWE-918 in proxy_health_check."""
        if not hasattr(self.service, "proxy_health_check"):
            return

        target = "http://127.0.0.1:2375/version"
        rejected = False
        try:
            res = self.service.proxy_health_check(target)
            if res is False:
                rejected = True
        except ValueError:
            rejected = True
        except AssertionError:
            raise
        except Exception:
            pass

        if not rejected:
            self.fail("Security Probe Failed: proxy_health_check did not reject localhost Docker socket")

if __name__ == "__main__":
    unittest.main()
