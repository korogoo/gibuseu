# 기부스 (기술부채상환스터디)

백엔드 실무/CS 지식 발표 + 프로젝트 트러블슈팅 공유 스터디. 스터디원 8명, 팀은 매 회차 3/3/2로 랜덤 배정.
운영 흐름과 파일 구조는 [`README.md`](./README.md) 참고, 카테고리 정의는 [`CATEGORIES.md`](./CATEGORIES.md) 참고.

## 이 레포에서 자주 하는 작업

- **새 회차 준비**: `teams/history.yaml`에서 가장 최근 회차의 팀 구성을 확인하고, `schedule.md`에 새 행을 추가 (회차 번호, 팀 구성까지만 채우고 주제/카테고리는 발표자 PR로 채워짐)
- **팀 랜덤 배정**: 직접 실행하지 말고 GitHub Actions `assign-teams` 워크플로우(`gh workflow run assign-teams.yml`)를 트리거하도록 안내 — 로컬에서 `scripts/assign_teams.py`를 돌리면 `teams/history.yaml`과 실제 저장소 상태가 어긋날 수 있음
- **완료기준 점검**: 유형이 "이론 학습"이면 이론+적용+SBI 3요소가 다 있는지, "트러블슈팅"이면 Situation/Behavior/Impact가 다 있는지 확인
- **디스코드 공지 문구 초안**: `schedule.md`의 해당 회차 행(팀/발표자/발표일/주제)을 바탕으로 짧은 공지 텍스트 작성
- **회고/블로그 링크 반영**: 발표 끝난 뒤 `schedule.md`의 블로그 링크 칸과 상태(`완료`)를 갱신하는 PR 작업

## 주의

- `members.yaml`의 이름이 8명 채워지지 않으면 `assign_teams.py`가 실패함 — 새 세션에서 처음 작업할 때 이 파일이 비어있으면 먼저 사용자에게 이름을 물어볼 것
- `teams/history.yaml`은 자동 생성 파일 — 사람이 직접 편집하지 않는 게 원칙
