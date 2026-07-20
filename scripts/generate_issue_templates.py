#!/usr/bin/env python3
"""대분류별 발표 등록 Issue Form(.github/ISSUE_TEMPLATE/presentation-*.yml)을 생성한다.

GitHub Issue Form은 '대분류 선택에 따라 소분류 옵션이 바뀌는' 조건부 드롭다운을
지원하지 않는다. 그래서 대분류마다 템플릿을 따로 만들어 New Issue에서
템플릿을 고르는 것 자체가 대분류 선택이 되도록 한다. CATEGORIES.md를 고치면
이 스크립트를 다시 실행해서 템플릿을 갱신한다.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / ".github" / "ISSUE_TEMPLATE"

# (대분류, 파일 슬러그, 소분류 목록)
CATEGORIES = [
    ("CS", "cs", ["컴퓨터 구조", "운영체제", "네트워크", "자료구조 & 알고리즘", "JVM & 언어"]),
    ("데이터베이스", "db", ["인덱스 & 쿼리 최적화", "트랜잭션 & 정합성", "락 & 동시성"]),
    ("인프라/DevOps", "infra", ["배포 & 인프라", "모니터링 & 관측성", "CI/CD"]),
    ("아키텍처", "arch", ["캐시", "메시징 & 이벤트", "MSA & 서비스 간 통신"]),
    ("보안", "security", ["인증 & 인가", "암호화 & OWASP"]),
    ("테스트/QA", "test", ["테스트 전략", "테스트 더블 & TDD"]),
    ("AI", "ai", ["LLM 활용 / RAG", "추천 시스템"]),
]


def render(category: str, subcategories: list[str]) -> str:
    sub_options = "\n".join(f'        - "{s}"' for s in subcategories)
    return f"""name: "발표 등록 - {category}"
description: "{category} 분야 발표를 등록합니다. 제목에 발표 주제를 바로 적어주세요."
labels: ["발표", "{category}"]
body:
  - type: input
    id: presenter
    attributes:
      label: 발표자
      placeholder: 행성이
    validations:
      required: true

  - type: input
    id: date
    attributes:
      label: 발표일
      placeholder: "YYYY-MM-DD"
    validations:
      required: true

  - type: dropdown
    id: subcategory
    attributes:
      label: 소분류
      options:
{sub_options}
        - "기타"
    validations:
      required: true

  - type: input
    id: subcategory_other
    attributes:
      label: 소분류 - 직접 입력
      description: 위에서 "기타"를 선택했다면 여기에 적어주세요
    validations:
      required: false

  - type: dropdown
    id: type
    attributes:
      label: 유형
      options:
        - "이론 학습"
        - "트러블슈팅"
    validations:
      required: true

  - type: textarea
    id: criteria
    attributes:
      label: 학습 완료기준
      description: 이론 학습이면 다룰 개념과 어디까지 정리할지, 트러블슈팅이면 어떤 문제였고 어떻게 해결했는지 자유롭게 적어주세요.
    validations:
      required: false

  - type: input
    id: blog
    attributes:
      label: 블로그 링크
      description: 발표 끝난 뒤 채워도 됩니다
    validations:
      required: false
"""


def main() -> None:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    for category, slug, subcategories in CATEGORIES:
        path = TEMPLATE_DIR / f"presentation-{slug}.yml"
        path.write_text(render(category, subcategories), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
