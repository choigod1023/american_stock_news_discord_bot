import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    # 디스코드 설정
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')  # 이제 선택사항 (토픽 기반 필터링 사용)
    
    # API 설정
    API_URL = os.getenv('API_URL', 'https://api.saveticker.com/api/community/list')
    NEWS_API_URL = os.getenv('NEWS_API_URL', 'https://api.saveticker.com/api/news/list')
    API_PAGE_SIZE = int(os.getenv('API_PAGE_SIZE', 20))
    
    # 속보 판단 키워드
    BREAKING_NEWS_KEYWORDS = os.getenv('BREAKING_NEWS_KEYWORDS', '속보,긴급,중요,특보,긴급속보,특별속보').split(',')
    
    # 일반 중요 메시지 판단 기준
    IMPORTANT_LIKE_THRESHOLD = int(os.getenv('IMPORTANT_LIKE_THRESHOLD', 5))
    
    # 업데이트 간격 (초)
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 10))
    
    # AI 리포트 설정
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    REPORT_INTERVAL = int(os.getenv('REPORT_INTERVAL', 3600))  # 1시간 (3600초)
    REPORT_PAGE_SIZE = int(os.getenv('REPORT_PAGE_SIZE', 30))  # 리포트용 뉴스 수집 개수
    
    @classmethod
    def validate(cls):
        """설정값 검증"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN이 설정되지 않았습니다.")
        
        # GEMINI_API_KEY는 선택사항 (없으면 기본 요약 모드로 동작)
        if not cls.GEMINI_API_KEY:
            print("⚠️ 경고: GEMINI_API_KEY가 설정되지 않았습니다. AI 요약 대신 기본 요약이 제공됩니다.")
        
        # DISCORD_CHANNEL_ID는 더 이상 필수가 아님 (토픽 기반 필터링 사용)