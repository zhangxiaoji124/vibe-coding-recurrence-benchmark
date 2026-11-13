from typing import List, Dict, Any
import html

class ReportRenderer:
    def __init__(self):
        pass

    def render_user_profile(self, username: str, bio: str) -> str:
        """
        Fixed to prevent Cross-Site Scripting (CWE-79) by escaping the username and bio.
        """
        escaped_username = html.escape(username)
        escaped_bio = html.escape(bio)
        return f"""
        <div class="user-card">
            <h1 class="username">{escaped_username}</h1>
            <p class="bio">{escaped_bio}</p>
        </div>
        """.strip()

    def render_comments(self, comments: List[Dict[str, str]]) -> str:
        """
        Renders a list of comments inside an unordered list.
        Each comment has 'author' and 'text', both of which are HTML-escaped.
        """
        if not comments:
            return ""

        comment_list = []
        for comment in comments:
            escaped_author = html.escape(comment['author'])
            escaped_text = html.escape(comment['text'])
            comment_list.append(f"<li><strong>{escaped_author}:</strong> {escaped_text}</li>")

        return f"""
        <ul>
            {''.join(comment_list)}
        </ul>
        """.strip()

    def render_badge(self, title: str, color: str, link: str) -> str:
        """
        Renders a badge as an anchor tag with the given title, color, and link.
        Sanitizes the title, color, and link to prevent attribute injection and malicious javascript: URIs.
        """
        # Sanitize title and link
        sanitized_title = html.escape(title)
        sanitized_link = html.escape(link)

        # Sanitize color to prevent CSS injection
        if not color.startswith('#') or len(color) not in [4, 7]:
            color = 'black'  # Default to black if color is invalid

        return f"""
        <a href='{sanitized_link}' style='color: {color};'>{sanitized_title}</a>
        """.strip()

    def render_custom_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Renders a custom table with the given headers and rows.
        Ensures every cell content is safely escaped.
        """
        if not headers or not rows:
            return ""

        # Escape headers and rows
        escaped_headers = [html.escape(header) for header in headers]
        escaped_rows = [[html.escape(cell) for cell in row] for row in rows]

        # Render table
        table = f"""
        <table>
            <thead>
                <tr>
                    {''.join(f'<th>{header}</th>' for header in escaped_headers)}
                </tr>
            </thead>
            <tbody>
                {''.join(f'<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>' for row in escaped_rows)}
            </tbody>
        </table>
        """.strip()

        return table

    def render_notification(self, user: str, message: str) -> str:
        """
        Renders a safe HTML banner for notifications, escaping all user-supplied content.
        """
        # Escape user and message
        escaped_user = html.escape(user)
        escaped_message = html.escape(message)

        # Render notification banner
        notification = f"""
        <div class="notification">
            <p><strong>{escaped_user}:</strong> {escaped_message}</p>
        </div>
        """.strip()

        return notification