# KITA Trade AX Master

> **AI 기반 국제무역 자동화 플랫폼** - HS CODE 검색부터 Proforma Invoice 발행까지, 무역 실무의 모든 것을 자동화합니다.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com)

---

## 프로젝트 개요

**KITA Trade AX Master**는 무역 실무자를 위한 올인원 자동화 솔루션입니다.

기존 무역 업무에서 HS CODE 조회, 관세율 확인, 운임비 비교, 인코텀즈별 비용 산출, PI 작성까지 **각각 별도의 시스템**에서 수작업으로 진행해야 했던 과정을 **단일 플랫폼**에서 AI 기반으로 자동화했습니다.

### 핵심 가치
- **45개국 관세율 데이터베이스** 통합 (2025년 최신 공식 데이터)
- **OpenAI GPT-4o-mini** 기반 지능형 검색 및 자동 매칭
- **11개 인코텀즈(Incoterms 2020)** 비용 자동 계산
- **Proforma Invoice** 원클릭 생성 및 Excel 다운로드

---

## 주요 기능

### 1. AI 기반 HS CODE 검색 시스템
| 기능 | 설명 |
|------|------|
| **지능형 품목 검색** | 품목명 입력 시 AI가 최적의 HS CODE 후보 3~6개 자동 제시 |
| **다국어 지원** | 한글/영문 품목명 모두 인식 (예: "냉동딸기", "Frozen Strawberry") |
| **HS10/HS6 자동 매칭** | 10자리 상세코드 우선, 6자리 기본코드 폴백 처리 |

```
입력: "냉동딸기"
출력: HS Code 081110 (냉동 딸기) - AI 자동 매칭
```

### 2. 국가별 관세율 자동 조회
| 기능 | 설명 |
|------|------|
| **45개국 데이터베이스** | 미국, 중국, EU, 일본, 베트남 등 주요 수출입 대상국 완비 |
| **3단계 Fallback 로직** | 수동입력 → 파일매칭 → AI파싱 순차 처리로 정확도 극대화 |
| **MFN/특혜관세 구분** | 최혜국대우(MFN) 및 FTA 특혜관세율 자동 식별 |

**지원 국가 (45개국)**
```
아시아: 한국, 중국, 일본, 베트남, 인도, 태국, 인도네시아, 말레이시아, 싱가포르, 필리핀 등
유럽: EU, 영국, 스위스, 노르웨이, 튀르키예, 러시아 등
미주: 미국, 캐나다, 멕시코, 브라질, 칠레 등
오세아니아: 호주, 뉴질랜드
중동/아프리카: UAE, 사우디아라비아, 남아공, 이스라엘 등
```

### 3. 운임비 비교 분석
| 운송방식 | 기준 | 비용 체계 |
|----------|------|-----------|
| **해상(SEA)** | 컨테이너 | 20FT: $850 / 40FT: $1,050 (부산항 기준) |
| **항공(AIR)** | 중량(KG) | 300KG: $4.7/kg / 500KG: $4.3/kg (인천공항 기준) |

### 4. 인코텀즈별 비용 자동 계산 (Incoterms 2020)
| 그룹 | 조건 | 설명 |
|------|------|------|
| **E조건** | EXW | 공장인도 - 매수인 전 비용 부담 |
| **F조건** | FCA, FAS, FOB | 주운송비 미지급 |
| **C조건** | CFR, CIF, CPT, CIP | 주운송비 지급 |
| **D조건** | DAP, DPU, DDP | 도착지 인도 - 매도인 전 비용 부담 |

**비용 산출 항목**
- Goods Value (상품가액)
- Freight (운임)
- Insurance (보험료) - CIF × 0.3% 자동 계산
- CIF Value (운임보험료포함가격)
- Duty (관세)
- **Total Landing Cost (총 도착비용)**

