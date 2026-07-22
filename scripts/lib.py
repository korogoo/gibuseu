"""리마인더 스크립트들이 공유하는 헬퍼."""
import json
import os
import re
import subprocess
from pathlib import Path

import requests
import yaml

BOT_NAME = "기부스지키미👀"
COMMENT_PREFIX = "**[기부스지키미👀💸]**"
CATEGORY_LABELS = {"CS", "데이터베이스", "인프라/DevOps", "아키텍처", "보안", "테스트/QA", "AI"}


def is_blank(value: str) -> bool:
    return not value or value == "_No response_"


def date_part(value: str) -> str:
    """'발표일' 필드값("YYYY-MM-DD 23:00" 또는 "YYYY-MM-DD")에서 날짜 부분만 뗀다."""
    return (value or "").strip()[:10]


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


def latest_round_date(root: Path) -> str | None:
    data = yaml.safe_load((root / "teams" / "history.yaml").read_text(encoding="utf-8")) or {}
    rounds = data.get("rounds") or []
    return rounds[-1]["date"] if rounds else None


def presenters_for_round(round_date: str) -> set[str]:
    """발표일이 round_date와 일치하는 이슈들의 발표자 집합을 구한다."""
    out = subprocess.run(
        ["gh", "issue", "list", "--state", "all", "--json", "body", "--limit", "200"],
        check=True, capture_output=True, text=True,
    )
    issues = json.loads(out.stdout)
    result = set()
    for issue in issues:
        sections = parse_sections(issue["body"])
        if date_part(sections.get("발표일", "")) != round_date:
            continue
        presenter = sections.get("발표자", "").strip()
        if presenter:
            result.add(presenter)
    return result


def missing_members(members: list[str], round_date: str) -> list[str]:
    """round_date에 발표하기로 등록된 이슈가 없는 스터디원을 계산한다."""
    registered = presenters_for_round(round_date)
    return [m for m in members if m not in registered]
