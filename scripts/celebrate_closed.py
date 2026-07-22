#!/usr/bin/env python3
"""발표 이슈가 블로그 링크와 함께 닫히면 칭찬하고, 아직 다음 회차 주제를 제출 안 한
크루가 있으면 이어서 찔러준다.

GitHub Actions는 "닫기 버튼 자체를 막는" 진짜 차단 기능이 없다 (닫힘 이벤트는
닫힌 뒤에야 받는다). 그래서 블로그 링크 없이 닫히면 그 자리에서 바로 재오픈하고
안내 코멘트를 남겨 사실상 못 닫게 막는다.
"""
import json
import os
import subprocess
from datetime import date, timedelta
from pathlib import Path

import yaml

from lib import COMMENT_PREFIX, is_blank, latest_round_date, missing_members, parse_sections, post_discord

ROOT = Path(__file__).resolve().parent.parent
INTERVAL_DAYS = 4  # assign_teams.py의 INTERVAL_DAYS와 동일해야 함


def load_members() -> list[str]:
    data = yaml.safe_load((ROOT / "members.yaml").read_text(encoding="utf-8")) or {}
    return [m["name"] for m in data.get("members", []) if m.get("name")]


def gh(*args) -> None:
    subprocess.run(["gh", *args], check=True)


def gh_json(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def main() -> None:
    number = os.environ["ISSUE_NUMBER"]
    issue = gh_json("issue", "view", number, "--json", "body")
    sections = parse_sections(issue["body"])
    presenter = sections.get("발표자", "").strip()
    blog = sections.get("블로그 링크", "").strip()

    if not presenter:
        return

    if is_blank(blog):
        gh("issue", "reopen", number)
        gh(
            "issue", "comment", number, "--body",
            f"{COMMENT_PREFIX}\n\n블로그 링크 없이는 못 닫아요! 블로그 쓰고 링크 남긴 다음 다시 닫아주세요 💸",
        )
        return

    lines = [
        f"🎉 이 귀찮은 걸 해내다니... 멋지십니다... {presenter}",
        f"📝 블로그 구경가기 → {blog}",
    ]

    members = load_members()
    since = latest_round_date(ROOT)
    if since:
        next_presentation = date.fromisoformat(since) + timedelta(days=INTERVAL_DAYS)
        missing = missing_members(members, next_presentation.isoformat())
        if missing:
            lines.append(f"\n{', '.join(missing)}...당신들은 언제 쓰실 거에요..?")

    post_discord("\n".join(lines))


if __name__ == "__main__":
    main()
