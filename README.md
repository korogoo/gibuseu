# 기부스 (기술부채상환스터디)

백엔드 실무/CS 지식을 발표로 정리하고, 프로젝트에서 겪은 트러블슈팅을 서로 공유하는 스터디입니다.
스터디원 8명 전원이 각자 발표합니다. "조"는 같은 시간에 모여서 같이 듣고 발표하기 위한 스케줄링 단위일 뿐, 조당 1명만 발표하는 게 아닙니다.

## 운영 흐름

1. **조 배정** — 발표 주기는 3일에 1번. `assign-teams`가 매일 자동 실행되지만 마지막 배정으로부터 3일이 안 지났으면 스킵하고, 3일이 지난 날에만 실제로 8명을 3/3/2 조로 랜덤 배정 (직전 회차와 동일 조합은 재시도). 배정이 실제로 일어난 날만 결과가 **디스코드에 자동 공지**됨. 급하게 주기 무시하고 재배정하려면 Actions 탭에서 `assign-teams` → `Run workflow` → `force` 체크
2. **주제 확정** — 발표자가 New Issue에서 대분류에 맞는 템플릿(예: "발표 등록 - 데이터베이스")을 고르고, 제목에 발표 주제를 바로 적어서 등록 (조/소분류/유형/완료기준은 드롭다운·텍스트로 채움, CATEGORIES.md 참고할 필요 없음). 등록되면 자동으로:
   - 대분류 라벨(`CS`/`데이터베이스`/... , 색상 지정됨) 부여
   - `assign-author`가 작성자 본인을 assignee로 지정 (작성자가 레포 협업자여야 성공)
   - `validate-presentation`이 발표일 형식/완료기준 줄 수/소분류-기타 누락을 검사, 문제 있으면 코멘트 + `형식 확인 필요` 라벨
   - `add-to-project`가 [Projects 보드](https://github.com/users/korogoo/projects/8)에 자동 추가 (발표일은 Date 필드라 보드에서 캘린더로 볼 수 있음)
3. **온라인 발표** — 디스코드에서 조원들이 각자 준비한 주제를 발표
4. **기록** — 발표자가 정리한 내용을 각자 블로그에 올리고, 링크를 Issue 코멘트에 남긴 뒤 Issue를 닫음(완료 처리)

## 리마인더 (매일 자동 실행)

- `remind-missing` — 이번 회차 조 배정 이후 아직 발표 Issue를 안 올린 스터디원이 있으면 디스코드로 알림
- `remind-overdue` — 발표일이 지났는데 아직 열려있는(블로그 링크 미기재) Issue에 코멘트 + `발표일 지남` 라벨 부여, 디스코드로도 알림 (한 Issue당 한 번만)

## 구조

```
members.yaml                              # 스터디원 명단
CATEGORIES.md                             # 대분류/소분류/유형 정의 (Issue Form 드롭다운의 참고표)
.github/ISSUE_TEMPLATE/presentation-*.yml # 대분류별 발표 등록 폼 (New Issue에서 사용)
scripts/generate_issue_templates.py       # 위 템플릿들을 생성하는 스크립트 (카테고리 바뀌면 재실행)
teams/history.yaml                        # 조 배정 이력 (자동 갱신)
scripts/assign_teams.py                   # 랜덤 조 배정 스크립트
.github/workflows/assign-teams.yml        # 조 배정 자동화 워크플로우
.github/workflows/validate-presentation.yml # 발표 등록 Issue 형식 자동 검사 봇
.github/workflows/assign-author.yml       # 작성자를 assignee로 자동 지정
.github/workflows/add-to-project.yml      # 새 발표 Issue를 Projects 보드에 자동 추가
.github/workflows/remind-missing.yml      # 미등록자 디스코드 리마인더 (매일)
.github/workflows/remind-overdue.yml      # 발표일 지난 미완료 Issue 리마인더 (매일)
scripts/lib.py                            # 리마인더 스크립트 공용 헬퍼 (Issue 본문 파싱, 디스코드 전송)
```

Discord 알림을 쓰려면 저장소 Settings → Secrets → `DISCORD_WEBHOOK_URL`이 등록돼 있어야 합니다 (이미 설정됨).

## 조 랜덤 배정 수동/강제 실행 방법

1. GitHub 저장소 → Actions 탭 → `assign-teams` 워크플로우 선택
2. `Run workflow` 클릭 (3일 안 지났으면 강제로 하려는 게 아닌 이상 `force` 체크 안 해도 됨 — 매일 자동으로도 돌아감)
3. `teams/history.yaml`에 새 회차 배정 결과가 자동 커밋됨

> 1회차(2026-07-19, 자동화 세팅 전)는 실제 배정 결과를 수기로 `teams/history.yaml`에 넣어뒀습니다. 이 회차엔 대응하는 Issue가 없어서, `remind-missing`이 2회차가 시작되기 전까지는 8명 전원을 "미등록"으로 계속 알릴 수 있습니다 — 정상입니다. 2회차(2026-07-22)부터는 정확해집니다.
