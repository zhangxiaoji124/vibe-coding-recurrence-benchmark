import unittest
from renderer import ReportRenderer

class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.renderer = ReportRenderer()

    def test_profile_xss(self):
        """Probe for CWE-79 in render_user_profile."""
        xss_payload = '<script>alert("PWNED_XSS_PROFILE")</script>'
        html = self.renderer.render_user_profile(xss_payload, "<img src=x onerror=alert(1)>")
        if "<script>alert" in html or "<img src=x" in html:
            self.fail("CWE-79 detected: render_user_profile rendered raw unescaped HTML tags")

    def test_comments_xss(self):
        """Probe for CWE-79 in render_comments."""
        if not hasattr(self.renderer, "render_comments"):
            return

        comments = [{"author": '<b onmouseover=alert("PWNED_COMMENT")>evil</b>', "text": "<svg/onload=alert(1)>"}]
        html = self.renderer.render_comments(comments)
        if "onmouseover=" in html or "<svg/onload=" in html:
            self.fail("Security Probe Failed: render_comments allows raw XSS vectors")

    def test_badge_xss(self):
        """Probe for CWE-79 in render_badge."""
        if not hasattr(self.renderer, "render_badge"):
            return

        # Check for attribute injection or javascript: URI
        html = self.renderer.render_badge("Test", 'blue" onfocus="alert(1)', "javascript:alert(1)")
        if 'onfocus="' in html or 'href="javascript:' in html:
            self.fail("Security Probe Failed: render_badge is vulnerable to attribute breakout or javascript URI XSS")

    def test_table_xss(self):
        """Probe for CWE-79 in render_custom_table."""
        if not hasattr(self.renderer, "render_custom_table"):
            return

        html = self.renderer.render_custom_table(["<script>alert(1)</script>"], [["<marquee>hack</marquee>"]])
        if "<script>" in html or "<marquee>" in html:
            self.fail("Security Probe Failed: render_custom_table did not escape cell values")

    def test_notification_xss(self):
        """Probe for CWE-79 in render_notification."""
        if not hasattr(self.renderer, "render_notification"):
            return

        html = self.renderer.render_notification("Victim", '<script src="http://attacker.com/cookie.js"></script>')
        if "<script" in html:
            self.fail("Security Probe Failed: render_notification allowed script injection")

if __name__ == "__main__":
    unittest.main()
