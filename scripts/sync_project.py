#!/usr/bin/env python3
"""발표 Issue를 Projects 보드(#8)에 추가하고, 발표일을 Date 필드에 채운다.

item-add는 이미 추가된 이슈에 다시 호출해도 기존 항목을 반환하므로
opened/edited 양쪽에서 그냥 호출해도 안전하다.
"""
import json
import os
import subprocess

from lib import parse_sections

OWNER = "korogoo"
PROJECT_NUMBER = "8"
PROJECT_ID = "PVT_kwHOB4mJYs4Bd4Md"
DATE_FIELD_ID = "PVTF_lAHOB4mJYs4Bd4MdzhYWe5k"


def gh_json(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def main() -> None:
    number = os.environ["ISSUE_NUMBER"]
    issue = gh_json("issue", "view", number, "--json", "url,body")

    item = gh_json(
        "project", "item-add", PROJECT_NUMBER, "--owner", OWNER,
        "--url", issue["url"], "--format", "json",
    )
    item_id = item["id"]

    presentation_date = parse_sections(issue["body"]).get("발표일", "").strip()
    if presentation_date:
        subprocess.run(
            ["gh", "project", "item-edit",
             "--id", item_id,
             "--field-id", DATE_FIELD_ID,
             "--project-id", PROJECT_ID,
             "--date", presentation_date],
            check=True,
        )
        print(f"synced 발표일={presentation_date} for issue #{number}")
    else:
        print(f"no 발표일 found for issue #{number}, skipped date sync")


if __name__ == "__main__":
    main()
