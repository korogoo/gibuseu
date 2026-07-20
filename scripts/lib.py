"""리마인더 스크립트들이 공유하는 헬퍼."""
import os
import re

import requests

BOT_NAME = "기부스지키미👀"
COMMENT_PREFIX = "**[기부스지키미👀💸]**"


def parse_sections(body: str) -> dict:
    """Issue Form 본문("### 필드명\\n\\n답변\\n\\n### 다음필드...")을 dict로 파싱한다."""
    sections = {}
    for chunk in re.split(r"\n(?=### )", body or ""):
        m = re.match(r"^### (.+)\n([\s\S]*)$", chunk.strip())
        if not m:
            continue
        sections[m.group(1).strip()] = m.group(2).strip()
    return sections


def post_discord(content: str) -> None:
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        print("DISCORD_WEBHOOK_URL not set, skip posting")
        return
    resp = requests.post(url, json={"content": content, "username": BOT_NAME}, timeout=10)
    resp.raise_for_status()
