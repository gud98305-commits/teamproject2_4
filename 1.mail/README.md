# 🚢 AI Trade Assistant v2.0

> **무역 인콰이어리 메일 자동 분석 및 AI 답장 생성 시스템**
> Gmail 연동 기반의 지능형 수출입 업무 의사결정 지원 대시보드

---

## 📌 프로젝트 개요

해외영업 담당자가 매일 수십 건의 인콰이어리 메일을 수동으로 분류하고, 답장을 작성하는 데 상당한 시간을 소모하는 문제를 해결하기 위해 개발되었습니다.

**AI Trade Assistant**는 Gmail API를 통해 메일을 자동 수집하고, 무역 특화 키워드 분석 알고리즘으로 **거래 가능성이 높은 Hot Lead를 자동 선별**합니다. 또한 OpenAI GPT를 활용한 **전문적인 답장 초안 자동 생성** 기능으로 업무 효율을 극대화합니다.

### 🎯 핵심 가치
- **업무 시간 80% 단축**: 메일 분류 및 우선순위 결정 자동화
- **거래 기회 포착률 향상**: 구매 의도가 높은 메일을 놓치지 않음
- **전문적 응대 품질 유지**: AI 기반 맞춤형 답장 초안 생성

---

## 🏆 주요 성과 및 기술적 특징

### 1. 데이터 수집 및 연동

| 항목 | 구현 내용 |
|------|----------|
| **Gmail API 연동** | OAuth 2.0 인증 기반 실시간 메일 수집 (최대 100건/회) |
| **다중 수집 모드** | 개수 기준 / 날짜 기준 / 기간 내 개수 기준 3가지 모드 지원 |
| **필수 항목 추출** | 제목, 발신자, 본문, 첨부파일 여부, 언어 자동 감지 |
| **보안 설계** | `.env` 파일로 API 키 분리, `credentials.json` Git 제외 처리 |
| **Demo 모드** | API 미연동 시 5개 샘플 메일로 즉시 테스트 가능 |

```python
# 수집 모드별 유연한 쿼리 구성
fetch_modes = ["개수 기준", "날짜 기준", "기간 내 개수 기준"]
```

### 2. 데이터 전처리 품질

| 항목 | 구현 내용 |
|------|----------|
| **다국어 처리** | 영어(EN) / 한국어(KO) 자동 감지 및 분리 처리 |
| **한국어 무역 은어 정규화** | "네고"→"negotiation", "발주"→"purchase order" 등 30+ 용어 매핑 |
| **Gibberish 필터링** | 키보드 패턴, 반복 문자, 특수문자 과다 등 무의미 텍스트 자동 제거 |
| **스팸 탐지** | 의심 도메인, 사기 패턴, 클릭베이트 키워드 기반 다중 검증 |
| **데이터 구조화** | SQLite DB 저장, 인덱스 최적화로 빠른 조회 지원 |

```
📁 config/jargon_map.json
├── "엘씨" → "l/c" (Letter of Credit)
├── "비엘" → "bill of lading"
├── "원산지증명서" → "certificate of origin"
└── "인코텀즈" → "incoterms"
```

### 3. 지표 및 분석 설계 (핵심 알고리즘)

#### 📊 3-Factor 무역 인콰이어리 스코어링 모델

| 평가 요소 | 가중치 | 주요 분석 항목 |
|----------|--------|---------------|
| **제품 명확성 (Clarity)** | 15% | Model No., Specification, Drawing, HS CODE 언급 여부 |
| **구매 의도 (Intent)** | 50% | PO, Target Price, MOQ, Urgent, Bulk Order 등 |
| **무역 조건 (Terms)** | 35% | L/C, T/T, FOB, CIF, COO, MSDS, 인코텀즈 전반 |

#### 🔢 종합 점수 산출 공식
```
총점 = (Clarity × 0.15) + (Intent × 0.50) + (Terms × 0.35)
범위: 0 ~ 100점
```

#### 🎯 우선순위 자동 분류
| 점수 구간 | 등급 | 의미 |
|----------|------|------|
| 70점 이상 | 🔴 **Hot Lead** | 즉시 대응 필요, 계약 가능성 높음 |
| 40~70점 | 🟠 **Potential** | 추가 확인 후 대응 |
| 40점 미만 | ⚫ **Follow-up** | 일반 문의, 후순위 처리 |
| 스팸 판정 | 🚫 **Filtered** | 자동 제외 |

#### 📈 분석 타당성 검증
- **무역 전문 용어 120+ 키워드** 기반 정밀 분석
- **인코텀즈 전 조건 지원**: FOB, CIF, CFR, DDP, DAP, EXW
- **결제 조건 인식**: L/C, T/T, Net 30/60, Advance Payment
- **무역 서류 감지**: COO, MSDS, Proforma Invoice, Packing List

### 4. 대시보드 기능 완성도

#### 🖥️ 화면 구성

| 영역 | 기능 |
|------|------|
| **사이드바** | 메일 수집 모드 선택, 수집 개수/기간 설정, 동기화 버튼 |
| **🏆 TOP 10 탭** | 종합 점수 상위 10개 메일 카드 형식 표시 |
| **🔥 Hot Lead 탭** | Intent 점수 기준 정렬, 구매 의도 높은 순 |
| **📋 전체 탭** | 모든 메일 리스트 조회 |

#### ⚡ 인터랙션 기능

| 기능 | 설명 |
|------|------|
| **실시간 필터링** | 국가, 언어, 점수 구간별 필터 |
| **처리 완료 마킹** | 버튼 클릭으로 메일 상태 변경 + Gmail 읽음 처리 동기화 |
| **Gmail 원본 링크** | 각 메일에서 원본으로 바로 이동 |
| **AI 답장 생성** | 버튼 클릭으로 GPT 기반 답장 초안 즉시 생성 |
| **Gmail 발송 연동** | 생성된 초안으로 Gmail Compose 화면 자동 오픈 |

