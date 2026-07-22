#!/usr/bin/env python3
"""제출된 발표 주제의 연관성(소분류 → 대분류 → 완료기준 키워드)을 기준으로 2~3인 팀을
배정하고 teams/history.yaml에 기록한다. 배정과 동시에 해당 회차 이슈들에 조 라벨(1조/2조/3조)을
붙이고, 왜 그렇게 묶었는지와 조별 발표 주제 링크를 담은 디스코드 공지 문구를 stdout에 출력한다.

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
import os
import random
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

from lib import CATEGORY_LABELS, date_part, parse_sections

OPENAI_MODEL = "gpt-4o-mini"

ROOT = Path(__file__).resolve().parent.parent
MEMBERS_FILE = ROOT / "members.yaml"
HISTORY_FILE = ROOT / "teams" / "history.yaml"
TEAM_SIZES = [3, 3, 2]
INTERVAL_DAYS = 4
WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]
TEAM_LABEL_RE = re.compile(r"^[1-9]\d*조$")
WORD_RE = re.compile(r"[A-Za-z가-힣]{2,}")

# 완료기준 문장에서 내용과 상관없이 반복되는 서술어/접속사류. 도메인 키워드가 아니라
# 글쓰기 템플릿("~를 설명할 수 있다", "~를 이해한다" 등)에서 나오는 단어라 필터링한다.
STOPWORDS = {
    "있다", "없이", "그리고", "이를", "위해", "통해", "대해", "대한",
    "무엇을", "무엇이", "무엇이며", "무엇인가", "무엇이고", "어떤", "어느", "각각", "가지",
    "경우", "시간이", "시작", "진행", "확인", "확인하고", "목표", "방법", "결과", "문제",
    "필요성", "비교", "전체", "전체에서", "영역", "핵심", "답할", "코드나", "그림",
    "말로만", "질문에", "예상", "예시와", "함께", "설명할", "이해한다", "알아본다",
    "학습", "개념", "개념을", "되는", "되는지", "하는지", "하는가", "사라지는지",
    "차단하는지로", "허용", "이상", "현상", "현상을", "높아질수록", "사용하는",
    "사용하는지", "사용해도", "시작하는", "자체가", "이유를", "해야", "만들", "좋을까",
    "작성하면", "제공해야", "자신의", "노출되기", "상단에", "글을", "글이", "구분하기",
    "구분해", "목적", "무너지는가", "믹스", "선정", "재현", "지점", "지점들", "측정과",
    "치솟기", "특징", "환경", "읽는", "차이", "쓰는지", "통합했는지", "성능", "비교표로",
    "성능향상설계", "전에", "전후의", "체크리스트를", "충분할", "시간",
}


@dataclass
class Topic:
    category: str
    subcategory: str
    title: str
    url: str
    criteria: str = ""
    keywords: frozenset[str] = field(default_factory=frozenset)


def gh(*args) -> None:
    # gh는 성공하면 이슈/라벨 URL을 자기 stdout에 찍는다. 이 스크립트의 stdout은
    # 통째로 디스코드 공지 문구로 쓰이므로(assign-teams.yml의 `| tee`), 여기서
    # 새어나가면 공지 앞에 URL 잡음이 붙는다 — 실패 메시지 확인용 stderr만 남긴다.
    subprocess.run(["gh", *args], check=True, stdout=subprocess.DEVNULL)


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


def extract_words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text or "") if w.lower() not in STOPWORDS}


def keywords_by_presenter(raw_words: dict[str, set[str]]) -> dict[str, frozenset[str]]:
    """모든 사람 완료기준에 다 나오는 흔한 단어(설명한다/이해한다류)는 제거하고,
    절반 이하 인원에게만 나오는 단어만 '내용을 드러내는 키워드'로 남긴다. 별도
    금지어 목록을 유지하는 대신 이슈 등록 시마다 자동으로 계산되게 하기 위함."""
    doc_freq = Counter()
    for words in raw_words.values():
        doc_freq.update(words)
    limit = max(1, len(raw_words) // 2)
    return {
        name: frozenset(w for w in words if doc_freq[w] <= limit)
        for name, words in raw_words.items()
    }


def load_topics(round_date: str) -> dict[str, Topic]:
    """round_date에 발표하기로 등록된 이슈들에서 {발표자: Topic}을 읽는다."""
    issues = gh_json(
        "issue", "list", "--state", "open",
        "--json", "number,title,url,body,labels", "--limit", "200",
    )
    partial: dict[str, Topic] = {}
    raw_words: dict[str, set[str]] = {}
    for issue in issues:
        sections = parse_sections(issue["body"])
        if date_part(sections.get("발표일", "")) != round_date:
            continue
        presenter = sections.get("발표자", "").strip()
        if not presenter:
            continue
        # 이슈 라벨 순서 그대로 훑는다 (set으로 바꿔서 훑으면 파이썬 해시 랜덤화 때문에
        # 라벨이 2개 이상인 이슈에서 매번 다른 카테고리가 뽑힐 수 있다 — 재현성 버그였음)
        category = next((l["name"] for l in issue["labels"] if l["name"] in CATEGORY_LABELS), "?")
        subcategory = sections.get("소분류", "").strip()
        subcategory_other = sections.get("소분류 - 직접 입력", "").strip()
        if subcategory == "기타" and subcategory_other and subcategory_other != "_No response_":
            subcategory = subcategory_other
        criteria_text = sections.get("학습 완료기준", "")
        partial[presenter] = Topic(category, subcategory, issue["title"], issue["url"], criteria_text)
        raw_words[presenter] = extract_words(subcategory) | extract_words(criteria_text)

    keywords = keywords_by_presenter(raw_words)
    for presenter, topic in partial.items():
        topic.keywords = keywords.get(presenter, frozenset())
    return partial


def group_by_relevance(names: list[str], topics: dict[str, Topic]) -> list[list[str]]:
    """제출된 주제의 (대분류, 소분류)가 가까운 사람끼리 우선 묶어서 3/3/2 팀으로 나눈다.
    주제를 제출하지 않은 사람(마감 엄수)은 뒤로 보내 가장 작은 조에 강제 편입한다."""
    submitted = [n for n in names if n in topics]
    missing = [n for n in names if n not in topics]

    def sort_key(name: str) -> tuple[str, str, float]:
        topic = topics[name]
        return (topic.category, topic.subcategory, random.random())

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


def llm_group_and_explain(names: list[str], topics: dict[str, Topic]) -> list[dict] | None:
    """OpenAI 저가 모델(gpt-4o-mini)에게 완료기준까지 읽히고 조를 나누게 해본다.
    OPENAI_API_KEY가 없거나 패키지가 없거나 호출/응답이 이상하면 None을 반환해서
    호출부가 규칙 기반(group_by_relevance)으로 대체하게 한다 — 외부 API 장애가
    회차 배정 자체를 막으면 안 되기 때문."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    submitted = [n for n in names if n in topics]
    if len(submitted) < 4:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        print("openai 패키지가 없어서 규칙 기반으로 대체", file=sys.stderr)
        return None

    profile = "\n".join(
        f"- {n} [{topics[n].category}/{topics[n].subcategory}] {topics[n].title}\n"
        f"  완료기준: {topics[n].criteria.strip()[:400]}"
        for n in submitted
    )
    schema = {
        "type": "object",
        "properties": {
            "teams": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "members": {"type": "array", "items": {"type": "string"}},
                        "reason": {"type": "string"},
                    },
                    "required": ["members", "reason"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["teams"],
        "additionalProperties": False,
    }
    prompt = (
        "아래는 스터디원들이 이번 회차에 제출한 발표 주제와 완료기준이다. "
        "내용상 서로 연관된 사람끼리 팀으로 묶어라. "
        f"전체 {len(submitted)}명을 빠짐없이 배정하고, 정확히 3개 팀으로 나누되 "
        "팀 크기는 2 또는 3만 써라(예: 8명이면 3/3/2).\n\n"
        f"{profile}\n\n"
        "각 팀마다 왜 그렇게 묶었는지 한국어로 한 문장씩 써라. 완료기준에 나온 "
        "구체적인 개념·메커니즘이 서로 어떻게 이어지는지 찾아서 그 연결고리를 근거로 설명해라. 예시: "
        "'트랜잭션 격리 수준(정콩이)이 스프링에서 AOP 프록시(캐리)로 실현된다는 연결고리로 묶었어요'. "
        "그런 연결고리가 뚜렷하지 않은 팀은 정직하게 '같은 대분류(◯◯)로 묶었다'고 사실 그대로 설명해라."
    )

    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "team_grouping", "schema": schema, "strict": True},
            },
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI 호출 실패({e}) — 규칙 기반으로 대체", file=sys.stderr)
        return None

    teams = data.get("teams", [])
    all_members = [m for t in teams for m in t.get("members", [])]
    valid = (
        len(teams) == 3
        and sorted(all_members) == sorted(submitted)
        and all(len(t.get("members", [])) in (2, 3) for t in teams)
    )
    if not valid:
        print(
            "OpenAI 응답이 인원 검증에 실패해서 규칙 기반으로 대체 — "
            f"제출자: {sorted(submitted)} / 응답: {[t.get('members') for t in teams]}",
            file=sys.stderr,
        )
        return None

    for name in [n for n in names if n not in topics]:
        min(teams, key=lambda t: len(t["members"]))["members"].append(name)

    return [{"members": sorted(t["members"]), "reason": t["reason"]} for t in teams]


