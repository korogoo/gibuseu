#!/usr/bin/env python3
"""주제 제출 마감일(D-2 자정)에만, 아직 주제를 제출 안 한 스터디원을 디스코드로 알려준다.

D-1에 연관성 기준 팀 배정이 있으려면 D-2 자정까지 주제가 다 모여있어야 한다.
워크플로우는 매일 09시/21시 두 번 실행되지만, 실제로 "다음 발표일의 D-2"가
아니면 이 스크립트가 조용히 스킵한다. 즉 마감일에만 하루 두 번 알림이 나간다.
"""
from datetime import date, timedelta
from pathlib import Path

import yaml

from lib import latest_round_date, missing_members, post_discord

ROOT = Path(__file__).resolve().parent.parent
INTERVAL_DAYS = 4  # assign_teams.py의 INTERVAL_DAYS와 동일해야 함


def load_members() -> list[str]:
    data = yaml.safe_load((ROOT / "members.yaml").read_text(encoding="utf-8")) or {}
    return [m["name"] for m in data.get("members", []) if m.get("name")]


def main() -> None:
    members = load_members()
    since = latest_round_date(ROOT)
    if since is None:
        print("아직 배정된 회차가 없어서 스킵")
        return

    next_presentation = date.fromisoformat(since) + timedelta(days=INTERVAL_DAYS)
    deadline_day = next_presentation - timedelta(days=2)
    if date.today() != deadline_day:
        print(f"오늘은 주제 제출 마감일이 아님 (다음 발표일: {next_presentation.isoformat()}) — 스킵")
        return

    missing = missing_members(members, next_presentation.isoformat())
    if not missing:
        print("all members registered")
        return

    lines = "\n".join(f"- {m}" for m in missing)
    post_discord(f"💸 **오늘 자정까지 주제 제출 마감! 아직 안 낸 사람**\n{lines}\n\nNew Issue에서 발표 등록 부탁드려요!")
    print(f"reminded: {missing}")


if __name__ == "__main__":
    main()