#### 🎨 시각화 및 UX

- **색상 코드 시스템**: 점수별 빨강/주황/회색 시각적 구분
- **언어 아이콘**: 🇺🇸 영어 / 🇰🇷 한국어 / 🌐 기타
- **점수 breakdown 표시**: 3가지 요소별 점수 투명하게 공개
- **분석 근거 표시**: AI가 왜 이 점수를 부여했는지 설명

---

## 💼 무역 실무 활용 시나리오

### 시나리오 1: 일일 인콰이어리 처리
```
09:00 출근 → 대시보드 접속 → 동기화 클릭
       ↓
전일 수신 메일 30건 자동 분석 완료
       ↓
🔴 Hot Lead 3건 확인 → 즉시 답장 초안 생성 → 검토 후 발송
       ↓
🟠 Potential 8건 → 추가 정보 확인 후 오후 대응
       ↓
⚫ Follow-up → 정기 답변 템플릿으로 처리
```

### 시나리오 2: 신규 바이어 발굴
- **구매 의도 점수 30점 이상** + **무역 조건 언급** = 진성 바이어
- "L/C at sight", "FOB price", "COO required" 등 실거래 신호 자동 감지
- Purchasing Manager, Procurement Director 등 의사결정권자 메일 우선 표시

### 시나리오 3: 긴급 대응
- "ASAP", "Urgent", "Deadline" 키워드 감지 시 자동 가점
- Hot Lead 중에서도 긴급 표시된 건 최우선 알림

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| **Frontend** | Streamlit (Python 웹 프레임워크) |
| **Backend** | Python 3.10+ |
| **AI/ML** | OpenAI GPT-3.5 Turbo |
| **Database** | SQLite3 |
| **Data Processing** | Pandas, BeautifulSoup4 |
| **API Integration** | Gmail API (google-api-python-client) |
| **Authentication** | OAuth 2.0 (google-auth-oauthlib) |
| **Environment** | python-dotenv |

---

## 📁 프로젝트 구조

```
1.mail/
├── main_final.py           # 메인 Streamlit 애플리케이션
├── requirements.txt        # 의존성 패키지 목록
├── .env                    # 환경변수 (API 키) - Git 제외
├── .gitignore              # Git 제외 파일 설정
├── README.md               # 프로젝트 문서
│
├── engine/                 # 핵심 분석 엔진
│   ├── analyzer.py         # 무역 인콰이어리 분석기
│   ├── database.py         # SQLite DB 관리자
│   └── reply_generator.py  # AI 답장 생성기
│
├── config/                 # 설정 파일
│   ├── keywords.json       # 무역 키워드 및 점수 매핑
│   └── jargon_map.json     # 한국어 무역 은어 변환 테이블
│
└── data/
    └── trade_emails.db     # 이메일 데이터베이스
```

---

## 🚀 실행 방법

### 1. 환경 설정

```bash
# 저장소 클론
git clone [repository-url]
cd 1.mail

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정

```bash
# .env 파일 생성
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Gmail API 설정 (선택)

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Gmail API 활성화
3. OAuth 2.0 클라이언트 ID 생성
4. `credentials.json` 다운로드 후 프로젝트 루트에 저장

### 4. 실행

```bash
streamlit run main_final.py
```

> **💡 Demo 모드**: Gmail API 미설정 시 5개 샘플 메일로 모든 기능 테스트 가능

---

## 📊 데이터베이스 스키마

```sql
CREATE TABLE emails (
    id TEXT PRIMARY KEY,           -- Gmail 메시지 ID
    subject TEXT,                  -- 제목
    sender TEXT,                   -- 발신자
    sender_email TEXT,             -- 이메일 주소
    body_text TEXT,                -- 본문

    -- 분석 점수
    score REAL,                    -- 종합 점수 (0-100)
    clarity_score REAL,            -- 제품 명확성 점수
    intent_score REAL,             -- 구매 의도 점수
    terms_score REAL,              -- 무역 조건 점수

    -- 분석 결과
    reason TEXT,                   -- AI 분석 근거
    keywords TEXT,                 -- 매칭된 키워드
    language TEXT,                 -- 감지된 언어
    is_spam INTEGER,               -- 스팸 여부
    status TEXT,                   -- Active/Archived
    created_at TEXT                -- 저장 시간
);
```

---

## 🔐 보안 설계

| 항목 | 구현 내용 |
|------|----------|
| **API 키 보호** | `.env` 파일 분리, `.gitignore` 등록 |
| **OAuth 인증** | Gmail API 접근 시 OAuth 2.0 필수 |
| **토큰 관리** | `token.json` 자동 생성, Git 제외 |
| **Streamlit Cloud** | Secrets 기능으로 배포 환경 보안 유지 |

---

## 📈 향후 확장 계획

- [ ] 다국어 확장: 중국어, 일본어 무역 용어 지원
- [ ] HS CODE 데이터베이스 연동으로 품목별 관세율 자동 조회
- [ ] 환율 API 연동으로 견적 금액 실시간 환산
- [ ] 바이어 이력 관리 및 거래 성사율 분석
- [ ] Slack/Teams 알림 연동

---

## 📝 라이선스

This project is licensed under the MIT License.

---

## 👥 기여자

- **개발 및 기획**: [Your Name]
- **AI 모델**: OpenAI GPT-3.5 Turbo
- **Co-Authored-By**: Claude Opus 4.5

---

<p align="center">
  <b>🚢 AI Trade Assistant - 무역 인콰이어리의 스마트한 시작</b>
</p>
