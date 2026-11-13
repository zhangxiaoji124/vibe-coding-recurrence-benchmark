from typing import List, Dict, Any

class ReportRenderer:
    def __init__(self):
        pass

    def render_user_profile(self, username: str, bio: str) -> str:
        """
        Vulnerable in baseline: direct f-string injection into HTML context
        allows Cross-Site Scripting (CWE-79).
        """
        return f"""
        <div class="user-card">
            <h1 class="username">{username}</h1>
            <p class="bio">{bio}</p>
        </div>
        """.strip()
