# agent-rag 프로젝트 검토 보고서

## 프로젝트 개요

Google ADK(Agent Development Kit) 기반의 RAG(Retrieval-Augmented Generation) 에이전트 프로젝트. 한국어 기술 보고서를 검색하고 답변하는 AI 에이전트를 FastAPI 서비스로 제공한다.

---

## 프로젝트 구조

```
rag_agent_A/
├── __init__.py              # 패키지 초기화 (root_agent 노출)
├── .env.sample              # 환경변수 샘플
├── README.md                # (빈 파일)
├── agent.py                 # 메인 에이전트 정의
├── prompt.yaml              # 프롬프트 설정 (빈 상태)
├── service.py               # FastAPI 서비스
├── constants/
│   ├── __init__.py          # 상수 re-export
│   └── constants.py         # 상수 정의
├── tools/
│   ├── __init__.py          # 도구 re-export
│   └── rag_search.py        # RAG 검색 도구
└── utils/
    ├── __init__.py           # 유틸리티 re-export
    ├── log_utils.py          # 세션별 로깅 유틸
    ├── prompt_utils.py       # YAML 프롬프트 로더
    └── retriever_utils.py    # 문서 검색 (BM25 + FAISS 앙상블)
```

---

## 파일별 상세 설명

### 1. `__init__.py` (루트)
- `agent.py`에서 `root_agent`를 import하여 패키지 외부에 노출

### 2. `.env.sample`
- `ROOT_AGENT_API_BASE`: vLLM 서버 API 엔드포인트 (IP/포트 플레이스홀더)
- `ROOT_AGENT_MODEL`: 호스팅된 모델 경로
- `OPENAI_API_KEY`: OpenAI API 키 플레이스홀더

### 3. `agent.py` - 메인 에이전트
- Google ADK `Agent` 클래스 사용, `LiteLlm` 모델 연동
- `before_agent_callback()`: 사용자 쿼리를 세션 로그에 기록
- `before_model_callback()`: LLM 요청 정보를 세션 로그에 기록
- `root_agent`: 에이전트 인스턴스 (이름: `root_agent_NoTune`)
  - 도구: `search_tech_reports`
  - prompt.yaml에서 프롬프트/글로벌 인스트럭션 로드

### 4. `prompt.yaml`
- `prompt`, `global_instruction` 키가 있으나 값이 비어 있음

### 5. `service.py` - FastAPI 서비스
- **세션 관리**: `DatabaseSessionService` (SQLite), IP 기반 사용자 식별
- **엔드포인트**:
  - `POST /chat`: 메시지 전송, 에이전트 실행, 응답 반환
  - `POST /session/new`: 새 세션 생성
  - `GET /sessions`: 사용자 세션 목록 조회
  - `GET /health`: 헬스체크
- **모델**: `ChatRequest`, `ChatResponse`, `SessionInfo` (Pydantic)
- IP→세션 매핑을 인메모리 dict로 관리

### 6. `constants/constants.py` - 설정 상수
- `APP_NAME`: "rag_agent"
- `TOP_K_RETRIEVAL`: 5 (검색 문서 수)
- `ENSEMBLE_WEIGHTS`: [0.5, 0.5] (BM25, FAISS 가중치)
- 파일 경로: 문서 JSON, 벡터DB, 임베딩 모델
- `IMAGE_PATH_OLD_PREFIX` / `IMAGE_PATH_NEW_PREFIX`: 이미지 경로 변환용
- `SESSION_DB_URL`: SQLite DB URL
- `RAG_LAST_SEARCH_QUERY` / `RAG_LAST_SEARCH_RESULTS`: 멀티턴 상태 키

### 7. `constants/__init__.py` - 상수 re-export
- `constants.py`에서 정의한 상수들을 re-export

### 8. `tools/rag_search.py` - RAG 검색 도구
- `_save_image_artifacts()`: 검색 결과의 이미지를 아티팩트로 저장 (보고서ID_이미지명 형식)
- `search_tech_reports()`: 메인 검색 함수
  - 문서 검색 → 세션 상태 저장 → 이미지 아티팩트 저장 → 구조화된 결과 반환
  - 에러 핸들링 포함

