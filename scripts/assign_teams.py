#!/usr/bin/env python3
"""제출된 발표 주제의 연관성(소분류 → 대분류)을 기준으로 2~3인 팀을 배정하고
teams/history.yaml에 기록한다. 배정과 동시에 해당 회차 이슈들에 조 라벨(1조/2조/3조)을 붙인다.

플로우: D-2 자정까지 주제 제출 → D-1에 이 스크립트가 연관성 기준으로 팀 배정 → D-day 발표.
그래서 이 스크립트는 "회차 날짜"를 직접 만들어내지 않고, 다음 회차 날짜(마지막 회차 +
INTERVAL_DAYS)에 발표일이 일치하는, 이미 제출된 이슈들을 읽어서 배정한다.

주기(4일)마다 한 번씩만 배정하면 되므로, 매일 실행되더라도 오늘이 다음 회차의
D-1이 아니면 그냥 스킵한다. --force를 주면 그 검사를 건너뛴다.
--date로 회차 날짜를 직접 지정할 수도 있다 (예: 3일 주기에서 4일 주기로 전환하는
회차처럼 "마지막 회차 + INTERVAL_DAYS" 공식이 안 맞는 예외적인 경우).
"""
import argparse
import json
import random
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

from lib import CATEGORY_LABELS, date_part, parse_sections

ROOT = Path(__file__).resolve().parent.parent
MEMBERS_FILE = ROOT / "members.yaml"
HISTORY_FILE = ROOT / "teams" / "history.yaml"
TEAM_SIZES = [3, 3, 2]
INTERVAL_DAYS = 4
WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]
TEAM_LABEL_RE = re.compile(r"^[1-9]\d*조$")


def gh(*args) -> None:
    subprocess.run(["gh", *args], check=True)


def gh_json(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def format_date_kr(d: date) -> str:
    return f"{d.month}/{d.day}({WEEKDAYS_KO[d.weekday()]})"


def load_members() -> list[str]:
    data = yaml.safe_load(MEMBERS_FILE.read_text(encoding="utf-8")) or {}
    names = [m["name"] for m in data.get("members", []) if m.get("name")]
    if len(names) != 8:
        sys.exit(f"members.yaml에 이름이 채워진 인원이 8명이어야 합니다 (현재 {len(names)}명)")
    return names


def load_history() -> dict:
    data = yaml.safe_load(HISTORY_FILE.read_text(encoding="utf-8")) or {}
    data.setdefault("rounds", [])
    return data


def load_topics(round_date: str) -> dict[str, tuple[str, str]]:
    """round_date에 발표하기로 등록된 이슈들에서 {발표자: (대분류, 소분류)}를 읽는다."""
    issues = gh_json(
        "issue", "list", "--state", "open",
        "--json", "number,body,labels", "--limit", "200",
    )
    topics: dict[str, tuple[str, str]] = {}
    for issue in issues:
        sections = parse_sections(issue["body"])
        if date_part(sections.get("발표일", "")) != round_date:
            continue
        presenter = sections.get("발표자", "").strip()
        if not presenter:
            continue
        label_names = {l["name"] for l in issue["labels"]}
        category = next((l for l in label_names if l in CATEGORY_LABELS), "?")
        subcategory = sections.get("소분류", "").strip()
        subcategory_other = sections.get("소분류 - 직접 입력", "").strip()
        if subcategory == "기타" and subcategory_other and subcategory_other != "_No response_":
            subcategory = subcategory_other
        topics[presenter] = (category, subcategory)
    return topics


def group_by_relevance(names: list[str], topics: dict[str, tuple[str, str]]) -> list[list[str]]:
    """제출된 주제의 (대분류, 소분류)가 가까운 사람끼리 우선 묶어서 3/3/2 팀으로 나눈다.
    주제를 제출하지 않은 사람(마감 엄수)은 뒤로 보내 가장 작은 조에 강제 편입한다."""
    submitted = [n for n in names if n in topics]
    missing = [n for n in names if n not in topics]

    def sort_key(name: str) -> tuple[str, str, float]:
        category, subcategory = topics[name]
        return (category, subcategory, random.random())

    submitted.sort(key=sort_key)

    teams: list[list[str]] = []
    i = 0
    for size in TEAM_SIZES:
        teams.append(submitted[i : i + size])
        i += size
    while i < len(submitted):
        teams[-1].append(submitted[i])
        i += 1

    for name in missing:
        smallest = min(teams, key=len)
        smallest.append(name)

    return [sorted(t) for t in teams if t]


def apply_team_labels(round_date: str, teams: list[list[str]]) -> None:
    issues = gh_json(
        "issue", "list", "--state", "open",
        "--json", "number,body,labels", "--limit", "200",
    )
    for issue in issues:
        sections = parse_sections(issue["body"])
        if date_part(sections.get("발표일", "")) != round_date:
            continue
        presenter = sections.get("발표자", "").strip()
        team_label = next(
            (f"{i}조" for i, team in enumerate(teams, start=1) if presenter in team), None
        )
        if not team_label:
            continue
        label_names = {l["name"] for l in issue["labels"]}
        stale = {l for l in label_names if TEAM_LABEL_RE.match(l) and l != team_label}
        for label in stale:
            gh("issue", "edit", str(issue["number"]), "--remove-label", label)
        if team_label not in label_names:
            gh("issue", "edit", str(issue["number"]), "--add-label", team_label)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="D-1 여부 검사 없이 강제 배정")
    parser.add_argument("--date", type=str, default=None, help="회차 날짜 직접 지정 (YYYY-MM-DD), D-1 검사 생략")
    args = parser.parse_args()

    names = load_members()
    history = load_history()
    last_round = history["rounds"][-1] if history["rounds"] else None

    if args.date:
        round_date = date.fromisoformat(args.date)
    elif last_round:
        round_date = date.fromisoformat(last_round["date"]) + timedelta(days=INTERVAL_DAYS)
    else:
        round_date = date.today()

    if not args.force and not args.date:
        d_minus_1 = round_date - timedelta(days=1)
        if date.today() != d_minus_1:
            print(f"오늘은 다음 회차({round_date.isoformat()})의 D-1이 아니라서 스킵")
            return

    topics = load_topics(round_date.isoformat())
    missing = [n for n in names if n not in topics]
    if missing:
        print(f"주제 미제출: {', '.join(missing)} — 가장 작은 조에 강제 편입해서 진행")

    teams = group_by_relevance(names, topics)
    round_no = (last_round["round"] + 1) if last_round else 1

    history["rounds"].append(
        {"round": round_no, "date": round_date.isoformat(), "teams": teams}
    )
    HISTORY_FILE.write_text(
        yaml.dump(history, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    apply_team_labels(round_date.isoformat(), teams)

    print(f"이번 회차({format_date_kr(round_date)}) 조 편성 나왔습니다 😘🫰💸")
    for i, team in enumerate(teams, start=1):
        print(f"{i}조: {', '.join(team)}")


if __name__ == "__main__":
    main()
