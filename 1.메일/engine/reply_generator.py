"""
Reply Generator Module
AI 기반 무역 메일 답장 초안 자동 생성

OpenAI GPT를 활용하여 수신 메일의 언어와 내용에 맞는
전문적인 무역 답장 초안을 생성합니다.
"""

import re
import json
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# OpenAI import (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class ReplyDraft:
    """답장 초안 결과"""
    subject: str
    body: str
    language: str
    sender_name: str
    key_points: list
    tone: str  # formal, friendly, urgent


class ReplyGenerator:
    """AI 답장 초안 생성기"""
    
    # 한국어 답장 템플릿
    KO_TEMPLATES = {
        'inquiry': """안녕하세요,

보내주신 문의사항('{subject}')은 현재 담당부서에서 상세히 검토 중에 있습니다.

Reviewing your inquiry in detail.

내용 확인이 완료되는 대로 신속히 추가 답변 드리겠습니다.

감사합니다,
해외영업팀 드림""",

        'quotation': """안녕하세요,

요청하신 견적 관련 문의에 감사드립니다.

검토 후 정식 견적서를 송부해 드리겠습니다.
추가 문의사항이 있으시면 말씀해 주세요.

감사합니다,
해외영업팀 드림""",

        'order': """안녕하세요,

발주 관련 문의에 감사드립니다.

말씀하신 내용을 확인하여 빠른 시일 내에 
Proforma Invoice와 함께 상세 회신 드리겠습니다.

감사합니다,
해외영업팀 드림"""
    }
    
    # 영어 답장 템플릿
    EN_TEMPLATES = {
        'inquiry': """Dear {sender_name},

Thank you for your inquiry regarding '{subject}'.

We are currently reviewing your request in detail and will get back to you shortly with more information.

Best regards,
Export Sales Team""",

        'quotation': """Dear {sender_name},

Thank you for your interest in our products.

We are preparing a formal quotation based on your requirements and will send it to you soon.

Please feel free to contact us if you have any questions.

Best regards,
Export Sales Team""",

        'order': """Dear {sender_name},

Thank you for your purchase order inquiry.

We are reviewing the details and will send you a Proforma Invoice along with our confirmation shortly.

Best regards,
Export Sales Team"""
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._demo_mode = not OPENAI_AVAILABLE or not api_key
        self.client = None
        
        if not self._demo_mode:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"OpenAI init failed: {e}")
                self._demo_mode = True
    
    def is_demo_mode(self) -> bool:
        return self._demo_mode
    
    def detect_language(self, text: str) -> str:
        """언어 감지"""
        if not text:
            return 'EN'
        
        korean_chars = len(re.findall(r'[\uac00-\ud7a3]', text))
        total = len(text.replace(' ', ''))
        
        if total == 0:
            return 'EN'
        
        return 'KO' if korean_chars / total > 0.1 else 'EN'
    
    def extract_sender_name(self, sender: str) -> str:
        """발신자 이름 추출"""
        if not sender:
            return "Sir/Madam"
        
        # "John Smith <john@email.com>" -> "John Smith"
        name = sender.split('<')[0].strip()
        
        if not name or '@' in name:
            return "Sir/Madam"
        
        # "김철수" or "John" 등 짧은 이름 처리
        name = name.strip('"\'')
        return name if name else "Sir/Madam"
    
    def detect_intent(self, subject: str, body: str) -> str:
        """메일 의도 감지"""
        text = f"{subject} {body}".lower()
        
        if any(kw in text for kw in ['order', 'po', 'purchase', '발주', '주문', 'proforma']):
            return 'order'
        elif any(kw in text for kw in ['quote', 'quotation', 'price', '견적', '단가', 'cost']):
            return 'quotation'
        else:
            return 'inquiry'
    
    def generate_reply(self, email_data: Dict) -> ReplyDraft:
        """
        AI 답장 초안 생성
        
        Args:
            email_data: {subject, body/snippet, sender, sender_email, language, ...}
        
        Returns:
            ReplyDraft with subject, body, language
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body_text') or email_data.get('body') or email_data.get('snippet', '')
        sender = email_data.get('sender', '')
        language = email_data.get('language') or self.detect_language(f"{subject} {body}")
        
        sender_name = self.extract_sender_name(sender)
        intent = self.detect_intent(subject, body)
        
        # OpenAI 모드면 GPT 사용
        if not self._demo_mode:
            return self._generate_with_gpt(
                subject=subject,
                body=body,
                sender_name=sender_name,
                language=language,
                intent=intent
            )
        
        # Demo 모드면 템플릿 사용
        return self._generate_from_template(
            subject=subject,
            sender_name=sender_name,
            language=language,
            intent=intent
        )
    
    def _generate_with_gpt(self, subject: str, body: str, sender_name: str, 
                          language: str, intent: str) -> ReplyDraft:
        """GPT를 사용한 답장 생성"""
        try:
            lang_instruction = "한국어로" if language == 'KO' else "in English"
            
            prompt = f"""You are a professional export sales representative. 