TEAM_LABEL_COLORS = ["C2E0C6", "BFDADC", "F9D0C4", "D4C5F9", "FFE0B2", "B3E5FC"]


def ensure_team_labels_exist(count: int) -> None:
    """조 개수가 늘어나면(예: 8명이 2/2/2/2로 나뉘어 4조까지 필요한 경우) 없는
    'N조' 라벨을 미리 만들어둔다. GitHub는 존재하지 않는 라벨을 붙이려 하면
    에러를 내면서 스크립트 전체가 죽어서, 라벨링 전에 항상 먼저 확인해야 한다."""
    existing = {l["name"] for l in gh_json("label", "list", "--json", "name", "--limit", "200")}
    for i in range(1, count + 1):
        name = f"{i}조"
        if name not in existing:
            color = TEAM_LABEL_COLORS[(i - 1) % len(TEAM_LABEL_COLORS)]
            gh("label", "create", name, "--color", color)


def apply_team_labels(round_date: str, teams: list[list[str]]) -> None:
    ensure_team_labels_exist(len(teams))
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


def common_field_label(team: list[str], topics: dict[str, Topic]) -> str:
    categories = [topics[n].category for n in team if n in topics]
    if not categories:
        return "미제출"
    counts = Counter(categories)
    ordered = sorted(set(categories), key=lambda c: (-counts[c], categories.index(c)))
    return "·".join(ordered)


