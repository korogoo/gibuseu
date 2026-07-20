# 기부스 (기술부채상환스터디)

백엔드 실무/CS 지식을 발표로 정리하고, 프로젝트에서 겪은 트러블슈팅을 서로 공유하는 스터디입니다.

## 운영 흐름

- 3일에 1번, 온라인(디스코드)으로 발표
- 매 발표마다 스터디원 8명을 2~3인 조로 랜덤 배정 (같이 듣는 스케줄링 단위 — 조당 한 명만 발표하는 게 아니라 전원 각자 발표)
- 발표 등록·형식 검사·일정 관리는 GitHub Issues/Actions/Projects로 자동화되어 있음

발표 등록 방법과 등록 이후 자동으로 일어나는 일은 [`GUIDE.md`](./GUIDE.md) 참고.

> ⚠️ 현재 정식 운영 시작 전 상태입니다 (개인 테스트 웹훅 사용 중, 조 배정 자동 실행은 꺼둠). 자세한 내용은 [`CLAUDE.md`](./CLAUDE.md) 참고.

## 구조

| 파일/경로 | 설명 |
|---|---|
| [`GUIDE.md`](./GUIDE.md) | 스터디원용 — 발표 등록 방법, 자동화 동작, 리마인더 안내 |
| [`CATEGORIES.md`](./CATEGORIES.md) | 발표 대분류/소분류/유형 정의 |
| [`members.yaml`](./members.yaml) | 스터디원 명단 |
| [`teams/history.yaml`](./teams/history.yaml) | 회차별 조 배정 이력 |
| [`.github/ISSUE_TEMPLATE/`](./.github/ISSUE_TEMPLATE) | 대분류별 발표 등록 폼 |
| [`scripts/`](./scripts) | 조 배정·리마인더·Issue Form 생성 스크립트 |
| [`.github/workflows/`](./.github/workflows) | 조 배정·형식 검사·assignee 지정·Projects 연동·리마인더 자동화 |
| [Projects 보드](https://github.com/users/korogoo/projects/8) | 발표 일정 (발표일 기준 캘린더 뷰 가능) |
