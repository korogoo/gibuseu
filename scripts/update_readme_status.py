#!/usr/bin/env python3
"""README.md의 발표 진행상황 표를 Issue 데이터 기준으로 자동 갱신한다.

STATUS:START ~ STATUS:END 마커 사이만 덮어쓰고 나머지 README 내용은 건드리지 않는다.
발표일별로 묶어서 소제목 + 표로 렌더링한다.
"""
import json
import subprocess
from datetime import date
from pathlib import Path

from lib import CATEGORY_LABELS, parse_sections

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START = "<!-- STATUS:START -->"
END = "<!-- STATUS:END -->"
WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]


def list_issues() -> list[dict]:
    out = subprocess.run(
        ["gh", "issue", "list", "--state", "all",
         "--json", "number,title,url,body,labels", "--limit", "200"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout)


def format_date(d: str) -> str:
    try:
        y, m, day = (int(x) for x in d.split("-"))
        return f"{d} ({WEEKDAYS_KO[date(y, m, day).weekday()]})"
    except ValueError:
        return d


def is_blank(value: str) -> bool:
    return not value or value == "_No response_"


def build_table() -> str:
    by_date: dict[str, list[dict]] = {}

    for issue in list_issues():
        sections = parse_sections(issue["body"])
        presenter = sections.get("발표자", "").strip() or "?"
        presentation_date = sections.get("발표일", "").strip() or "날짜 미정"

        subcategory = sections.get("소분류", "").strip()
        subcategory_other = sections.get("소분류 - 직접 입력", "").strip()
        if subcategory == "기타" and not is_blank(subcategory_other):
            subcategory = subcategory_other

        category = next((l["name"] for l in issue["labels"] if l["name"] in CATEGORY_LABELS), "?")
        field = f"{category} / {subcategory}" if subcategory else category

        blog = sections.get("블로그 링크", "").strip()
        blog_cell = f"[링크]({blog})" if not is_blank(blog) else "-"

        time_cell = sections.get("발표 시간", "").strip() or "-"

        by_date.setdefault(presentation_date, []).append(
            {"presenter": presenter, "time": time_cell, "title": issue["title"], "field": field, "blog": blog_cell}
        )

    if not by_date:
        return "_아직 등록된 발표가 없습니다._"

    def sort_key(d: str) -> str:
        return "9999-99-99" if d == "날짜 미정" else d

    blocks = []
    for d in sorted(by_date, key=sort_key):
        header = d if d == "날짜 미정" else format_date(d)
        rows = "\n".join(
            f"| {r['presenter']} | {r['time']} | {r['title']} | {r['field']} | {r['blog']} |"
            for r in by_date[d]
        )
        blocks.append(
            f"### {header}\n\n"
            "| 닉네임 | 시간 | 발표 제목 | 분야/소분야 | 블로그 |\n"
            "|---|---|---|---|---|\n"
            f"{rows}"
        )
    return "\n\n".join(blocks)


def main() -> None:
    table = build_table()
    content = README.read_text(encoding="utf-8")
    start_idx = content.index(START) + len(START)
    end_idx = content.index(END)
    new_content = f"{content[:start_idx]}\n\n{table}\n\n{content[end_idx:]}"
    README.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    main()