Generate a polite and professional reply email {lang_instruction}.

Original Email:
Subject: {subject}
Content: {body[:1500]}

Requirements:
1. Write the reply {lang_instruction}
2. Be professional and courteous
3. Acknowledge receipt of their inquiry
4. Mention that you are reviewing their request
5. Promise a detailed follow-up soon
6. Keep it concise (under 150 words)
7. Do NOT include email headers like "Subject:" or "To:" - just the body text
8. Start with appropriate greeting using sender name: {sender_name}
9. End with "Best regards," or "감사합니다," and "Export Sales Team" or "해외영업팀 드림"

Return ONLY the email body text, nothing else."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            reply_body = response.choices[0].message.content.strip()
            
            # 제목 생성
            reply_subject = f"Re: {subject}"
            
            return ReplyDraft(
                subject=reply_subject,
                body=reply_body,
                language=language,
                sender_name=sender_name,
                key_points=[intent],
                tone='formal'
            )
            
        except Exception as e:
            logger.error(f"GPT reply generation failed: {e}")
            return self._generate_from_template(subject, sender_name, language, intent)
    
    def _generate_from_template(self, subject: str, sender_name: str, 
                                language: str, intent: str) -> ReplyDraft:
        """템플릿 기반 답장 생성 (Demo 모드)"""
        
        templates = self.KO_TEMPLATES if language == 'KO' else self.EN_TEMPLATES
        template = templates.get(intent, templates['inquiry'])
        
        # 템플릿 변수 치환
        reply_body = template.format(
            sender_name=sender_name,
            subject=subject[:50]
        )
        
        reply_subject = f"Re: {subject}"
        
        return ReplyDraft(
            subject=reply_subject,
            body=reply_body,
            language=language,
            sender_name=sender_name,
            key_points=[intent],
            tone='formal'
        )
    
    def regenerate_with_context(self, email_data: Dict, additional_context: str) -> ReplyDraft:
        """추가 컨텍스트를 포함한 답장 재생성"""
        if self._demo_mode:
            # Demo 모드에서는 기본 답장에 컨텍스트 추가
            draft = self.generate_reply(email_data)
            draft.body = f"{draft.body}\n\n{additional_context}"
            return draft
        
        subject = email_data.get('subject', '')
        body = email_data.get('body_text') or email_data.get('body') or email_data.get('snippet', '')
        sender = email_data.get('sender', '')
        language = email_data.get('language') or self.detect_language(f"{subject} {body}")
        sender_name = self.extract_sender_name(sender)
        
        try:
            lang_instruction = "한국어로" if language == 'KO' else "in English"
            
            prompt = f"""You are a professional export sales representative.
Generate a reply email {lang_instruction} incorporating this additional context.

Original Email:
Subject: {subject}
Content: {body[:1000]}

Additional Context/Instructions:
{additional_context}

Write a professional reply {lang_instruction}. Return ONLY the email body."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600
            )
            
            return ReplyDraft(
                subject=f"Re: {subject}",
                body=response.choices[0].message.content.strip(),
                language=language,
                sender_name=sender_name,
                key_points=[],
                tone='formal'
            )
            
        except Exception as e:
            logger.error(f"GPT regeneration failed: {e}")
            draft = self._generate_from_template(subject, sender_name, language, 'inquiry')
            draft.body = f"{draft.body}\n\n{additional_context}"
            return draft
