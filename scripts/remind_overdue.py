#!/usr/bin/env python3
"""발표일이 지났는데 아직 열려있는 발표 Issue에 매일 알림을 남긴다.

일부러 하루 한 번으로 제한하지 않는다 — 블로그 정리하고 이슈 닫을 때까지
매일 찔러야 강제성이 생긴다는 게 운영 방침.
"""
import json
import subprocess
from datetime import date

from lib import BOT_NAME, parse_sections, post_discord

OVERDUE_LABEL = "발표일 지남"


def list_open_presentation_issues() -> list[dict]:
    out = subprocess.run(
        [
            "gh", "issue", "list",
            "--state", "open",
            "--json", "number,url,body,labels",
            "--limit", "200",
        ],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout)


def main() -> None:
    today = date.today().isoformat()
    overdue = []

    for issue in list_open_presentation_issues():
        presentation_date = parse_sections(issue["body"]).get("발표일", "").strip()
        if not presentation_date or presentation_date >= today:
            continue

        number = str(issue["number"])
        label_names = {l["name"] for l in issue["labels"]}
        if OVERDUE_LABEL not in label_names:
            subprocess.run(["gh", "issue", "edit", number, "--add-label", OVERDUE_LABEL], check=True)

        subprocess.run(
            ["gh", "issue", "comment", number,
             "--body", f"**{BOT_NAME}**\n\n발표일이 지났어요. 블로그 링크 남기고 이슈를 닫아주세요!"],
            check=True,
        )
        overdue.append(issue["url"])

    if overdue:
        lines = "\n".join(f"- {u}" for u in overdue)
        post_discord(f"**발표일 지난 미완료 발표 ({len(overdue)}건)**\n{lines}")
    print(f"overdue: {len(overdue)}")


if __name__ == "__main__":
    main()
