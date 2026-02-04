"""
Inquiry Analyzer Module (v2.0 - Async Support)
무역 인콰이어리 메일 분석 엔진

가중치: Intent(50%) + Terms(35%) + Clarity(15%)
비동기 처리 지원
"""

import re
import json
import logging
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# OpenAI import (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class AnalysisResult:
    """분석 결과"""
    total: float
    clarity: float
    intent: float
    terms: float
    reason: str
    keywords: str
    is_spam: bool = False
    language: str = 'EN'


class GibberishDetector:
    """Gibberish 탐지기 - 한글 완성형 30% 이상이면 정상"""
    
    KEYBOARD_PATTERNS = ['qwert', 'asdf', 'zxcv', '12345', 'abcde']
    SPAM_THRESHOLD = 50
    
    def detect(self, text: str) -> Tuple[int, List[str], bool]:
        """Gibberish 탐지 - Returns: (score, reasons, is_gibberish)"""
        if not text or len(text.strip()) < 5:
            return 100, ['empty_content'], True
        
        text = text.strip()
        reasons = []
        score = 0
        
        # 한글 완성형 비율 체크 (30% 이상이면 정상)
        korean_syllables = len(re.findall(r'[\uac00-\ud7a3]', text))
        total_chars = len(text.replace(' ', ''))
        korean_ratio = korean_syllables / max(total_chars, 1)
        
        if korean_ratio >= 0.3:
            return 0, [], False
        
        # 자음/모음만 연속 체크
        jamo_pattern = re.findall(r'[ㄱ-ㅎㅏ-ㅣ]{3,}', text)
        if jamo_pattern:
            score += min(30, len(jamo_pattern) * 10)
            reasons.append('consecutive_jamo')
        
        # 키보드 패턴
        text_lower = text.lower()
        for pattern in self.KEYBOARD_PATTERNS:
            if pattern in text_lower:
                score += 15
                reasons.append('keyboard_pattern')
                break
        
        # 반복 문자
        if re.search(r'(.)\1{4,}', text):
            score += 15
            reasons.append('repeated_chars')
        
        # 특수문자 과다
        special_ratio = len(re.findall(r'[^\w\s\uac00-\ud7a3]', text)) / max(len(text), 1)
        if special_ratio > 0.3:
            score += 15
            reasons.append('excessive_special_chars')
        
        # 의미있는 영어 단어 체크
        english_words = re.findall(r'[a-zA-Z]{3,}', text)
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 
                       'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
                       'dear', 'please', 'thank', 'regards', 'order', 'price',
                       'shipment', 'delivery', 'payment', 'product', 'inquiry'}
        
        if english_words:
            matched = sum(1 for w in english_words if w.lower() in common_words)
            if matched / len(english_words) < 0.1 and len(english_words) > 5:
                score += 20
                reasons.append('no_meaningful_words')
        
        is_gibberish = score >= self.SPAM_THRESHOLD
        return score, reasons, is_gibberish


class SpamDetector:
    """스팸 탐지기"""
    
    SPAM_PATTERNS = [
        (r'you\s*(have\s*)?won', 'lottery_scam', 30),
        (r'claim\s*(your\s*)?(prize|reward)', 'prize_scam', 30),
        (r'click\s*here', 'click_bait', 20),
        (r'act\s*now', 'urgency_scam', 20),
        (r'100%\s*(free|guaranteed)', 'over_promise', 25),
        (r'unsubscribe', 'newsletter', 15),
        (r'nigerian?\s*prince', 'nigerian_scam', 50),
    ]
    
    SUSPICIOUS_DOMAINS = ['.xyz', '.tk', '.ml', '.ga', '.cf', '.gq', '.buzz']
    
    def __init__(self):
        self.patterns = [(re.compile(p, re.I), n, s) for p, n, s in self.SPAM_PATTERNS]
    
    def detect(self, email_data: Dict, text: str, gibberish_score: int = 0) -> Tuple[int, List[str], bool]:
        """스팸 탐지 - Returns: (score, reasons, is_spam)"""
        if not text:
            text = ''
        
        score = gibberish_score
        reasons = []
        
        # 패턴 매칭
        for pattern, name, points in self.patterns:
            if pattern.search(text):
                score += points
                reasons.append(name)
        
        # 의심 도메인 체크
        sender_email = email_data.get('sender_email', '') or ''
        if isinstance(sender_email, str):
            for domain in self.SUSPICIOUS_DOMAINS:
                if sender_email.lower().endswith(domain):
                    score += 25
                    reasons.append('suspicious_domain')
                    break
        
        # 제목 체크
        subject = email_data.get('subject', '') or ''
        if subject.isupper() and len(subject) > 10:
            score += 15
            reasons.append('all_caps_subject')
        
        if subject.count('!') > 3:
            score += 10
            reasons.append('excessive_exclamation')
        
        is_spam = score >= 50
        return score, reasons, is_spam


