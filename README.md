# 기부스 (기술부채상환스터디)

백엔드 실무/CS 지식을 발표로 정리하고, 프로젝트에서 겪은 트러블슈팅을 서로 공유하는 스터디입니다.
스터디원 8명 전원이 각자 발표합니다. "조"는 같은 시간에 모여서 같이 듣고 발표하기 위한 스케줄링 단위일 뿐, 조당 1명만 발표하는 게 아닙니다.

## 운영 흐름

1. **주제 확정** — 발표자가 New Issue에서 대분류에 맞는 템플릿(예: "발표 등록 - 데이터베이스")을 고르고, 제목에 발표 주제를 바로 적어서 등록 (조/소분류/유형/완료기준은 드롭다운·텍스트로 채움, CATEGORIES.md 참고할 필요 없음). 등록하면 `validate-presentation` 워크플로우가 발표일 형식/완료기준 줄 수/소분류-기타 누락을 자동 검사해서 문제가 있으면 코멘트를 남기고 `형식 확인 필요` 라벨을 붙임
2. **조 배정** — Actions 탭에서 `assign-teams` 워크플로우를 수동 실행하면 스터디원 8명을 3/3/2 조로 랜덤 배정 (직전 회차와 동일 조합은 재시도)
3. **디스코드 공지** — 조 배정 결과 + 모이는 시간을 디스코드에 공유
4. **온라인 발표** — 디스코드에서 조원들이 각자 준비한 주제를 발표
5. **기록** — 발표자가 정리한 내용을 각자 블로그에 올리고, 링크를 Issue 코멘트에 남긴 뒤 Issue를 닫음(완료 처리)

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
```

## 조 랜덤 배정 실행 방법

1. GitHub 저장소 → Actions 탭 → `assign-teams` 워크플로우 선택
2. `Run workflow` 클릭
3. `teams/history.yaml`에 새 회차 배정 결과가 자동 커밋됨
