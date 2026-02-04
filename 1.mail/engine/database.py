"""
Database Manager Module
SQLite 기반 영구 저장소
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class DBManager:
    """SQLite 데이터베이스 관리자"""
    
    def __init__(self, db_path: str = "data/trade_emails.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_database()
    
    def _get_conn(self) -> sqlite3.Connection:
        """스레드별 연결"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_database(self):
        """테이블 초기화"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                subject TEXT,
                sender TEXT,
                sender_email TEXT,
                snippet TEXT,
                body_text TEXT,
                
                score REAL DEFAULT 0,
                clarity_score REAL DEFAULT 0,
                intent_score REAL DEFAULT 0,
                terms_score REAL DEFAULT 0,
                
                reason TEXT,
                keywords TEXT,
                language TEXT DEFAULT 'EN',
                
                is_spam INTEGER DEFAULT 0,
                has_attachment INTEGER DEFAULT 0,
                is_reply INTEGER DEFAULT 0,
                
                status TEXT DEFAULT 'Active',
                mail_date TEXT,
                full_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON emails(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_score ON emails(score DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_intent ON emails(intent_score DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spam ON emails(is_spam)')
        
        conn.commit()
        logger.info(f"Database initialized: {self.db_path}")
    
    def insert_email_full(self, email_data: Dict) -> bool:
        """이메일 전체 데이터 저장"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO emails 
                (id, subject, sender, sender_email, snippet, body_text,
                 score, clarity_score, intent_score, terms_score,
                 reason, keywords, language, is_spam, has_attachment, is_reply,
                 status, mail_date, full_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_data.get('id'),
                email_data.get('subject'),
                email_data.get('sender'),
                email_data.get('sender_email'),
                email_data.get('snippet'),
                email_data.get('body_text') or email_data.get('body'),
                email_data.get('score', 0),
                email_data.get('clarity_score', 0),
                email_data.get('intent_score', 0),
                email_data.get('terms_score', 0),
                email_data.get('reason', ''),
                email_data.get('keywords', ''),
                email_data.get('language', 'EN'),
                1 if email_data.get('is_spam') else 0,
                1 if email_data.get('has_attachment') else 0,
                1 if email_data.get('is_reply') else 0,
                email_data.get('status', 'Active'),
                email_data.get('mail_date'),
                email_data.get('full_date'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Insert full failed: {e}")
            return False
    
    def get_active_emails(self, sort_by: str = "score", limit: int = 50) -> List[Dict]:
        """활성 이메일 목록 (스팸 제외)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        order_col = {
            'score': 'score',
            'intent_score': 'intent_score',
            'clarity_score': 'clarity_score',
            'terms_score': 'terms_score',
            'date': 'mail_date'
        }.get(sort_by, 'score')
        
        cursor.execute(f'''
            SELECT * FROM emails 
            WHERE status = 'Active' AND is_spam = 0
            ORDER BY {order_col} DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_emails(self, include_spam: bool = False, limit: int = 100) -> List[Dict]:
        """전체 이메일 목록"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if include_spam:
            cursor.execute('SELECT * FROM emails ORDER BY score DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM emails WHERE is_spam = 0 ORDER BY score DESC LIMIT ?', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_email_by_id(self, email_id: str) -> Optional[Dict]:
        """ID로 이메일 조회"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM emails WHERE id = ?', (email_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_status(self, email_id: str, status: str):
        """상태 업데이트"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE emails SET status = ? WHERE id = ?', (status, email_id))
        conn.commit()
    
    def email_exists(self, email_id: str) -> bool:
        """이메일 존재 여부"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM emails WHERE id = ?', (email_id,))
        return cursor.fetchone() is not None
    
    def get_statistics(self) -> Dict:
        """통계"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM emails WHERE status = "Active" AND is_spam = 0')
        stats['active'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM emails WHERE is_spam = 1')
        stats['spam'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM emails WHERE status = "Archived"')
        stats['archived'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(score) FROM emails WHERE is_spam = 0')
        avg = cursor.fetchone()[0]
        stats['avg_score'] = round(avg, 1) if avg else 0
        
        cursor.execute('SELECT COUNT(*) FROM emails WHERE score >= 70 AND is_spam = 0')
        stats['high_priority'] = cursor.fetchone()[0]
        
        return stats
    
    def clear_all(self):
        """모든 데이터 삭제"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM emails')
        conn.commit()
