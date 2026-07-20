"""리마인더 스크립트들이 공유하는 헬퍼."""
import json
import os
import re
from pathlib import Path

import requests

BOT_NAME = "기부스지키미👀"
COMMENT_PREFIX = "**[기부스지키미👀💸]**"
CATEGORY_LABELS = {"CS", "데이터베이스", "인프라/DevOps", "아키텍처", "보안", "테스트/QA", "AI"}


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


def load_state_set(path: Path) -> set[int]:
    """중복 알림 방지용 상태 파일(이슈 번호 목록)을 읽는다. 라벨 대신 이걸 쓴다 —
    이슈에 내부용 라벨이 보이는 걸 원치 않는다는 운영 방침."""
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def save_state_set(path: Path, values: set[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(values)), encoding="utf-8")
