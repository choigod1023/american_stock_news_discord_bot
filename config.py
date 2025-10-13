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
    
    @classmethod
    def validate(cls):
        """설정값 검증"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN이 설정되지 않았습니다.")
        # DISCORD_CHANNEL_ID는 더 이상 필수가 아님 (토픽 기반 필터링 사용)