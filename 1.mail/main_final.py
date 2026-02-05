"""
================================================================================
AI Trade Assistant v2.0 - Intelligence Decision Support System
================================================================================
무역 인콰이어리 메일 AI 분석 + 답장 초안 자동 생성 시스템

[핵심 기능]
1. Gmail API 연동 메일 수집
2. AI 기반 스코어링 (Intent 50% + Terms 35% + Clarity 15%)
3. 스팸/Gibberish 자동 필터링
4. AI 답장 초안 자동 생성 (영어→영어, 한국어→한국어)
5. 비동기 처리 지원

[답장 초안 기능]
- 답장하기 버튼 클릭 시 AI가 초안 자동 생성
- 수정 가능한 텍스트 영역 제공
- 수정 후 mailto 링크로 메일 앱 연동
================================================================================
"""

import os
import re
import urllib.parse
import logging
import asyncio
import json
from datetime import datetime, timedelta
import streamlit as st

# ==============================================================================
# [핵심 수정] Streamlit secrets → 인증 파일 복원
# ==============================================================================
# TOML에서 credentials.json = """...""" 은 st.secrets["credentials"]["json"]으로 파싱됨
# token.json = """...""" 은 st.secrets["token"]["json"]으로 파싱됨
#
# Streamlit Cloud Secrets 입력 형식:
#   credentials.json = """{"installed":{...}}"""
#   token.json = """{"token":"...","refresh_token":"..."}"""

def _restore_from_secrets(toml_table, toml_key, filename):
    """st.secrets에서 인증 파일을 복원합니다."""
    try:
        # TOML 점(.) 구분자로 인해 테이블.키 구조로 파싱됨
        if toml_table in st.secrets and toml_key in st.secrets[toml_table]:
            content = st.secrets[toml_table][toml_key]
            json.loads(content)  # JSON 검증
            with open(filename, "w") as f:
                f.write(content)
            logging.info(f"{filename} 복원 완료 (from secrets)")
            return True
    except json.JSONDecodeError as e:
        st.error(f"secrets '{toml_table}.{toml_key}' JSON 형식 오류: {e}")
    except Exception as e:
        logging.error(f"secrets '{toml_table}.{toml_key}' 로드 실패: {e}")
    return False

# credentials.json 복원: secrets의 credentials.json → ["credentials"]["json"]
if not os.path.exists("credentials.json"):
    _restore_from_secrets("credentials", "json", "credentials.json")

# token.json 복원: secrets의 token.json → ["token"]["json"]
if not os.path.exists("token.json"):
    if not _restore_from_secrets("token", "json", "token.json"):
        logging.warning("token.json이 없습니다. 로컬에서 먼저 OAuth 인증을 완료한 후 "
                         "token.json 내용을 Streamlit secrets에 추가하세요.")

# 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 로컬 엔진 모듈
from engine.analyzer import InquiryAnalyzer
from engine.database import DBManager
from engine.reply_generator import ReplyGenerator

# Gmail API (optional)
try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

# 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("TradeAssistant")