### 5. Proforma Invoice 자동 생성
- **PI 번호 자동 부여**: PI-YYYYMMDDHHmm 형식
- **입력 항목**: Exporter/Buyer 정보, 품목 상세, 은행정보, 결제조건
- **출력 형식**: 전문적인 Excel 양식 (.xlsx)
- **즉시 다운로드**: 원클릭 파일 생성

---

## 기술 스택

### Backend & AI
| 기술 | 용도 |
|------|------|
| **Python 3.9+** | 메인 개발 언어 |
| **OpenAI GPT-4o-mini** | HS CODE 검색, 국가 인식, 관세 파싱 |
| **Pandas** | 데이터 처리, 결측치 정제, 타입 변환 |

### Frontend & Visualization
| 기술 | 용도 |
|------|------|
| **Streamlit** | 대화형 웹 대시보드 UI |
| **Metric Cards** | KPI 요약 시각화 |
| **DataFrames** | 비교표 및 상세 데이터 표시 |

### Data & Security
| 기술 | 용도 |
|------|------|
| **Excel/CSV/Parquet** | 45개국 관세율 데이터베이스 |
| **python-dotenv** | API Key 환경변수 보안 관리 |
| **openpyxl** | PI Excel 파일 생성 |

---

## 데이터 출처

| 데이터 | 출처 | 갱신주기 |
|--------|------|----------|
| **HS CODE 마스터** | 관세청 공식 HS부호 (2026.01.01) | 연 1회 |
| **국가별 관세율표** | 각국 정부 공식 문서 (2025년) | 연 1회 |
| **운임 참고자료** | KITA 한국무역협회 | 월 1회 |

### 데이터 구조
```
📁 프로젝트 루트/
├── 📁 hs/                          # HS CODE 마스터
│   └── 관세청_HS부호_20260101.xlsx
├── 📁 freight/                     # 운임 참고 데이터
│   ├── Kita 항공 참고운임 1월.csv
│   └── Kita 해상 참고운임 1월.csv
├── 📁 tariff_files/                # 45개국 관세율 DB
│   ├── 2025년_미국_관세율표.xlsx
│   ├── 2025년_중국_관세율표.xlsx
│   ├── 2025년_일본_관세율표.xlsx
│   ├── 2025년_EU_관세율표.xlsx
│   ├── ... (40개국 추가)
│   └── integrated_tariffs.parquet  # 통합 관세 DB
└── 📄 profoma.py                   # 메인 애플리케이션
```

---

## 설치 및 실행 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/kita-trade-ax-master.git
cd kita-trade-ax-master
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
# .env 파일 생성
echo "OPEN_API_KEY=your-openai-api-key" > .env
```

### 5. 애플리케이션 실행
```bash
streamlit run profoma.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 화면 구성 및 사용법

### Step 1: 기본 설정 (Sidebar)
1. **거래 유형 선택**: 수출 / 수입
2. **도착지 입력**: 도시명 또는 국가명 (예: Tokyo, 도쿄, 상하이)
   - AI가 자동으로 국가 인식
3. **상품 정보 입력**: 단가(USD), 수량, 중량(KG)
4. **HS CODE 검색**: 품목명 입력 → AI 후보 선택

### Step 2: 관세 및 운임 분석
1. AI가 도착지 국가에 맞는 관세파일 자동 선택
2. HS CODE 기반 관세율 자동 추출
3. 해상/항공 운임비 비교 분석

### Step 3: 인코텀즈별 비용 계산
1. **인코텀즈 그룹 선택**: E / F / C / D
2. **세부 조건 선택**: EXW, FOB, CIF, DDP 등
3. **비용 구성 확인**: Goods → Freight → Insurance → Duty → Total

### Step 4: Proforma Invoice 생성
1. Exporter/Buyer 정보 입력
2. 품목 상세 및 결제조건 설정
3. **Excel 다운로드** 버튼 클릭

---

## 핵심 지표 및 분석 로직

