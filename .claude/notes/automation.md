# 자동화 동작 방식

## 회차 / 조 배정

- 새 회차를 준비할 때는 `teams/history.yaml`에서 최근 회차의 조 구성을 먼저 확인해라
- 조 재배정은 GitHub Actions `assign-teams` 워크플로우로 실행해라 (`gh workflow run assign-teams.yml`). 로컬에서 `scripts/assign_teams.py`를 직접 돌리면 저장소 상태와 어긋날 수 있으니, 항상 워크플로우를 통해 실행해라
- `teams/history.yaml`은 `assign_teams.py` 실행 결과로만 갱신되게 유지해라
- `members.yaml`에는 항상 정확히 8명을 채워둬라 (모자라면 `assign_teams.py`가 실패한다). 세션 시작 시 이 파일이 비어있거나 8명이 아니면 먼저 사용자에게 확인해라

## 발표 등록 검증

- 형식 검사는 `validate-presentation` 워크플로우(`scripts/validate_presentation.py`, 봇 이름 "기부스지킴이")가 자동으로 처리한다 — 결과 코멘트를 신뢰하고 그대로 안내해라
- 검사 항목: 발표자 이름이 `members.yaml`에 있는지, 발표일이 `YYYY-MM-DD`인지, 완료기준이 `-`로 시작하는 줄 2개 이상인지, 소분류 "기타" 선택 시 직접입력이 채워졌는지, 블로그 링크가 URL 형식인지
- 조 라벨(`1조`/`2조`/`3조`)은 발표자 이름을 `teams/history.yaml` 최신 회차와 매칭해서 봇이 자동으로 붙인다. 폼에는 조 입력 필드가 없다

## 카테고리 수정

- 대분류/소분류를 바꿀 때는 `scripts/generate_issue_templates.py`의 `CATEGORIES`를 고치고 스크립트를 다시 실행해라. `CATEGORIES.md`도 같이 갱신해라

## 알림

- `assign-teams`: 조 배정이 실제로 일어난 날에만 디스코드로 공지해라 (스킵된 날은 조용히 지나가게 둬라)
- `remind-missing`: 매일 09시/21시에 실행되지만 "다음 발표일 전날"에만 실제로 알림이 나가게 되어 있다 (하루 2회)
- `remind-overdue`: 매일 09시, 이슈가 닫힐 때까지 매일 반복 알림이 나가게 되어 있다 (의도적으로 중복 방지 없음 — 강제성 확보 목적)
- 모든 알림은 "기부스지킴이" 이름으로 통일해서 보내라 (Discord는 webhook `username` 필드, Issue 코멘트는 본문에 `**기부스지킴이**` 프리픽스)

## Projects 보드

- https://github.com/users/korogoo/projects/8 (번호 8)
- `add-to-project` 워크플로우가 모든 새 Issue를 자동으로 추가한다 (blank issue를 막아뒀으므로 라벨 조건 없이 전부 추가해도 안전하다)
- `PROJECT_TOKEN` 시크릿(개인 gh 토큰, project 스코프)을 쓴다. 토큰을 로테이션하면 이 시크릿도 같이 갱신해라

## 라벨

- '발표' 라벨은 삭제했다. `blank_issues_enabled: false`로 모든 이슈가 발표 등록 템플릿을 거치게 했으므로, `gh issue list`는 라벨 없이 전체로 조회해라
