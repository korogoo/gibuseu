# 카테고리 정의

발표 등록은 New Issue에서 **대분류에 맞는 템플릿**을 고르면 됩니다 (예: DB 발표면 "발표 등록 - 데이터베이스").
템플릿을 고르는 것 자체가 대분류 선택이고, 그 안의 소분류는 드롭다운으로 나옵니다.
목록에 원하는 소분류가 없으면 "기타"를 고르고 "소분류 - 직접 입력" 칸에 적으면 됩니다.
카테고리를 바꾸고 싶으면 `scripts/generate_issue_templates.py`의 `CATEGORIES`를 수정하고 다시 실행하세요.

## 대분류 / 소분류

| 대분류 | 템플릿 | 소분류 |
|---|---|---|
| CS | `presentation-cs.yml` | 컴퓨터 구조, 운영체제, 네트워크, 자료구조 & 알고리즘, JVM & 언어 |
| 데이터베이스 | `presentation-db.yml` | 인덱스 & 쿼리 최적화, 트랜잭션 & 정합성, 락 & 동시성 |
| 인프라/DevOps | `presentation-infra.yml` | 배포 & 인프라, 모니터링 & 관측성, CI/CD |
| 아키텍처 | `presentation-arch.yml` | 캐시, 메시징 & 이벤트(Kafka, Outbox), MSA & 서비스 간 통신 |
| 보안 | `presentation-security.yml` | 인증 & 인가(JWT, OAuth), 암호화 & OWASP |
| 테스트/QA | `presentation-test.yml` | 테스트 전략(단위/통합/E2E), 테스트 더블 & TDD |
| AI | `presentation-ai.yml` | LLM 활용 / RAG, 추천 시스템 |

## 유형

- **이론 학습**: 다룰 개념과 어디까지 정리할지가 완료기준
- **트러블슈팅**: 어떤 문제였고 어떻게 해결했는지가 완료기준
