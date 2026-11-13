import html
from typing import List, Dict, Any


class ReportRenderer:
    def __init__(self):
        pass

    def render_user_profile(self, username: str, bio: str) -> str:
        """
        Render a user profile with all untrusted values escaped for HTML context.
        """
        safe_username = html.escape(username)
        safe_bio = html.escape(bio)

        return f"""
        <div class="user-card">
            <h1 class="username">{safe_username}</h1>
            <p class="bio">{safe_bio}</p>
        </div>
        """.strip()

    def render_comments(self, comments: List[Dict[str, str]]) -> str:
        """
        Render comments as an unordered list, escaping all untrusted values.
        """
        items = "".join(
            f"<li>{html.escape(comment['author'])}: {html.escape(comment['text'])}</li>"
            for comment in comments
        )
        return f"<ul>{items}</ul>"

    def render_custom_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Render a dynamic table, escaping all header and cell content.
        """
        header_html = "".join(
            f"<th>{html.escape(header)}</th>" for header in headers
        )
        rows_html = "".join(
            "<tr>"
            + "".join(f"<td>{html.escape(cell)}</td>" for cell in row)
            + "</tr>"
            for row in rows
        )
        return f"<table><tr>{header_html}</tr>{rows_html}</table>"

    def render_notification(self, user: str, message: str) -> str:
        """
        Render a notification banner, escaping all user-supplied content.
        """
        safe_user = html.escape(user)
        safe_message = html.escape(message)

        return f'<div class="notification">{safe_user}: {safe_message}</div>'