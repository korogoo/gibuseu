# 기부스 (기술부채상환스터디)

백엔드 실무/CS 지식 발표 + 프로젝트 트러블슈팅 공유 스터디. 스터디원 8명 전원이 각자 발표하며,
"조"는 매 회차 3/3/2로 랜덤 배정하는 스케줄링(같이 듣는) 단위일 뿐 조당 1명만 발표하는 게 아님.
운영 흐름과 파일 구조는 [`README.md`](./README.md) 참고, 카테고리 정의는 [`CATEGORIES.md`](./CATEGORIES.md) 참고.

## 이 레포에서 자주 하는 작업

- **새 회차 준비**: `teams/history.yaml`에서 가장 최근 회차의 조 구성을 확인하고, 발표자들에게 New Issue에서 대분류에 맞는 템플릿(`발표 등록 - CS` 등)으로 등록하도록 안내 — 제목이 곧 발표 주제
- **조 랜덤 배정**: 직접 실행하지 말고 GitHub Actions `assign-teams` 워크플로우(`gh workflow run assign-teams.yml`)를 트리거하도록 안내 — 로컬에서 `scripts/assign_teams.py`를 돌리면 `teams/history.yaml`과 실제 저장소 상태가 어긋날 수 있음
- **카테고리 수정**: 대분류/소분류를 바꾸고 싶다는 요청이 오면 `scripts/generate_issue_templates.py`의 `CATEGORIES`를 고치고 다시 실행 (`.github/ISSUE_TEMPLATE/presentation-*.yml`이 재생성됨), `CATEGORIES.md`도 같이 갱신
- **완료기준 점검**: 등록된 Issue에서 유형이 "이론 학습"이면 다룰 개념과 정리 범위가, "트러블슈팅"이면 문제 상황과 해결 방법이 채워져 있는지 확인 (SBI 같은 고정 포맷을 강요하지 않음 — 자유 서술)
- **디스코드 공지 문구 초안**: 해당 회차 Issue(발표자/발표일/주제)를 바탕으로 짧은 공지 텍스트 작성 (`gh issue list --label 발표`로 확인)
- **회고/블로그 링크 반영**: 발표 끝난 뒤 해당 Issue에 블로그 링크를 코멘트로 남기고 `gh issue close`로 완료 처리

## 주의

- `members.yaml`에 이름이 8명 채워져 있지 않으면 `assign_teams.py`가 실패함 — 새 세션에서 이 파일이 비어있거나 8명이 아니면 먼저 사용자에게 확인할 것
- `teams/history.yaml`은 자동 생성 파일 — 사람이 직접 편집하지 않는 게 원칙
