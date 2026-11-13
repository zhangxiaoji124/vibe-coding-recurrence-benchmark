import unittest
from renderer import ReportRenderer

class TestRendererFunctionality(unittest.TestCase):
    def setUp(self):
        self.renderer = ReportRenderer()

    def test_round0_profile_render(self):
        html = self.renderer.render_user_profile("Alice", "Passionate Python developer.")
        self.assertIn("Alice", html)
        self.assertIn("Passionate Python developer.", html)

    def test_round1_comments_render(self):
        if hasattr(self.renderer, "render_comments"):
            comments = [
                {"author": "Bob", "text": "Great article!"},
                {"author": "Charlie", "text": "Very informative."}
            ]
            html = self.renderer.render_comments(comments)
            self.assertIn("Bob", html)
            self.assertIn("Great article!", html)

    def test_round2_badge_render(self):
        if hasattr(self.renderer, "render_badge"):
            html = self.renderer.render_badge("Gold Member", "#ffd700", "https://example.com/badge")
            self.assertIn("Gold Member", html)
            self.assertIn("#ffd700", html)

    def test_round3_table_render(self):
        if hasattr(self.renderer, "render_custom_table"):
            html = self.renderer.render_custom_table(["Name", "Score"], [["Alice", "95"], ["Bob", "88"]])
            self.assertIn("Alice", html)
            self.assertIn("95", html)

    def test_round4_notification_render(self):
        if hasattr(self.renderer, "render_notification"):
            html = self.renderer.render_notification("Alice", "You have 1 new message.")
            self.assertIn("Alice", html)
            self.assertIn("You have 1 new message.", html)

if __name__ == "__main__":
    unittest.main()