# ==============================================================================
# Gmail API Functions
# ==============================================================================
def get_gmail_service():
    """Gmail API 서비스 생성"""
    if not GMAIL_AVAILABLE:
        return None
    
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            logger.error(f"Token load error: {e}")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                st.error(f"⚠️ Gmail 토큰 갱신 실패: {e}")
                return None
        else:
            if not os.path.exists('credentials.json'):
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def mark_as_read(service, msg_id):
    """Gmail 읽음 처리"""
    if service:
        try:
            service.users().messages().modify(
                userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Mark as read failed: {e}")
    return False


def fetch_emails_from_gmail(service, max_results=50, date_range=None, mode="개수 기준"):
    """Gmail에서 메일 수집"""
    if not service:
        return []
    
    query = "is:unread"
    
    if mode != "개수 기준" and date_range and len(date_range) == 2:
        start_date, end_date = date_range
        q_after = start_date.strftime('%Y/%m/%d')
        q_before = (end_date + timedelta(days=1)).strftime('%Y/%m/%d')
        query += f" after:{q_after} before:{q_before}"
    
    fetch_limit = 500 if mode == "날짜 기준" else max_results
    
    try:
        results = service.users().messages().list(
            userId='me', maxResults=fetch_limit, q=query
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            m = service.users().messages().get(userId='me', id=msg['id']).execute()
            
            date_raw = int(m['internalDate']) / 1000
            dt_obj = datetime.fromtimestamp(date_raw)
            
            headers = m['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            
            email_match = re.search(r'<(.+?)>', sender)
            sender_email = email_match.group(1) if email_match else sender
            
            emails.append({
                'id': msg['id'],
                'subject': subject,
                'sender': sender,
                'sender_email': sender_email,
                'body': m.get('snippet', ''),
                'snippet': m.get('snippet', ''),
                'has_attachment': 'parts' in m['payload'],
                'mail_date': dt_obj.strftime('%m-%d %H:%M'),
                'full_date': dt_obj.strftime('%Y-%m-%d')
            })
        
        return emails
        
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        st.error(f"❌ 메일 수집 중 오류 발생: {e}")
        return []


def get_demo_emails():
    """데모용 샘플 메일"""
    return [
        {
            'id': 'demo_001',
            'subject': 'URGENT: Purchase Order for LED Bulbs - FOB Shenzhen',
            'sender': 'John Smith <john@globaltrading.com>',
            'sender_email': 'john@globaltrading.com',
            'body': '''Dear Sir,

We are interested in purchasing LED bulbs for our retail network.

Product: LED Bulb E27
Model No: LED-12W-6500K  
Quantity: 50,000 pcs
Target Price: USD 1.20/pc FOB Shenzhen
Delivery: ASAP, within 3 weeks

We are a major distributor with 200+ retail stores.
Please send your best quotation and proforma invoice.

Payment terms: T/T 30% advance, 70% before shipment.

Best regards,
John Smith
Procurement Director''',
            'snippet': 'We are interested in purchasing LED bulbs...',
            'has_attachment': True,
            'mail_date': '02-03 10:30',
            'full_date': '2026-02-03',
            'language': 'EN'
        },
        {
            'id': 'demo_002',
            'subject': '견적 요청 - 전자부품 긴급 발주',
            'sender': '김철수 <chulsoo@koreatrade.co.kr>',
            'sender_email': 'chulsoo@koreatrade.co.kr',
            'body': '''안녕하세요,

긴급하게 발주 관련 문의드립니다.

품목: IC 칩셋
모델번호: IC-7805
수량: 100,000개
단가: 네고 가능
납기: 2주 이내

저희는 국내 대형 유통사이며, 정기 발주를 검토 중입니다.
견적서와 MOQ 정보 부탁드립니다.

결제조건: 인코텀즈 CIF 부산, T/T 30일

감사합니다.
김철수 드림
구매팀장''',
            'snippet': '긴급하게 발주 관련 문의드립니다...',
            'has_attachment': False,
            'mail_date': '02-03 09:15',
            'full_date': '2026-02-03',
            'language': 'KO'
        },
        {
            'id': 'demo_003',
            'subject': 'RE: L/C Amendment - Container MSKU1234567',
            'sender': 'Sarah Lee <sarah@importers.eu>',
            'sender_email': 'sarah@importers.eu',
            'body': '''Dear Supplier,

Following our previous discussion, please find the amended L/C details:

L/C Number: LC2024-0123
Amount: EUR 85,000
Port of Discharge: Hamburg
Incoterms: CIF Hamburg

We need the Certificate of Origin and MSDS documents.
Please confirm you can meet the deadline.

Best regards,
Sarah Lee
Import Manager''',
            'snippet': 'Following our previous discussion...',
            'has_attachment': True,
            'mail_date': '02-02 16:45',
            'full_date': '2026-02-02',
            'language': 'EN'
        },
        {
            'id': 'demo_004',
            'subject': 'Product Inquiry - General',
            'sender': 'info@company.com',
            'sender_email': 'info@company.com',
            'body': '''Hello,

I am looking for some products. Can you send me your catalog?

Thanks''',
            'snippet': 'I am looking for some products...',
            'has_attachment': False,
            'mail_date': '02-02 08:00',
            'full_date': '2026-02-02',
            'language': 'EN'
        },
        {
            'id': 'demo_005',
            'subject': 'CONGRATULATIONS!!! YOU WON $1,000,000!!!',
            'sender': 'winner@lottery.xyz',
            'sender_email': 'winner@lottery.xyz',
            'body': '''CONGRATULATIONS!!! You have WON $1,000,000!!! Click here NOW!!!''',
            'snippet': 'You have WON $1,000,000...',
            'has_attachment': False,
            'mail_date': '02-01 07:30',
            'full_date': '2026-02-01',
            'language': 'EN'
        }
    ]


# ==============================================================================
# Streamlit UI
# ==============================================================================
def main():
    st.set_page_config(
        page_title="AI Trade Assistant",
        page_icon="🚀",
        layout="wide"
    )
    
    # CSS 스타일
    st.markdown("""
    <style>
        .main-header {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(90deg, #3b82f6, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .score-box {
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            color: white;
            display: inline-block;
        }
        .bg-high { background-color: #ef4444; }
        .bg-medium { background-color: #f59e0b; }
        .bg-low { background-color: #6b7280; }
        .reply-draft-box {
            background-color: #f0fdf4;
            border-left: 4px solid #22c55e;
            padding: 15px;
            margin: 10px 0;
        }
        .gmail-btn {
            background-color: #f1f3f4;
            color: #3c4043;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dadce0;
            font-weight: bold;
            display: block;
            text-decoration: none;
            margin: 10px 0;
        }
        .gmail-btn:hover { background-color: #e8eaed; }
        
        /* ✨ 새로운 스타일: 점수 강조 */
        .rank-score {
            color: #ef4444;
            font-weight: bold;
        }
        
        /* ✨ 새로운 스타일: 날짜 강조 */
        .rank-date {
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header"> 🚀 메일 자동화 시스템</h1>', unsafe_allow_html=True)
    st.caption("무역 인콰이어리 분석 + AI 답장 초안 자동 생성")
    
    # 서비스 초기화
    db = DBManager("data/trade_emails.db")
    analyzer = InquiryAnalyzer(
        openai_api_key=OPENAI_API_KEY,
        keywords_path="config/keywords.json",
        jargon_path="config/jargon_map.json"
    )
    reply_generator = ReplyGenerator(api_key=OPENAI_API_KEY)
    
    # Session State 초기화
    if 'reply_drafts' not in st.session_state:
        st.session_state.reply_drafts = {}
    if 'show_reply_modal' not in st.session_state:
        st.session_state.show_reply_modal = None
    
    # 사이드바
    with st.sidebar:
        # 수집 모드
        st.markdown("### 📬 메일 수집")
        collect_mode = st.selectbox(
            "수집 모드",
            ["개수 기준", "날짜 기준", "기간 내 개수 기준"]
        )
        
        analysis_limit = st.slider("분석할 메일 수", 10, 100, 30)
        
        if collect_mode != "개수 기준":
            selected_period = st.date_input(
                "기간 선택",
                value=(datetime.now().date() - timedelta(days=7), datetime.now().date()),
                format="YYYY-MM-DD"
            )
        else:
            selected_period = None
        
        # 동기화 버튼
        if st.button("🔄 데이터 동기화 및 AI 분석", use_container_width=True):
            # 기존 데이터 자동 초기화 (이전 메일이 남아있는 문제 방지)
            db.clear_all()
            st.session_state.reply_drafts = {}

            with st.spinner("메일 수집 및 분석 중..."):
                if not GMAIL_AVAILABLE:
                    st.warning("⚠️ Gmail API 라이브러리가 설치되지 않아 데모 데이터를 표시합니다.")
                    emails = get_demo_emails()
                else:
                    service = get_gmail_service()
                    if service:
                        emails = fetch_emails_from_gmail(service, analysis_limit, selected_period, collect_mode)
                        if not emails:
                            st.warning("⚠️ 조건에 맞는 읽지 않은 메일이 없습니다.")
                    else:
                        st.error("❌ Gmail 연결 실패 - 데모 데이터를 표시합니다. 토큰을 확인해주세요.")
                        emails = get_demo_emails()
                
                if emails:
                    progress = st.progress(0)
                    status = st.empty()
                    
                    for i, email in enumerate(emails):
                        if not db.email_exists(email['id']):
                            status.text(f"분석 중: {i+1}/{len(emails)}")
                            result = analyzer.calculate_score(email)
                            
                            db.insert_email_full({
                                **email,
                                'score': result['total'],
                                'clarity_score': result['clarity'],
                                'intent_score': result['intent'],
                                'terms_score': result['terms'],
                                'reason': result['reason'],
                                'keywords': result['keywords'],
                                'language': result['language'],
                                'is_spam': result['is_spam'],
                                'status': 'Active'
                            })
                        
                        progress.progress((i + 1) / len(emails))
                    
                    progress.empty()
                    status.empty()
                    st.success(f"✅ {len(emails)}개 메일 분석 완료!")
                    st.rerun()
        
        st.divider()
        
        # ✨ 통계 수정: "활성 메일" 제거, "스팸"과 "긴급(70+)"만 표시
        stats = db.get_statistics()
        st.markdown("### 📊 현황")
        col1, col2 = st.columns(2)
        col1.metric("스팸", f"{stats['spam']}건")
        col2.metric("긴급(70+)", f"{stats['high_priority']}건")
        
        st.divider()
        
        if st.button("🗑️ 전체 초기화", use_container_width=True):
            db.clear_all()
            st.session_state.reply_drafts = {}
            st.rerun()
    
    # 메인 영역
    all_emails = db.get_active_emails(sort_by="score", limit=100)
    
    # ✨ 탭 텍스트 수정: "🔥 Hot Lead" → "🔥 Hot Lead 순"
    tab1, tab2, tab3 = st.tabs(["🏆 종합 TOP 10", "🔥 Hot Lead 순", "📋 전체"])
    
    with tab1:
        if not all_emails:
            st.info("📬 '데이터 동기화 및 AI 분석' 버튼을 클릭하여 시작하세요.")
        else:
            top_emails = sorted(all_emails, key=lambda x: x['score'], reverse=True)[:10]
            for idx, mail in enumerate(top_emails):
                render_email_card(mail, idx + 1, db, reply_generator)
    
    with tab2:
        if all_emails:
            hot_leads = sorted(all_emails, key=lambda x: x['intent_score'], reverse=True)[:20]
            for mail in hot_leads:
                score = int(mail['intent_score'])
                cls = "bg-high" if score >= 70 else "bg-medium" if score >= 40 else "bg-low"
                
                col1, col2 = st.columns([0.88, 0.12])
                with col1:
                    st.markdown(f"""
                    🎯 <span class="score-box {cls}">{score}점</span>
                    **{mail['subject'][:50]}** ({mail['mail_date']})
                    """, unsafe_allow_html=True)
                with col2:
                    gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{mail['id']}"
                    st.link_button("🌐", gmail_url)
    
    with tab3:
        if all_emails:
            for mail in all_emails:
                st.write(f"[{int(mail['score'])}점] {mail['subject'][:60]} ({mail['mail_date']})")


def render_email_card(mail: dict, rank: int, db: DBManager, reply_gen: ReplyGenerator):
    """이메일 카드 렌더링 (답장 초안 기능 포함)"""
    score = mail['score']
    cls = "bg-high" if score >= 70 else "bg-medium" if score >= 40 else "bg-low"
    
    # ✨ 카드 라벨 수정: 점수를 빨간색 볼드체로, 날짜를 볼드체로
    card_label = f"**Rank {rank}:** <span class='rank-score'>[{int(score)}점]</span> {mail['subject'][:50]}... <span class='rank-date'>({mail['mail_date']})</span>"
    
    # ⚠️ st.expander는 HTML을 지원하지 않으므로, 순수 텍스트로 변경
    card_label_text = f"Rank {rank}: [{int(score)}점] {mail['subject'][:50]}... ({mail['mail_date']})"
    
    with st.expander(card_label_text, expanded=False):
        # ✨ 확장 시 내부에서 점수와 날짜 강조 스타일 적용
        st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <strong>Rank {rank}:</strong> 
            <span style="color: #ef4444; font-weight: bold;">[{int(score)}점]</span> 
            {mail['subject'][:50]}... 
            <strong>({mail['mail_date']})</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # 점수 표시
        has_attach = mail.get('has_attachment') == 1 or mail.get('has_attachment') is True
        attach_badge = "📎 첨부파일 포함" if has_attach else ""
        
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:15px; margin-bottom:15px;">
            <span class="score-box {cls}">종합 {score:.0f}점</span>
            <span>{attach_badge}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 세부 점수
        c1, c2, c3 = st.columns(3)
        c1.metric("제품 명확성 (15%)", f"{mail['clarity_score']:.0f}점")
        c2.metric("구매 의도 (50%)", f"{mail['intent_score']:.0f}점")
        c3.metric("무역 조건 (35%)", f"{mail['terms_score']:.0f}점")
        
        # 언어 표시
        lang_map = {'EN': '🇺🇸 영어', 'KO': '🇰🇷 한국어', 'OTHER': '🌐 기타'}
        st.caption(f"언어: {lang_map.get(mail.get('language', 'EN'), '🌐')}")
        
        st.divider()
        
        # AI 분석
        st.info(f"💡 **AI 분석 근거:** {mail['reason']}")
        
        if mail['keywords']:
            st.success(f"🔑 **판단 키워드:** {mail['keywords']}")
        
        # Gmail 링크
        gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{mail['id']}"
        st.markdown(f'<a href="{gmail_url}" target="_blank" class="gmail-btn">🔗 Gmail 원본 메일 확인하기</a>', unsafe_allow_html=True)
        
        st.divider()
        
        # 액션 버튼
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 처리 완료", key=f"done_{mail['id']}", use_container_width=True):
                db.update_status(mail['id'], 'Archived')
                if not mail['id'].startswith('demo_'):
                    service = get_gmail_service()
                    if service:
                        mark_as_read(service, mail['id'])
                st.toast("보관함으로 이동되었습니다.")
                st.rerun()
        
        with col2:
            if st.button("📧 답장하기", key=f"reply_{mail['id']}", use_container_width=True):
                # AI 답장 초안 생성
                with st.spinner("AI가 답장 초안을 작성 중..."):
                    draft = reply_gen.generate_reply(mail)
                    st.session_state.reply_drafts[mail['id']] = draft.body
                st.rerun()
        
        # 답장 초안 영역 (생성된 경우에만 표시)
        if mail['id'] in st.session_state.reply_drafts:
            st.markdown("---")
            st.markdown("""
            <div class="reply-draft-box">
                <strong>📝 AI 수출 전문가 답장 초안 (수정 및 발송)</strong><br>
                <small>내용을 검토하신 뒤 '단가, 납기, 담당자 성함' 등을 수정하여 파트너사에게 발송하세요.</small>
            </div>
            """, unsafe_allow_html=True)
            
            # 수정 가능한 텍스트 영역
            edited_reply = st.text_area(
                "답장 내용 (수정 가능)",
                value=st.session_state.reply_drafts[mail['id']],
                height=250,
                key=f"edit_{mail['id']}"
            )
            
            # 수정된 내용 저장
            st.session_state.reply_drafts[mail['id']] = edited_reply
            
            # 발송 버튼
            col_send1, col_send2, col_send3 = st.columns([1, 1, 1])
            
            with col_send1:
                # Gmail 작성 링크 생성 (수정된 내용 반영)
                sender_email = mail.get('sender_email', '') or mail['sender'].split('<')[-1].replace('>', '')
                reply_subject = f"Re: {mail['subject']}"
                
                # URL 인코딩
                encoded_to = urllib.parse.quote(sender_email)
                encoded_subject = urllib.parse.quote(reply_subject)
                encoded_body = urllib.parse.quote(edited_reply)
                
                # Gmail 작성 URL (웹)
                gmail_compose_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={encoded_to}&su={encoded_subject}&body={encoded_body}"
                
                st.markdown(f'''
                <a href="{gmail_compose_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#ea4335;color:white;padding:12px;
                    border-radius:8px;text-align:center;font-weight:bold;">
                        📤 Gmail에서 발송하기
                    </div>
                </a>
                ''', unsafe_allow_html=True)
            
            with col_send2:
                if st.button("🔄 초안 재생성", key=f"regen_{mail['id']}", use_container_width=True):
                    with st.spinner("초안 재생성 중..."):
                        draft = reply_gen.generate_reply(mail)
                        st.session_state.reply_drafts[mail['id']] = draft.body
                    st.rerun()
            
            with col_send3:
                if st.button("❌ 초안 닫기", key=f"close_{mail['id']}", use_container_width=True):
                    del st.session_state.reply_drafts[mail['id']]
                    st.rerun()


if __name__ == "__main__":
    main()
