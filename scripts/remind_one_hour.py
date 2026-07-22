#!/usr/bin/env python3
"""발표 시작 1시간 전에 디스코드로 알린다.

발표 시간은 매 회차 23:00 고정이다. 발표일 필드는 "YYYY-MM-DD 23:00"으로 적는 게
표준이지만, 예전 형식("YYYY-MM-DD"만 있는)으로 남은 이슈도 있을 수 있어 23:00을
붙여서 재시도하는 폴백을 둔다. 중복 방지는 라벨이 아니라 state/reminded_one_hour.json
파일로 한다 (이슈에 내부용 라벨이 붙는 걸 원치 않는다는 운영 방침).
"""
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from lib import load_state_set, parse_sections, post_discord, save_state_set

KST = ZoneInfo("Asia/Seoul")
ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state" / "reminded_one_hour.json"


def list_open_presentation_issues() -> list[dict]:
    out = subprocess.run(
        ["gh", "issue", "list", "--state", "open",
         "--json", "number,url,title,body", "--limit", "200"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout)


def parse_target(sections: dict) -> datetime | None:
    date_str = sections.get("발표일", "").strip()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
    except ValueError:
        pass
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(hour=23, minute=0, tzinfo=KST)
    except ValueError:
        return None


def main() -> None:
    now = datetime.now(KST)
    already = load_state_set(STATE_FILE)
    newly_reminded = set()
    lines = []

    for issue in list_open_presentation_issues():
        number = issue["number"]
        if number in already:
            continue

        target = parse_target(parse_sections(issue["body"]))
        if target is None:
            continue

        remind_at = target - timedelta(hours=1)
        if remind_at <= now < target:
            newly_reminded.add(number)
            lines.append(f"- {issue['title']} ({target.strftime('%H:%M')} 시작) {issue['url']}")

    if newly_reminded:
        save_state_set(STATE_FILE, already | newly_reminded)
        post_discord("⏰ **1시간 뒤 발표 시작!** 미리 준비하세요 💸\n" + "\n".join(lines))
    print(f"reminded: {len(newly_reminded)}")


if __name__ == "__main__":
    main()
