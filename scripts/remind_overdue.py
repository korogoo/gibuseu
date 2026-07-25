#!/usr/bin/env python3
"""발표일이 지났는데 아직 열려있는 발표 Issue에 매일 알림을 남긴다.

일부러 하루 한 번으로 제한하지 않는다 — 블로그 정리하고 이슈 닫을 때까지
매일 찔러야 강제성이 생긴다는 게 운영 방침.
"""
import json
import subprocess
from collections import Counter
from datetime import date

from lib import COMMENT_PREFIX, parse_sections, post_discord

OVERDUE_LABEL = "발표일 지남"
NAG_MESSAGE = "취업은 조상님이 시켜주나요? 미루지 말고 블로그 작성하세요👴🏻💸"


def nag_line(name: str, count: int) -> str:
    if count >= 3:
        return f"{name} - 벌써 {count}개나 밀림..도대체 언제까지 미룰거임?"
    if count == 2:
        return f"{name} - 2개 밀림..빨리빨리 쓰자.."
    return f"{name} - 1개 밀림. 하나가 2개 되고 2개가 3개 된다.."


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
    overdue_counts: Counter[str] = Counter()

    for issue in list_open_presentation_issues():
        sections = parse_sections(issue["body"])
        presentation_date = sections.get("발표일", "").strip()
        if not presentation_date or presentation_date >= today:
            continue

        number = str(issue["number"])
        label_names = {l["name"] for l in issue["labels"]}
        if OVERDUE_LABEL not in label_names:
            subprocess.run(["gh", "issue", "edit", number, "--add-label", OVERDUE_LABEL], check=True)

        subprocess.run(
            ["gh", "issue", "comment", number,
             "--body", f"{COMMENT_PREFIX}\n\n{NAG_MESSAGE}"],
            check=True,
        )
        presenter = sections.get("발표자", "").strip() or "(이름 미상)"
        overdue_counts[presenter] += 1

    if overdue_counts:
        ranked = sorted(overdue_counts.items(), key=lambda kv: kv[1], reverse=True)
        lines = "\n".join(nag_line(name, count) for name, count in ranked)
        post_discord(f"{NAG_MESSAGE}\n\n{lines}")
    print(f"overdue: {sum(overdue_counts.values())}")


if __name__ == "__main__":
    main()
