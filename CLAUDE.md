# 기부스 (기술부채상환스터디)

백엔드 실무/CS 지식 발표 + 프로젝트 트러블슈팅 공유 스터디. 스터디원 8명 전원이 각자 발표하며,
"조"는 매 회차 3/3/2로 랜덤 배정하는 스케줄링(같이 듣는) 단위일 뿐 조당 1명만 발표하는 게 아님.
운영 흐름과 파일 구조는 [`README.md`](./README.md) 참고, 스터디원용 사용법은 [`GUIDE.md`](./GUIDE.md), 카테고리 정의는 [`CATEGORIES.md`](./CATEGORIES.md) 참고.

## 운영 상태 (중요)

아직 스터디 그룹에 정식 공지 전입니다. `DISCORD_WEBHOOK_URL` 시크릿이 개인 테스트 채널로 걸려있고,
`assign-teams`의 `schedule` 트리거는 주석 처리되어 꺼져있습니다 (3회차가 자동으로 생기지 않도록).
사용자가 "이제 운영 시작"이라고 명시적으로 말하기 전까지는:
- `assign-teams.yml`의 schedule 주석을 풀지 말 것
- `DISCORD_WEBHOOK_URL`을 실제 스터디 채널 웹훅으로 바꾸지 말 것
운영 시작 신호가 오면 이 두 가지를 같이 처리하고, 이 섹션을 지울 것.

## 이 레포에서 자주 하는 작업

- **새 회차 준비**: `teams/history.yaml`에서 가장 최근 회차의 조 구성을 확인하고, 발표자들에게 New Issue에서 대분류에 맞는 템플릿(`발표 등록 - CS` 등)으로 등록하도록 안내 — 제목이 곧 발표 주제
- **조 랜덤 배정**: 직접 실행하지 말고 GitHub Actions `assign-teams` 워크플로우(`gh workflow run assign-teams.yml`)를 트리거하도록 안내 — 로컬에서 `scripts/assign_teams.py`를 돌리면 `teams/history.yaml`과 실제 저장소 상태가 어긋날 수 있음
- **카테고리 수정**: 대분류/소분류를 바꾸고 싶다는 요청이 오면 `scripts/generate_issue_templates.py`의 `CATEGORIES`를 고치고 다시 실행 (`.github/ISSUE_TEMPLATE/presentation-*.yml`이 재생성됨), `CATEGORIES.md`도 같이 갱신
- **완료기준 점검**: 등록된 Issue에서 유형이 "이론 학습"이면 다룰 개념과 정리 범위가, "트러블슈팅"이면 문제 상황과 해결 방법이 채워져 있는지 확인 (SBI 같은 고정 포맷을 강요하지 않음 — 자유 서술). 형식(발표일/완료기준 줄 수/소분류-기타 누락)은 `validate-presentation` 워크플로우가 자동으로 검사해서 코멘트 남김 — 수동으로 다시 검사할 필요 없음
- **조 라벨 확인**: Issue Form의 "조" 답변이 그대로 라벨(`1조`/`2조`/`3조`)로도 붙으므로 `gh issue list --label 1조` 식으로 조별 등록 현황 확인 가능
- **디스코드 알림**: `assign-teams`(조 배정 결과, 실제 배정 일어난 날만), `remind-missing`(미등록자 — 매일 09:00/21:00 KST에 실행되지만 다음 발표일 "전날"에만 실제로 알림), `remind-overdue`(발표일 지난 미완료 건 — 매일 09:00 KST, 닫힐 때까지 매일 반복. 일부러 dedup 안 함, 강제성 확보가 목적)가 `DISCORD_WEBHOOK_URL` 시크릿으로 자동 발송됨
- **Projects 보드**: https://github.com/users/korogoo/projects/8 (번호 8). `add-to-project` 워크플로우가 `발표` 라벨 붙은 새 Issue를 자동으로 넣음. 이 워크플로우는 `PROJECT_TOKEN` 시크릿(개인 gh 인증 토큰, project 스코프 포함)을 씀 — 토큰 로테이션 시 이 시크릿도 같이 갱신해야 함
- **디스코드 공지 문구 초안**: 해당 회차 Issue(발표자/발표일/주제)를 바탕으로 짧은 공지 텍스트 작성 (`gh issue list --label 발표`로 확인)
- **회고/블로그 링크 반영**: 발표 끝난 뒤 해당 Issue에 블로그 링크를 코멘트로 남기고 `gh issue close`로 완료 처리

## 주의

- `members.yaml`에 이름이 8명 채워져 있지 않으면 `assign_teams.py`가 실패함 — 새 세션에서 이 파일이 비어있거나 8명이 아니면 먼저 사용자에게 확인할 것
- `teams/history.yaml`은 자동 생성 파일 — 사람이 직접 편집하지 않는 게 원칙