### 9. `utils/log_utils.py` - 로깅 유틸리티
- `get_user_session_logger()`: 사용자/세션별 전용 로거 생성
- 로그 저장 경로: `./artifacts/rag_agent/{user_id}/{session_id}/`
- 싱글턴 패턴 (핸들러 중복 방지)

### 10. `utils/prompt_utils.py` - 프롬프트 로더
- `get_prompt_yaml()`: YAML 파일에서 프롬프트 로드
- `inspect.stack()`으로 호출자 디렉토리 기준 경로 해석
- 점(.) 표기법으로 중첩 키 접근 지원

### 11. `utils/retriever_utils.py` - 문서 검색 엔진
- 한국어 형태소 분석기 (KonLPy Okt) 사용
- **BM25 Sparse Retriever** + **FAISS Dense Retriever** 앙상블
- `preprocess_func_okt()`: 한국어 텍스트 토큰화
- `fix_image_paths()`: 이미지 경로 prefix 변환
- `retrieve_documents()`: 앙상블 검색 실행, 경로 변환, 구조화된 결과 반환
- 모듈 로드 시 문서/벡터스토어 초기화 (GPU 비활성화: `CUDA_VISIBLE_DEVICES=-1`)

---

## 발견된 오타 및 버그

### 버그 (런타임 에러 발생)

| # | 파일 | 라인 | 문제 | 수정안 | 상태 |
|---|------|------|------|--------|------|
| 1 | `constants/__init__.py` | 8 | `IMAEG_PATH_OLD_PREFIX` (오타) | `IMAGE_PATH_OLD_PREFIX` | 수정 완료 |
| 2 | `constants/__init__.py` | 9 | `IMAEG_PATH_NEW_PREFIX` (오타) | `IMAGE_PATH_NEW_PREFIX` | 수정 완료 |
| 3 | `tools/rag_search.py` | 9 | `retriever_documents` - 함수명 불일치. 실제 함수명은 `retrieve_documents` | `retrieve_documents`로 변경 | 수정 완료 |

- **1, 2번**: `constants.py`에서는 `IMAGE_PATH_*`로 정의했는데 `__init__.py`에서 `IMAEG_PATH_*`로 import하여 **ImportError** 발생
- **3번**: `retriever_utils.py`에서 함수명이 `retrieve_documents`인데 `rag_search.py`에서 `retriever_documents`로 import하여 **ImportError** 발생

### 오타 (비치명적)

| # | 파일 | 라인 | 문제 | 수정안 | 상태 |
|---|------|------|------|--------|------|
| 4 | `utils/retriever_utils.py` | 56 | `"Dense (FAISS) retriever initialization"` - 48번 라인의 `"initialized"` 패턴과 불일치 | `"Dense (FAISS) retriever initialized"` | 수정 완료 |

### 기타 주의사항

| # | 파일 | 라인 | 내용 |
|---|------|------|------|
| 5 | `utils/log_utils.py` | 15 | `logging.debug(...)` - 모듈 레벨 루트 로거 사용. 의도적일 수 있으나 비일관적 |
| 6 | `README.md` | - | 파일이 비어 있음 |
| 7 | `prompt.yaml` | - | prompt, global_instruction 값이 비어 있음 |

---

## 수정 완료 파일 요약

1. **`constants/__init__.py`** (라인 8-9): `IMAEG` → `IMAGE` 오타 수정
2. **`tools/rag_search.py`** (라인 9, 50): `retriever_documents` → `retrieve_documents` 함수명 수정
3. **`utils/retriever_utils.py`** (라인 56): 로그 메시지 `"initialization"` → `"initialized"` 통일

---

## 검증 방법

1. 오타 수정 후 `python -c "from rag_agent_A import root_agent"` 실행하여 ImportError 없는지 확인
2. 전체 서비스 실행: `uvicorn rag_agent_A.service:app` 후 `/health` 엔드포인트 호출
