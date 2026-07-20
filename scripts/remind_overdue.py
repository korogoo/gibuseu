#!/usr/bin/env python3
"""발표일이 지났는데 아직 열려있는 발표 Issue에 한 번만 알림을 남긴다."""
import json
import subprocess
from datetime import date

from lib import parse_sections, post_discord

OVERDUE_LABEL = "발표일 지남"


def list_open_presentation_issues() -> list[dict]:
    out = subprocess.run(
        [
            "gh", "issue", "list",
            "--label", "발표",
            "--state", "open",
            "--json", "number,url,body,labels",
            "--limit", "200",
        ],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout)


def main() -> None:
    today = date.today().isoformat()
    newly_overdue = []

    for issue in list_open_presentation_issues():
        presentation_date = parse_sections(issue["body"]).get("발표일", "").strip()
        if not presentation_date or presentation_date >= today:
            continue

        label_names = {l["name"] for l in issue["labels"]}
        if OVERDUE_LABEL in label_names:
            continue  # 이미 알림 보냄

        number = str(issue["number"])
        subprocess.run(["gh", "issue", "edit", number, "--add-label", OVERDUE_LABEL], check=True)
        subprocess.run(
            ["gh", "issue", "comment", number,
             "--body", "발표일이 지났어요. 블로그 링크 남기고 이슈를 닫아주세요!"],
            check=True,
        )
        newly_overdue.append(issue["url"])

    if newly_overdue:
        lines = "\n".join(f"- {u}" for u in newly_overdue)
        post_discord(f"**발표일 지난 미완료 발표**\n{lines}")
    print(f"newly overdue: {len(newly_overdue)}")


if __name__ == "__main__":
    main()
