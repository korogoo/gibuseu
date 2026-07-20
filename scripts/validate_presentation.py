#!/usr/bin/env python3
"""발표 등록 Issue를 검사하고 조를 자동 라벨링하는 '기부스지킴이' 봇.

- 발표자 이름이 members.yaml에 있는지
- 발표일이 YYYY-MM-DD 형식인지
- 소분류가 '기타'인데 직접입력이 비어있지 않은지
- 학습 완료기준이 '-'로 시작하는 줄 2개 이상인지
- 블로그 링크가 URL 형식인지 (입력했다면)
문제가 있으면 코멘트를 남기고 '형식 확인 필요' 라벨을 붙인다.
문제가 없으면 그 라벨을 떼고, teams/history.yaml의 최신 회차에서 발표자를 찾아
해당 조 라벨(1조/2조/3조)을 자동으로 붙인다.
"""
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

from lib import COMMENT_PREFIX, parse_sections

ROOT = Path(__file__).resolve().parent.parent
NEEDS_FIX_LABEL = "형식 확인 필요"


def gh(*args) -> None:
    subprocess.run(["gh", *args], check=True)


def gh_json(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def load_members() -> list[str]:
    data = yaml.safe_load((ROOT / "members.yaml").read_text(encoding="utf-8")) or {}
    return [m["name"] for m in data.get("members", []) if m.get("name")]


def latest_round_teams() -> list[list[str]] | None:
    data = yaml.safe_load((ROOT / "teams" / "history.yaml").read_text(encoding="utf-8")) or {}
    rounds = data.get("rounds") or []
    return rounds[-1]["teams"] if rounds else None


def find_team_label(presenter: str, teams: list[list[str]]) -> str | None:
    for i, team in enumerate(teams, start=1):
        if presenter in team:
            return f"{i}조"
    return None


def is_blank(value: str) -> bool:
    return not value or value == "_No response_"


def main() -> None:
    number = os.environ["ISSUE_NUMBER"]
    issue = gh_json("issue", "view", number, "--json", "body,labels")
    sections = parse_sections(issue["body"])
    label_names = {l["name"] for l in issue["labels"]}
    errors = []

    presenter = sections.get("발표자", "").strip()
    members = load_members()
    if presenter and presenter not in members:
        errors.append(f"닉네임에 오타가 있나요? 확인해주세요. (입력값: {presenter})")

    presentation_date = sections.get("발표일", "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", presentation_date):
        errors.append(f"발표 형식은 YYYY-MM-DD 로 작성해주세요. (입력값: {presentation_date})")

    subcategory = sections.get("소분류", "").strip()
    subcategory_other = sections.get("소분류 - 직접 입력", "").strip()
    if subcategory == "기타" and is_blank(subcategory_other):
        errors.append("소분류를 '기타'로 선택했다면 직접입력을 작성해주세요.")

    criteria = sections.get("학습 완료기준", "")
    bullet_lines = [l for l in (line.strip() for line in criteria.split("\n")) if l.startswith("-")]
    if len(bullet_lines) < 2:
        errors.append("학습 완료 기준은 '-'를 이용해 2개 이상 작성해주세요.")

    blog = sections.get("블로그 링크", "").strip()
    if not is_blank(blog) and not re.match(r"^https?://\S+$", blog):
        errors.append(f"블로그 링크는 URL 형식으로 작성해주세요. (입력값: {blog})")

    if presenter in members:
        teams = latest_round_teams()
        team_label = find_team_label(presenter, teams) if teams else None
        if team_label:
            if team_label not in label_names:
                gh("issue", "edit", number, "--add-label", team_label)
        else:
            errors.append("이번 회차 조 배정에서 발표자를 찾지 못했어요. 이름을 다시 확인해주세요.")

    has_fix_label = NEEDS_FIX_LABEL in label_names
    if errors:
        body = f"{COMMENT_PREFIX}\n\n다음 항목을 확인해주세요.\n\n" + "\n".join(f"- {e}" for e in errors)
        gh("issue", "comment", number, "--body", body)
        if not has_fix_label:
            gh("issue", "edit", number, "--add-label", NEEDS_FIX_LABEL)
    elif has_fix_label:
        gh("issue", "edit", number, "--remove-label", NEEDS_FIX_LABEL)


if __name__ == "__main__":
    main()