### 비용 산출 공식
```python
# CIF 가격 계산
CIF = Goods Value + Freight + Insurance

# 보험료 계산 (CIF의 0.3%)
Insurance = (Goods Value + Freight) × 0.003

# 관세 계산
Duty = CIF × Tariff Rate (%)

# 총 도착비용
Total Landing Cost = CIF + Duty
```

### 운송방식별 비용 비교
```
예시: 상품가 $50,000, 중량 500KG

[해상 - 20FT]
Freight: $850
Insurance: $152.55
Total: $50,000 + $850 + $152.55 = $51,002.55

[항공 - 500KG]
Freight: 500 × $4.3 = $2,150
Insurance: $156.45
Total: $50,000 + $2,150 + $156.45 = $52,306.45

→ 해상이 $1,303.90 절감
```

### 인코텀즈별 책임 범위
| 항목 | EXW | FOB | CIF | DDP |
|------|-----|-----|-----|-----|
| 상품가 | ✓ | ✓ | ✓ | ✓ |
| 내륙운송(출발) | - | ✓ | ✓ | ✓ |
| 수출통관 | - | ✓ | ✓ | ✓ |
| 주운송비 | - | - | ✓ | ✓ |
| 보험료 | - | - | ✓ | ✓ |
| 수입통관 | - | - | - | ✓ |
| 관세 | - | - | - | ✓ |

---

## 실무 활용 사례

### 1. 수출 견적서 작성
- 해외 바이어에게 인코텀즈별 가격 제시
- 운송방식(해상/항공) 비용 비교 제공
- 즉시 Proforma Invoice 발행

### 2. 수입 원가 계산
- 관세율 자동 조회로 정확한 원가 산출
- 인코텀즈 조건별 총 도착비용 비교
- 최적 조건 선택 의사결정 지원

### 3. FTA 활용 검토
- 국가별 MFN 관세율 vs FTA 특혜관세율 비교
- 원산지 증명 필요 여부 판단

### 4. 물류비 최적화
- 해상 vs 항공 운임 비교
- 중량/부피 기준 최적 운송방식 선택
- 리드타임 vs 비용 트레이드오프 분석

### 5. 신규 시장 진출 검토
- 45개국 관세율 즉시 조회
- 품목별 관세 부담 비교
- 경쟁력 있는 시장 선별

---

## 프로젝트 구조

```
📁 kita-trade-ax-master/
├── 📄 profoma.py              # 메인 Streamlit 애플리케이션 (1,800+ LOC)
│   ├── Part 1: 설정 & OpenAI 연동
│   ├── Part 2: Sidebar UI
│   ├── Part 3: HS/국가/관세 분석
│   ├── Part 4: 운송비/인코텀즈 계산
│   ├── Part 5: PI 생성
│   └── Part 6: 앱 라우터
│
├── 📄 requirements.txt        # Python 의존성 패키지
├── 📄 .env                    # API Key (gitignore)
├── 📄 .gitignore              # Git 제외 파일
├── 📄 README.md               # 프로젝트 문서
│
├── 📁 hs/                     # HS CODE 마스터 데이터
├── 📁 freight/                # 운임 참고 데이터
└── 📁 tariff_files/           # 45개국 관세율 DB
```

---

## 의존성 패키지

```txt
streamlit>=1.30.0
pandas>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
requests>=2.31.0
```

---

## 향후 개발 계획

- [ ] **환율 API 연동**: 실시간 USD ↔ KRW 자동 변환
- [ ] **관세 API 연동**: 외부 관세 데이터베이스 실시간 조회
- [ ] **지도 시각화**: 무역 루트 Folium 지도 표시
- [ ] **다중 품목 지원**: 여러 품목 일괄 계산
- [ ] **이력 관리**: 견적 이력 저장 및 조회

---

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.

---

## 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해 주세요.

---

<div align="center">

**무역 실무의 복잡한 계산, AI가 대신합니다.**

*KITA Trade AX Master - Your Intelligent Trade Partner*

</div>
