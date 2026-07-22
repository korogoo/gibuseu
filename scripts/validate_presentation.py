#!/usr/bin/env python3
"""발표 등록 Issue의 형식을 검사하는 '기부스지키미' 봇.

- 발표자 이름이 members.yaml에 있는지
- 발표일이 "YYYY-MM-DD 23:00" 형식인지 (시간은 고정이지만 표기는 필수)
- 소분류가 '기타'인데 직접입력이 비어있지 않은지
- 학습 완료기준이 '-'로 시작하는 줄 2개 이상인지
- 블로그 링크가 URL 형식인지 (입력했다면)
문제가 있으면 코멘트를 남기고 '형식 확인 필요' 라벨을 붙인다. 문제가 없으면 그 라벨을 뗀다.

조 라벨(1조/2조/3조)은 여기서 붙이지 않는다 — 새 플로우에서는 주제 제출(D-2)이
끝난 뒤 D-1에 scripts/assign_teams.py가 연관성 기준으로 조를 배정하면서 붙인다.
등록 시점엔 아직 그 회차의 조가 정해지지 않았을 수 있어서다.

문제가 없는 새 이슈는 디스코드에 발표 주제를 공지한다 (state/announced.json으로
중복 방지). 이미 공지된 이슈가 수정(edited)되면 가벼운 "수정됨" 알림을 보낸다.
"""
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

from lib import CATEGORY_LABELS, COMMENT_PREFIX, is_blank, load_state_set, parse_sections, post_discord, save_state_set

ROOT = Path(__file__).resolve().parent.parent
NEEDS_FIX_LABEL = "형식 확인 필요"
ANNOUNCED_FILE = ROOT / "state" / "announced.json"


def gh(*args) -> None:
    subprocess.run(["gh", *args], check=True)


def gh_json(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def load_members() -> list[str]:
    data = yaml.safe_load((ROOT / "members.yaml").read_text(encoding="utf-8")) or {}
    return [m["name"] for m in data.get("members", []) if m.get("name")]


def main() -> None:
    number = os.environ["ISSUE_NUMBER"]
    action = os.environ.get("ISSUE_ACTION", "opened")
    issue = gh_json("issue", "view", number, "--json", "title,url,body,labels")
    sections = parse_sections(issue["body"])
    label_names = {l["name"] for l in issue["labels"]}
    errors = []

    presenter = sections.get("발표자", "").strip()
    members = load_members()
    if presenter and presenter not in members:
        errors.append(f"닉네임에 오타가 있나요? 확인해주세요. (입력값: {presenter})")

    presentation_date = sections.get("발표일", "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2} 23:00", presentation_date):
        errors.append(f"발표일은 'YYYY-MM-DD 23:00' 형식으로 적어주세요 (시간은 23:00 고정). (입력값: {presentation_date})")

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

    has_fix_label = NEEDS_FIX_LABEL in label_names
    if errors:
        body = f"{COMMENT_PREFIX}\n\n다음 항목을 확인해주세요.\n\n" + "\n".join(f"- {e}" for e in errors)
        gh("issue", "comment", number, "--body", body)
        if not has_fix_label:
            gh("issue", "edit", number, "--add-label", NEEDS_FIX_LABEL)
        return

    if has_fix_label:
        gh("issue", "edit", number, "--remove-label", NEEDS_FIX_LABEL)

    # set이 아니라 라벨 원본 순서로 훑는다 (set 순회는 해시 랜덤화로 라벨이 2개
    # 이상인 이슈에서 실행마다 다른 카테고리가 뽑힐 수 있어서 재현성이 없다)
    category = next((l["name"] for l in issue["labels"] if l["name"] in CATEGORY_LABELS), "?")
    field = f"{category} / {subcategory}" if subcategory else category
    announced = load_state_set(ANNOUNCED_FILE)
    issue_number = int(number)

    if issue_number not in announced:
        post_discord(
            f"📢 **새 발표 등록!** [{field}] {issue['title']}\n"
            f"발표자: {presenter} · {presentation_date}\n"
            f"{issue['url']}"
        )
        save_state_set(ANNOUNCED_FILE, announced | {issue_number})
    elif action == "edited":
        post_discord(
            f"✏️ **발표 정보 수정됨**: [{field}] {issue['title']} ({presenter})\n{issue['url']}"
        )


if __name__ == "__main__":
    main()
