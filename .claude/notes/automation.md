# 자동화 동작 방식

## 회차 / 조 배정

- 새 회차를 준비할 때는 `teams/history.yaml`에서 최근 회차의 조 구성을 먼저 확인해라
- 조 재배정은 GitHub Actions `assign-teams` 워크플로우로 실행해라 (`gh workflow run assign-teams.yml`). 로컬에서 `scripts/assign_teams.py`를 직접 돌리면 저장소 상태와 어긋날 수 있으니, 항상 워크플로우를 통해 실행해라
- `teams/history.yaml`은 `assign_teams.py` 실행 결과로만 갱신되게 유지해라
- `members.yaml`에는 항상 정확히 8명을 채워둬라 (모자라면 `assign_teams.py`가 실패한다). 세션 시작 시 이 파일이 비어있거나 8명이 아니면 먼저 사용자에게 확인해라

## 발표 등록 검증

- 형식 검사는 `validate-presentation` 워크플로우(`scripts/validate_presentation.py`, 봇 이름 "기부스지키미👀💸")가 자동으로 처리한다 — 결과 코멘트를 신뢰하고 그대로 안내해라
- 검사 항목: 발표자 이름이 `members.yaml`에 있는지, 발표일이 `YYYY-MM-DD`인지, 발표 시간이 `HH:MM`인지, 완료기준이 `-`로 시작하는 줄 2개 이상인지, 소분류 "기타" 선택 시 직접입력이 채워졌는지, 블로그 링크가 URL 형식인지
- 조 라벨(`1조`/`2조`/`3조`)은 발표자 이름을 `teams/history.yaml` 최신 회차와 매칭해서 봇이 자동으로 붙인다. 폼에는 조 입력 필드가 없다
- 문제 없이 등록된 이슈는 디스코드에 "📢 새 발표 등록!"으로 주제/분야/발표자/일시를 공지한다 (`state/announced.json`으로 중복 방지, 이슈당 최초 1회). 이미 공지된 이슈가 수정(edited)되면 "✏️ 발표 정보 수정됨" 알림을 추가로 보낸다

## 카테고리 수정

- 대분류/소분류를 바꿀 때는 `scripts/generate_issue_templates.py`의 `CATEGORIES`를 고치고 스크립트를 다시 실행해라. `CATEGORIES.md`도 같이 갱신해라

## 알림 (기술부채상환 컨셉으로 유쾌한 톤 유지)

- `assign-teams`: 조 배정이 실제로 일어난 날에만 디스코드로 공지해라 (스킵된 날은 조용히 지나가게 둬라). 문구: "이번 회차(N/D(요일)) 조 편성 나왔습니다 😘🫰💸"
- `remind-missing`: 매일 09시/21시에 실행되지만 "다음 발표일 전날"에만 실제로 알림이 나가게 되어 있다 (하루 2회). 문구는 "💸 아직 발표 빚 안 갚은 사람" 톤 유지
- `remind-overdue`: 매일 09시, 이슈가 닫힐 때까지 매일 반복 알림이 나가게 되어 있다 (의도적으로 중복 방지 없음 — 강제성 확보 목적). 고정 문구: "취업은 조상님이 시켜주나요? 미루지 말고 블로그 작성하세요👴🏻💸"
- `remind-one-hour`: 15분 간격 스케줄 + Issue opened/edited 이벤트, 두 트리거로 실행된다. 각 Issue의 발표일+발표 시간(KST, `zoneinfo` 사용)을 계산해서 "목표 시각 - 1시간"을 넘긴 걸 발견하면 그때 한 번만 알린다. `state/reminded_one_hour.json`으로 중복 방지 (라벨 아님 — 이슈에 내부용 라벨이 보이는 걸 원치 않는다는 운영 방침). 발표 시간이 회차마다 다르므로 고정 시각이 아니라 Issue별로 계산해야 한다. GitHub Actions는 "미래 특정 시각에 실행"하는 진짜 예약 기능이 없어서 폴링 + 이벤트 트리거 조합이 최선이다 (등록 직후 목표시각이 이미 1시간 이내로 임박한 경우를 이벤트 트리거가 즉시 잡아줌)
- `notify-deleted`: 이슈가 삭제(deleted)되면 "🗑️ 발표 취소/삭제됨" 알림. 삭제된 이슈는 API로 재조회가 안 되니 웹훅 payload(`github.event.issue.*`)를 env로 직접 넘겨 쓴다
- Discord는 webhook `username` 필드에 `기부스지키미👀` (BOT_NAME), Issue 코멘트는 본문에 `**[기부스지키미👀💸]**` 프리픽스(볼드) (COMMENT_PREFIX) — 둘 다 `scripts/lib.py` 상수를 써라, 표기가 서로 다른 게 의도된 것이다
- 새 알림 문구를 추가할 때는 이 유쾌한 "기술부채 갚기" 톤을 유지해라 (진지한 사무 톤으로 되돌리지 마라)

