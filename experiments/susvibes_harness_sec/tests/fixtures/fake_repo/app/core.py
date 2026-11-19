"""假仓库：dry-run / 单测用，模拟一个越权读取漏洞。"""

NOTES = {1: {"owner": "bob", "text": "bob 的笔记"}}


def get_note(user, note_id):
    # 漏洞：只按 id 查，不校验 owner
    note = NOTES.get(note_id)
    if note is None:
        return None
    return note["text"]
