# 기부스 (기술부채상환스터디)

백엔드 실무/CS 지식을 발표로 정리하고, 프로젝트에서 겪은 트러블슈팅을 서로 공유하는 스터디입니다.

## 운영 흐름

1. **주제 확정** — 발표자가 New Issue → "발표 등록" 템플릿으로 주제/카테고리/완료기준을 등록 (카테고리는 드롭다운으로 선택, CATEGORIES.md 참고할 필요 없음)
2. **팀 배정** — Actions 탭에서 `assign-teams` 워크플로우를 수동 실행하면 스터디원 8명을 3/3/2로 랜덤 배정 (직전 회차와 동일 조합은 재시도)
3. **디스코드 공지** — 배정 결과 + 발표 시간을 디스코드에 공유
4. **온라인 발표** — 디스코드에서 발표 진행
5. **기록** — 발표자가 정리한 내용을 각자 블로그에 올리고, 링크를 Issue 코멘트에 남긴 뒤 Issue를 닫음(완료 처리)

## 구조

```
members.yaml              # 스터디원 명단
CATEGORIES.md              # 대분류/소분류/유형 정의 (Issue Form 드롭다운의 참고표)
.github/ISSUE_TEMPLATE/presentation.yml  # 발표 등록 폼 (New Issue에서 사용)
teams/history.yaml         # 팀 배정 이력 (자동 갱신)
scripts/assign_teams.py    # 랜덤 팀 배정 스크립트
.github/workflows/assign-teams.yml  # 팀 배정 자동화 워크플로우
```

## 팀 랜덤 배정 실행 방법

1. GitHub 저장소 → Actions 탭 → `assign-teams` 워크플로우 선택
2. `Run workflow` 클릭
3. `teams/history.yaml`에 새 회차 배정 결과가 자동 커밋됨