## Projects 보드

- https://github.com/users/korogoo/projects/8 (번호 8, project id `PVT_kwHOB4mJYs4Bd4Md`), 현재 private
- `add-to-project` 워크플로우(issues opened/edited)가 `scripts/sync_project.py`를 실행해서: (1) 이슈를 보드에 추가하고 (2) 이슈 본문의 발표일을 "발표일" Date 필드(field id `PVTF_lAHOB4mJYs4Bd4MdzhYWe5k`)에 동기화한다. item-add는 이미 추가된 항목에 다시 호출해도 안전(idempotent)하다
- `PROJECT_TOKEN` 시크릿(개인 gh 토큰, project 스코프)을 쓴다. 토큰을 로테이션하면 이 시크릿도 같이 갱신해라
- GitHub Projects v2에는 "캘린더" 뷰가 따로 없다 — 발표일 Date 필드를 타임라인으로 보려면 보드에서 사람이 직접 "New view → Roadmap"으로 뷰를 하나 만들어야 한다 (CLI로 뷰 생성은 지원 안 됨). 이 저장소 문서에서 "캘린더"라고 쓰지 말고 "Roadmap/타임라인 뷰"라고 정확히 표현해라

## 라벨

- '발표' 라벨은 삭제했다. `blank_issues_enabled: false`로 모든 이슈가 발표 등록 템플릿을 거치게 했으므로, `gh issue list`는 라벨 없이 전체로 조회해라
- '1시간전알림' 라벨도 삭제했다. 이슈에 사람이 볼 필요 없는 내부용 라벨을 남기지 않는 게 운영 방침 — 새로 중복방지 로직을 추가할 때 라벨이 아니라 `state/*.json` 파일을 써라

## 상태 파일 (state/)

- `state/announced.json`, `state/reminded_one_hour.json` — 이슈 번호 배열을 담은 JSON. `lib.py`의 `load_state_set`/`save_state_set`으로 읽고 쓴다
- 이 파일들을 쓰는 워크플로우(`validate-presentation`, `remind-one-hour`)는 `contents: write` 권한과 커밋 스텝이 필요하다. 같은 이슈 이벤트에 여러 워크플로우(`add-to-project`, `update-readme` 포함)가 동시에 커밋을 시도해서 push가 경합할 수 있으므로, 커밋 스텝은 실패하면 `git fetch` + `git rebase` 후 재시도하는 루프를 넣어라 (기존 커밋 스텝들 참고)

## README 발표 진행상황 표

- `update-readme` 워크플로우가 Issue open/edited/closed/reopened마다 `scripts/update_readme_status.py`를 실행해서 README.md의 `<!-- STATUS:START -->`~`<!-- STATUS:END -->` 구간을 자동으로 다시 쓴다
- 발표일별로 묶어서(소제목 + 표) 렌더링한다. 닉네임/발표 제목/분야·소분야/블로그 링크 컬럼을 쓴다
- 이 구간은 자동 생성이니 사람이 직접 손으로 고치지 말고, 표 형식을 바꾸고 싶으면 `update_readme_status.py`를 수정해라