class InquiryAnalyzer:
    """무역 인콰이어리 분석기 (비동기 지원)"""
    
    # 가중치: Intent(50%) + Terms(35%) + Clarity(15%)
    WEIGHTS = {
        'clarity': 0.15,
        'intent': 0.50,
        'terms': 0.35
    }
    
    def __init__(self, openai_api_key: str = None, keywords_path: str = "config/keywords.json",
                 jargon_path: str = "config/jargon_map.json"):
        
        self.openai_key = openai_api_key
        self.client = None
        self._demo_mode = not OPENAI_AVAILABLE or not openai_api_key
        
        if not self._demo_mode:
            try:
                self.client = OpenAI(api_key=openai_api_key)
            except Exception as e:
                logger.error(f"OpenAI init failed: {e}")
                self._demo_mode = True
        
        self.keywords = self._load_json(keywords_path)
        self.jargon_map = self._load_json(jargon_path)
        
        self.gibberish_detector = GibberishDetector()
        self.spam_detector = SpamDetector()
        
        # 비동기 처리용 ThreadPool
        self._executor = ThreadPoolExecutor(max_workers=5)
    
    def _load_json(self, path: str) -> Dict:
        """JSON 로드"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"File not found: {path}")
            return {}
    
    def is_demo_mode(self) -> bool:
        return self._demo_mode
    
    def detect_language(self, text: str) -> str:
        """언어 감지"""
        if not text:
            return 'EN'
        
        korean_chars = len(re.findall(r'[\uac00-\ud7a3ㄱ-ㅎㅏ-ㅣ]', text))
        total = len(text.replace(' ', ''))
        
        if total == 0:
            return 'EN'
        
        korean_ratio = korean_chars / total
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        japanese_chars = len(re.findall(r'[\u3040-\u30ff]', text))
        
        if korean_ratio > 0.1:
            return 'KO'
        elif chinese_chars / total > 0.1:
            return 'OTHER'
        elif japanese_chars / total > 0.05:
            return 'OTHER'
        
        return 'EN'
    
    def replace_jargon(self, text: str) -> str:
        """한국어 무역 은어 치환"""
        jargon = self.jargon_map.get('korean_jargon', {})
        
        for ko, en in jargon.items():
            text = re.sub(re.escape(ko), en, text, flags=re.IGNORECASE)
        
        return text
    
    def calculate_keyword_scores(self, text: str) -> Tuple[Dict[str, float], List[str]]:
        """키워드 매칭 스코어 계산"""
        text_lower = text.lower()
        
        scores = {'clarity': 0, 'intent': 0, 'terms': 0}
        matched_keywords = []
        
        category_map = {
            'product_clarity': 'clarity',
            'buying_intent': 'intent',
            'trade_terms': 'terms'
        }
        
        for cat_key, score_key in category_map.items():
            cat_data = self.keywords.get(cat_key, {})
            words = cat_data.get('words', {})
            
            for word, points in words.items():
                if word.lower() in text_lower:
                    scores[score_key] += points
                    matched_keywords.append(word)
        
        # 스팸 키워드 체크 (감점)
        spam_words = self.keywords.get('spam_keywords', {}).get('words', {})
        for word, points in spam_words.items():
            if word.lower() in text_lower:
                for key in scores:
                    scores[key] = max(0, scores[key] + points)
        
        return scores, matched_keywords
    
    def calculate_score(self, email_data: Dict) -> Dict[str, Any]:
        """메일 분석 및 스코어 계산 (동기)"""
        body = email_data.get('body', '') or email_data.get('snippet', '') or ''
        subject = email_data.get('subject', '') or ''
        has_attachment = email_data.get('has_attachment', False)
        
        full_text = f"{subject}\n{body}"
        
        # 1. 언어 감지
        language = self.detect_language(full_text)
        
        # 2. 기타 언어는 Low Priority
        if language == 'OTHER':
            return {
                'total': 0, 'clarity': 0, 'intent': 0, 'terms': 0,
                'reason': '지원되지 않는 언어입니다 (영어/한국어만 지원)',
                'keywords': '', 'is_spam': False, 'language': language
            }
        
        # 3. Gibberish 탐지
        gib_score, gib_reasons, is_gibberish = self.gibberish_detector.detect(full_text)
        
        if is_gibberish:
            return {
                'total': 0, 'clarity': 0, 'intent': 0, 'terms': 0,
                'reason': f'의미없는 콘텐츠 (Gibberish): {", ".join(gib_reasons)}',
                'keywords': '', 'is_spam': True, 'language': language
            }
        
        # 4. 한국어면 은어 치환
        analysis_text = full_text
        if language == 'KO':
            analysis_text = self.replace_jargon(full_text)
        
        # 5. 스팸 탐지
        spam_score, spam_reasons, is_spam = self.spam_detector.detect(
            email_data, analysis_text, gib_score
        )
        
        if is_spam:
            return {
                'total': 0, 'clarity': 0, 'intent': 0, 'terms': 0,
                'reason': f'스팸으로 판정: {", ".join(spam_reasons[:3])}',
                'keywords': '', 'is_spam': True, 'language': language
            }
        
        # 6. 키워드 스코어 계산
        kw_scores, matched_keywords = self.calculate_keyword_scores(analysis_text)
        
        # 7. 보너스 점수
        bonus = self.keywords.get('bonus', {})
        
        if subject.lower().startswith(('re:', 'fwd:')):
            kw_scores['intent'] += bonus.get('thread_reply', 20)
        
        if has_attachment:
            kw_scores['intent'] += bonus.get('has_attachment', 10)
        
        # 8. 정규화 (0-100)
        clarity = min(100, max(0, kw_scores['clarity']))
        intent = min(100, max(0, kw_scores['intent']))
        terms = min(100, max(0, kw_scores['terms']))
        
        # 9. 종합 점수 (가중 평균)
        total = (
            clarity * self.WEIGHTS['clarity'] +
            intent * self.WEIGHTS['intent'] +
            terms * self.WEIGHTS['terms']
        )
        total = round(total, 1)
        
        # 10. 분석 근거 생성
        reason = self._generate_reason(clarity, intent, terms, matched_keywords)
        
        return {
            'total': total,
            'clarity': round(clarity, 1),
            'intent': round(intent, 1),
            'terms': round(terms, 1),
            'reason': reason,
            'keywords': ', '.join(matched_keywords[:10]),
            'is_spam': False,
            'language': language
        }
    
    async def calculate_score_async(self, email_data: Dict) -> Dict[str, Any]:
        """메일 분석 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.calculate_score,
            email_data
        )
    
    async def batch_analyze_async(self, emails: List[Dict]) -> List[Dict[str, Any]]:
        """배치 분석 (비동기)"""
        tasks = [self.calculate_score_async(email) for email in emails]
        return await asyncio.gather(*tasks)
    
    def _generate_reason(self, clarity: float, intent: float, terms: float, 
                        keywords: List[str]) -> str:
        """분석 근거 생성"""
        reasons = []
        
        if intent >= 70:
            reasons.append("강한 구매 의도 감지")
        elif intent >= 40:
            reasons.append("중간 수준의 구매 의도")
        else:
            reasons.append("구매 의도 불명확")
        
        if terms >= 60:
            reasons.append("구체적인 무역 조건 제시")
        elif terms >= 30:
            reasons.append("일부 무역 조건 언급")
        
        if clarity >= 50:
            reasons.append("제품 스펙 상세히 기술")
        elif clarity >= 25:
            reasons.append("기본적인 제품 정보 있음")
        
        if keywords:
            key_str = ', '.join(keywords[:5])
            reasons.append(f"주요 키워드: {key_str}")
        
        return ' | '.join(reasons) if reasons else "추가 분석 필요"
