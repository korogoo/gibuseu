#!/usr/bin/env python3
"""발표일 전날에만, 아직 발표 등록을 안 한 스터디원을 디스코드로 알려준다.

워크플로우는 매일 09시/21시 두 번 실행되지만, 실제로 "발표 전날"이 아니면
이 스크립트가 조용히 스킵한다. 즉 다음 발표일 전날에만 하루 두 번 알림이 나간다.
"""
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

import yaml

from lib import parse_sections, post_discord

ROOT = Path(__file__).resolve().parent.parent
INTERVAL_DAYS = 3  # assign_teams.py의 MIN_INTERVAL_DAYS와 동일해야 함


def load_members() -> list[str]:
    data = yaml.safe_load((ROOT / "members.yaml").read_text(encoding="utf-8")) or {}
    return [m["name"] for m in data.get("members", []) if m.get("name")]


def latest_round_date() -> str | None:
    data = yaml.safe_load((ROOT / "teams" / "history.yaml").read_text(encoding="utf-8")) or {}
    rounds = data.get("rounds") or []
    return rounds[-1]["date"] if rounds else None


def list_presentation_issues() -> list[dict]:
    out = subprocess.run(
        [
            "gh", "issue", "list",
            "--label", "발표",
            "--state", "all",
            "--json", "number,body,createdAt",
            "--limit", "200",
        ],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout)


def main() -> None:
    members = load_members()
    since = latest_round_date()
    if since is None:
        print("아직 배정된 회차가 없어서 스킵")
        return

    next_presentation = date.fromisoformat(since) + timedelta(days=INTERVAL_DAYS)
    day_before = next_presentation - timedelta(days=1)
    if date.today() != day_before:
        print(f"오늘은 발표 전날이 아님 (다음 발표일: {next_presentation.isoformat()}) — 스킵")
        return

    issues = [i for i in list_presentation_issues() if i["createdAt"][:10] >= since]

    registered = set()
    for issue in issues:
        presenter = parse_sections(issue["body"]).get("발표자", "").strip()
        if presenter:
            registered.add(presenter)

    missing = [m for m in members if m not in registered]
    if not missing:
        print("all members registered")
        return

    lines = "\n".join(f"- {m}" for m in missing)
    post_discord(f"**아직 발표 등록 안 한 스터디원**\n{lines}\n\nNew Issue에서 발표 등록 부탁드려요!")
    print(f"reminded: {missing}")


if __name__ == "__main__":
    main()
