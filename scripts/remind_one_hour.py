#!/usr/bin/env python3
"""발표 시작 1시간 전에 디스코드로 알린다.

회차마다 발표 시간이 다를 수 있어서 각 Issue의 발표일+발표 시간을 조합해
목표 시각을 계산한다. 15분 간격으로 도는 워크플로우가 "목표 시각 - 1시간"을
넘긴 걸 발견하면 그때 한 번만 알리고 라벨로 중복 방지한다.
"""
import json
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from lib import parse_sections, post_discord

KST = ZoneInfo("Asia/Seoul")
REMINDED_LABEL = "1시간전알림"


def list_open_presentation_issues() -> list[dict]:
    out = subprocess.run(
        ["gh", "issue", "list", "--state", "open",
         "--json", "number,url,title,body,labels", "--limit", "200"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout)


def parse_target(sections: dict) -> datetime | None:
    date_str = sections.get("발표일", "").strip()
    time_str = sections.get("발표 시간", "").strip()
    try:
        naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    return naive.replace(tzinfo=KST)


def main() -> None:
    now = datetime.now(KST)
    reminded = []

    for issue in list_open_presentation_issues():
        label_names = {l["name"] for l in issue["labels"]}
        if REMINDED_LABEL in label_names:
            continue

        target = parse_target(parse_sections(issue["body"]))
        if target is None:
            continue

        remind_at = target - timedelta(hours=1)
        if remind_at <= now < target:
            number = str(issue["number"])
            subprocess.run(["gh", "issue", "edit", number, "--add-label", REMINDED_LABEL], check=True)
            reminded.append((issue["title"], target, issue["url"]))

    if reminded:
        lines = "\n".join(f"- {title} ({t.strftime('%H:%M')} 시작) {url}" for title, t, url in reminded)
        post_discord(f"⏰ **1시간 뒤 발표 시작!** 미리 준비하세요 💸\n{lines}")
    print(f"reminded: {len(reminded)}")


if __name__ == "__main__":
    main()
