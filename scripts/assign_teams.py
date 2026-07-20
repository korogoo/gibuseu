#!/usr/bin/env python3
"""8명의 스터디원을 3/3/2 팀으로 랜덤 배정하고 teams/history.yaml에 기록한다."""
import random
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MEMBERS_FILE = ROOT / "members.yaml"
HISTORY_FILE = ROOT / "teams" / "history.yaml"
TEAM_SIZES = [3, 3, 2]
MAX_RETRY = 30


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


def split_teams(names: list[str]) -> list[list[str]]:
    shuffled = names[:]
    random.shuffle(shuffled)
    teams, i = [], 0
    for size in TEAM_SIZES:
        teams.append(sorted(shuffled[i : i + size]))
        i += size
    return teams


def as_group_set(teams: list[list[str]]) -> set[frozenset[str]]:
    return {frozenset(t) for t in teams}


def assign(names: list[str], last_teams: list[list[str]] | None) -> list[list[str]]:
    last_set = as_group_set(last_teams) if last_teams else None
    for _ in range(MAX_RETRY):
        teams = split_teams(names)
        if last_set is None or as_group_set(teams) != last_set:
            return teams
    return teams  # 재시도 다 써도 못 피하면 그냥 반환


def main() -> None:
    names = load_members()
    history = load_history()
    last_round = history["rounds"][-1] if history["rounds"] else None
    last_teams = last_round["teams"] if last_round else None

    teams = assign(names, last_teams)
    round_no = (last_round["round"] + 1) if last_round else 1

    history["rounds"].append(
        {"round": round_no, "date": date.today().isoformat(), "teams": teams}
    )
    HISTORY_FILE.write_text(
        yaml.dump(history, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    print(f"# {round_no}회차 팀 배정 ({date.today().isoformat()})")
    for i, team in enumerate(teams, start=1):
        print(f"팀{i}: {', '.join(team)}")


if __name__ == "__main__":
    main()
