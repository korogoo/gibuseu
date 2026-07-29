#!/usr/bin/env python3
"""제출된 발표 주제의 연관성(소분류 → 대분류 → 완료기준 키워드)을 기준으로 2~3인 팀을
배정하고 teams/history.yaml에 기록한다. 조는 2인 페어가 기본이고 인원이 홀수일 때만 한 조가
3인이 된다. 배정과 동시에 해당 회차 이슈들에 조 라벨(1조/2조/…)을 붙이고, 왜 그렇게 묶었는지와 조별 발표 주제 링크를 담은 디스코드 공지 문구를 stdout에 출력한다.

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

from lib import CATEGORY_LABELS, date_part, load_members, parse_sections

OPENAI_MODEL = "gpt-4o"  # gpt-4o-mini는 이유 문장이 "같은 분야라서" 수준에서 못 벗어났다

ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "teams" / "history.yaml"
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


def members_for_round(round_date: str) -> list[str]:
    """그 회차를 쉬기로 한 사람(members.yaml의 skip_rounds)을 뺀 참여자 명단."""
    names = load_members(ROOT, round_date)
    if not names:
        sys.exit("members.yaml에 이번 회차 참여자가 없습니다")
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


def team_sizes(total: int) -> list[int]:
    """2인 페어를 기본으로 하고, 인원이 홀수일 때만 한 조를 3인으로 만든다.

    조 개수를 3개로 고정했던 시절이 있었는데, 스터디에서 자동 배정을 뒤집고
    직접 2인 페어로 다시 짜는 일이 생겨서(5회차) 페어 우선으로 바꿨다.
    조가 몇 개가 되든 `ensure_team_labels_exist()`가 'N조' 라벨을 만들어준다.
    """
    if total < 2:
        return [total] if total else []
    sizes = [2] * (total // 2)
    if total % 2:
        sizes[-1] = 3
    return sizes


def fill_missing(
    teams: list[list[str]], sizes: list[int], missing: list[str]
) -> dict[int, list[str]]:
    """주제 미제출자를 목표 크기에 가장 많이 못 미치는 조부터 채운다(제자리 수정).

    어느 조에 누가 편입됐는지 {조 인덱스: [이름]}으로 돌려준다 — 조 편성 이유를
    쓸 때 필요하다. LLM은 제출자만 보고 나누므로 편입 결과를 모르고, 그대로 두면
    3인조를 "단독 팀"이라고 설명하는 일이 생긴다.
    """
    appended: dict[int, list[str]] = {}
    for name in missing:
        idx, _ = max(
            enumerate(teams), key=lambda it: (sizes[it[0]] - len(it[1]), -len(it[1]))
        )
        teams[idx].append(name)
        appended.setdefault(idx, []).append(name)
    return appended


def josa(word: str, pair: str) -> str:
    """받침 유무로 조사를 고른다. pair는 '은는'/'이가'/'과와'처럼 받침 있을 때가 앞."""
    ch = word[-1] if word else ""
    has_batchim = "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28
    return pair[0] if has_batchim else pair[1]


# "키워드(닉네임)" 또는 "'키워드(닉네임)'" 바로 뒤에 붙은 조사를 잡는다.
NICK_JOSA_RE = re.compile(r"\(([^()]{1,20})\)(['\"]?)(은|는|이|가|와|과|을|를)")
JOSA_PAIRS = {
    "은": "은는", "는": "은는", "이": "이가", "가": "이가",
    "와": "과와", "과": "과와", "을": "을를", "를": "을를",
}


def fix_josa_after_nick(text: str, names: list[str]) -> str:
    """'키워드(닉네임)' 뒤 조사를 닉네임 받침에 맞춘다.

    괄호 앞 단어에 맞출지 괄호 안 닉네임에 맞출지는 관례가 갈리는데, LLM이
    실행마다 다르게 쓰는 걸 막으려고 닉네임 기준으로 고정한다.
    """
    def repl(m: re.Match) -> str:
        nick, quote, particle = m.groups()
        if nick not in names:
            return m.group(0)
        return f"({nick}){quote}{josa(nick, JOSA_PAIRS[particle])}"

    return NICK_JOSA_RE.sub(repl, text)


def note_appended(names: list[str]) -> str:
    """주제 미제출로 편입된 사람을 이유 문장 끝에 덧붙이는 문구."""
    if not names:
        return ""
    joined = "·".join(names)
    return f" (주제 미제출한 {joined}{josa(joined, '은는')} 빈자리가 있는 이 조에 편입됐어요)"


def group_by_relevance(names: list[str], topics: dict[str, Topic]) -> list[list[str]]:
    """제출된 주제의 (대분류, 소분류)가 가까운 사람끼리 우선 묶어서 2인 페어 위주로 나눈다.
    주제를 제출하지 않은 사람(마감 엄수)은 뒤로 보내 빈자리가 많은 조에 강제 편입한다."""
    submitted = [n for n in names if n in topics]
    missing = [n for n in names if n not in topics]

    def sort_key(name: str) -> tuple[str, str, float]:
        topic = topics[name]
        return (topic.category, topic.subcategory, random.random())

    submitted.sort(key=sort_key)

    sizes = team_sizes(len(names))
    teams: list[list[str]] = []
    i = 0
    for size in sizes:
        teams.append(submitted[i : i + size])
        i += size
    while i < len(submitted):
        teams[-1].append(submitted[i])
        i += 1

    fill_missing(teams, sizes, missing)

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
    missing = [n for n in names if n not in topics]
    sizes = team_sizes(len(names))
    # 조 개수만큼 제출자가 없으면 LLM이 빈 조를 만들 수밖에 없으니 규칙 기반에 맡긴다.
    if len(submitted) < 4 or len(submitted) < len(sizes):
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
                        # 이름을 자유 문자열로 두면 주제 본문에 나온 단어를 사람 이름으로
                        # 착각해서 뱉는다 (실제로 '커버링 인덱스' 때문에 캐리가 '커버링'으로
                        # 바뀐 적이 있다). enum으로 제출자 이름만 고르게 강제한다.
                        "members": {
                            "type": "array",
                            "items": {"type": "string", "enum": submitted},
                        },
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
        "내용상 서로 연관된 사람끼리 팀으로 묶어라.\n"
        f"배정 대상은 정확히 이 {len(submitted)}명이다: {', '.join(submitted)}. "
        "이 목록에 있는 이름만, 적힌 그대로 써라. 발표 제목이나 완료기준에 나온 기술 용어를 "
        "사람 이름으로 착각하지 마라. 한 사람도 빠뜨리거나 중복시키지 마라.\n"
        f"정확히 {len(sizes)}개 팀으로 나눠라. "
        "2인 페어가 기본이고, 인원이 홀수라 남을 때만 한 팀을 3인으로 만들어라"
        + (
            f" (주제 미제출자 {len(missing)}명이 나중에 작은 팀부터 채워지니, "
            "지금은 1~2인짜리 팀이 나와도 된다)"
            if missing
            else ""
        )
        + ".\n\n"
        f"{profile}\n\n"
        "각 팀마다 왜 그렇게 묶었는지 한국어로 한 문장씩 써라.\n"
        "**형식: 완료기준에서 뽑은 구체적인 키워드 뒤에 그 사람 닉네임을 괄호로 붙이고, "
        "두 키워드가 어떻게 이어지는지 설명해라.** 예시:\n"
        "- '트랜잭션 격리 수준(정콩이)을 스프링이 AOP 프록시(캐리)로 실현한다는 연결고리로 묶었어요'\n"
        "- 'WAL 로그 순서(동키)가 결국 버퍼 풀 플러시 시점(어셔)을 정한다는 점에서 이어져요'\n"
        "키워드는 '데이터베이스', '이론 학습' 같은 분류명이 아니라 완료기준 문장에 실제로 나온 "
        "개념·메커니즘이어야 한다(예: 'B+Tree 리프 노드', '넥스트 키 락', '커버링 인덱스').\n"
        "'같은 분야라서', '기본 개념을 깊이 이해하는 데 도움이 되어서' 같은 뭉뚱그린 설명은 쓰지 마라. "
        "진짜 연결고리가 없으면 억지로 만들지 말고 각자의 키워드만 짚어서 "
        "'A(닉네임)와 B(닉네임)은 직접 이어지진 않지만 둘 다 ◯◯를 다뤄요'처럼 한계를 인정해라.\n"
        "**말투는 '~해요/~예요'체로 써라** — 공지 전체가 그 톤이라 '~합니다'체가 섞이면 어색하다. "
        "'유익할 거예요', '이해를 도울 수 있어요' 같은 군더더기 없이 딱 한 문장, 80자 안쪽으로 끊어라."
    )

    # 검증 실패는 대부분 확률적이라(팀 개수·인원 누락) 한 번은 다시 물어본다. 조용히
    # 규칙 기반으로 떨어지면 "완료기준을 읽고 묶는다"는 기능이 사실상 안 쓰이게 된다.
    client = OpenAI(api_key=api_key)
    for attempt in range(1, 3):
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                # 같은 입력이면 같은 결과가 나오게 고정한다 — 기본값이면 돌릴 때마다
                # 조가 바뀌어서 미리보기로 확인한 결과와 실제 공지가 달라진다.
                # temperature만으로는 이유 문장 표현이 흔들려서 seed까지 준다
                # (OpenAI가 보장하는 건 best-effort라 완전 동일을 장담하진 못한다).
                temperature=0,
                seed=20260731,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "team_grouping", "schema": schema, "strict": True},
                },
            )
            teams = json.loads(resp.choices[0].message.content).get("teams", [])
        except Exception as e:
            print(f"OpenAI 호출 실패({e}) — 규칙 기반으로 대체", file=sys.stderr)
            return None

        all_members = [m for t in teams for m in t.get("members", [])]
        if not (
            len(teams) == len(sizes)
            and sorted(all_members) == sorted(submitted)
            and all(1 <= len(t.get("members", [])) <= 3 for t in teams)
        ):
            print(
                f"OpenAI 응답 인원 검증 실패({attempt}/2) — "
                f"제출자: {sorted(submitted)} / 응답: {[t.get('members') for t in teams]}",
                file=sys.stderr,
            )
            continue

        filled = [t["members"] for t in teams]
        appended = fill_missing(filled, sizes, missing)
        # 미제출자를 채우고 나서도 2~3인이 안 되면(LLM이 한쪽에 몰아준 경우) 다시 시도한다.
        if not all(2 <= len(t) <= 3 for t in filled):
            print(f"채우고 나니 조 크기가 2~3을 벗어남({attempt}/2) — {filled}", file=sys.stderr)
            continue

        # LLM은 제출자만 보고 나눴으니 편입 사실을 모른다 — 이유 문장에 직접 덧붙인다.
        return [
            {
                "members": sorted(t),
                "reason": fix_josa_after_nick(tm["reason"], submitted)
                + note_appended(appended.get(i, [])),
            }
            for i, (t, tm) in enumerate(zip(filled, teams))
        ]

    print("OpenAI 응답이 두 번 다 검증에 실패해서 규칙 기반으로 대체", file=sys.stderr)
    return None


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
    """규칙 기반 조 편성 이유. LLM 경로와 같은 '키워드(닉네임)' 형식을 지킨다."""
    present = [n for n in team if n in topics]
    absent = [n for n in team if n not in topics]

    def with_nick(names: list[str], pick) -> str:
        return "·".join(f"{pick(n)}({n})" for n in names)

    if not present:
        return f"{'·'.join(absent)} 모두 주제를 안 내서 한 조가 됐어요"

    if len(present) == 1:
        n = present[0]
        base = f"{topics[n].subcategory}({n}) 주제예요"
    else:
        last = present[-1]
        subs = {topics[n].subcategory for n in present}
        cats = {topics[n].category for n in present}
        keyword_counts = Counter()
        for n in present:
            keyword_counts.update(topics[n].keywords)
        shared = sorted(
            (w for w, c in keyword_counts.items() if c >= 2), key=lambda w: -keyword_counts[w]
        )
        shared_note = f" ('{', '.join(shared[:2])}' 키워드가 겹쳐요)" if shared else ""

        if len(subs) == 1:
            # 소분류까지 같으면 키워드(닉네임)을 나열해봐야 같은 말이 반복될 뿐이다.
            base = f"{'·'.join(present)} 모두 '{next(iter(subs))}' 주제라 묶었어요" + shared_note
        elif shared:
            base = (
                f"{with_nick(present, lambda n: topics[n].subcategory)}"
                f"{josa(last, '이가')} '{', '.join(shared[:2])}' 키워드로 이어져요"
            )
        elif len(cats) == 1:
            base = (
                f"{with_nick(present, lambda n: topics[n].subcategory)}"
                f"{josa(last, '이가')} 같은 {next(iter(cats))} 분야라 묶었어요"
            )
        else:
            base = (
                f"{with_nick(present, lambda n: topics[n].category)}"
                f"{josa(last, '은는')} 직접 이어지진 않지만 카테고리가 인접해서 묶었어요"
            )

    return base + note_appended(absent)


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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="배정 결과를 계산만 하고 history.yaml 기록·조 라벨은 건드리지 않는다 (미리보기용)",
    )
    args = parser.parse_args()

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

    # 회차 날짜가 정해진 뒤에 명단을 읽는다 — 이번 회차를 쉬는 사람을 빼야 하기 때문.
    names = members_for_round(round_date.isoformat())
    topics = load_topics(round_date.isoformat())
    missing = [n for n in names if n not in topics]
    if missing:
        print(f"주제 미제출: {', '.join(missing)} — 빈자리가 많은 조에 강제 편입해서 진행", file=sys.stderr)

    llm_teams = llm_group_and_explain(names, topics)
    if llm_teams:
        teams = [t["members"] for t in llm_teams]
        reasons = [t["reason"] for t in llm_teams]
        print(f"OpenAI({OPENAI_MODEL})로 완료기준까지 읽고 조 배정", file=sys.stderr)
    else:
        teams = group_by_relevance(names, topics)
        reasons = None

    if args.dry_run:
        # 미리보기 — history.yaml도 조 라벨도 건드리지 않는다. history.yaml이 그대로면
        # 워크플로우의 커밋 스텝이 no-op이 되고, 디스코드 공지도 따라서 안 나간다.
        print("[dry-run] 기록·라벨·디스코드 공지 없이 결과만 출력한다", file=sys.stderr)
        print(build_announcement(round_date, teams, topics, reasons))
        return

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