def explain_team(team: list[str], topics: dict[str, Topic]) -> str:
    present = [n for n in team if n in topics]
    if len(present) < len(team):
        return "주제 미제출자가 있어 가장 작은 조에 편입했어요"
    subs = {topics[n].subcategory for n in present}
    cats = {topics[n].category for n in present}
    if len(subs) == 1:
        return f"모두 '{next(iter(subs))}' 주제라 묶었어요"
    if len(cats) == 1:
        return f"모두 {next(iter(cats))} 분야({'·'.join(sorted(subs))})라 묶었어요"

    cat_desc = common_field_label(team, topics)
    base = (
        f"{cat_desc} 두 분야가 카테고리상 인접해서 묶었어요"
        if len(cats) == 2
        else f"{cat_desc}가 순서대로 인접한 분야라 다리처럼 묶였어요"
    )

    keyword_counts = Counter()
    for n in present:
        keyword_counts.update(topics[n].keywords)
    shared = sorted((w for w, c in keyword_counts.items() if c >= 2), key=lambda w: -keyword_counts[w])
    if shared:
        base += f" ('{', '.join(shared[:2])}' 키워드도 겹쳐요)"
    return base


def build_announcement(
    round_date: date,
    teams: list[list[str]],
    topics: dict[str, Topic],
    reasons: list[str] | None = None,
) -> str:
    lines = [f"😘🫰💸 이번 회차({format_date_kr(round_date)}) 조 편성 나왔습니다", ""]
    for i, team in enumerate(teams, start=1):
        lines.append(f"**{i}조 ({common_field_label(team, topics)})**: {', '.join(team)}")

    lines += ["", "**왜 이렇게 묶었나요?**"]
    for i, team in enumerate(teams, start=1):
        reason = reasons[i - 1] if reasons else explain_team(team, topics)
        lines.append(f"- {i}조: {reason}")

    lines += ["", "📎 **조별 발표 주제**"]
    for i, team in enumerate(teams, start=1):
        lines.append(f"**{i}조**")
        for n in team:
            topic = topics.get(n)
            if topic:
                lines.append(f"- {n}: [{topic.title}]({topic.url})")
            else:
                lines.append(f"- {n}: (주제 미제출)")

    return "\n".join(lines)


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
            print(f"오늘은 다음 회차({round_date.isoformat()})의 D-1이 아니라서 스킵", file=sys.stderr)
            return

    topics = load_topics(round_date.isoformat())
    missing = [n for n in names if n not in topics]
    if missing:
        print(f"주제 미제출: {', '.join(missing)} — 가장 작은 조에 강제 편입해서 진행", file=sys.stderr)

    llm_teams = llm_group_and_explain(names, topics)
    if llm_teams:
        teams = [t["members"] for t in llm_teams]
        reasons = [t["reason"] for t in llm_teams]
        print(f"OpenAI({OPENAI_MODEL})로 완료기준까지 읽고 조 배정", file=sys.stderr)
    else:
        teams = group_by_relevance(names, topics)
        reasons = None

    existing_round = next(
        (r for r in history["rounds"] if r["date"] == round_date.isoformat()), None
    )
    if existing_round:
        existing_round["teams"] = teams
        print(f"기존 회차({round_date.isoformat()})를 재배정 결과로 덮어씀", file=sys.stderr)
    else:
        round_no = (last_round["round"] + 1) if last_round else 1
        history["rounds"].append(
            {"round": round_no, "date": round_date.isoformat(), "teams": teams}
        )
    HISTORY_FILE.write_text(
        yaml.dump(history, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    apply_team_labels(round_date.isoformat(), teams)

    print(build_announcement(round_date, teams, topics, reasons))


if __name__ == "__main__":
    main()
