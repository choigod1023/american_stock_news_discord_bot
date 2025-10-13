import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

class NewsAPIClient:
    def __init__(self, community_api_url: str, news_api_url: str, page_size: int = 20, breaking_keywords: List[str] = None):
        self.community_api_url = community_api_url
        self.news_api_url = news_api_url
        self.page_size = page_size
        self.breaking_keywords = breaking_keywords or ['속보', '긴급', '중요', '특보', '긴급속보', '특별속보']
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_news(self, page: int = 1) -> Optional[Dict]:
        """뉴스 데이터를 두 개의 API에서 가져와서 병합합니다."""
        try:
            # 두 API에서 데이터를 병렬로 가져오기
            community_data, news_data = await asyncio.gather(
                self._fetch_community_news(page),
                self._fetch_news_api(page),
                return_exceptions=True
            )
            
            # 결과 병합
            merged_posts = []
            
            # Community API 결과 처리 (리스트를 뒤에서부터 읽어오기)
            if isinstance(community_data, dict) and 'posts' in community_data:
                community_posts = community_data['posts']
                # 리스트를 뒤에서부터 읽어서 최신 뉴스가 앞에 오도록 함
                for post in reversed(community_posts):
                    # Community API에서 온 뉴스임을 표시
                    post['_source_api'] = 'community'
                    merged_posts.append(post)
                logger.info(f"Community API: {len(community_posts)}개 뉴스 수신")
            
            # News API 결과 처리 (리스트를 뒤에서부터 읽어오기)
            if isinstance(news_data, dict) and 'news_list' in news_data:
                news_posts = news_data['news_list']
                # 리스트를 뒤에서부터 읽어서 최신 뉴스가 앞에 오도록 함
                for post in reversed(news_posts):
                    # News API에서 온 뉴스임을 표시
                    post['_source_api'] = 'news'
                    merged_posts.append(post)
                logger.info(f"News API: {len(news_posts)}개 뉴스 수신")
            
            # 중복 제거 (ID 기준) - 이미 시간순으로 정렬된 상태에서 중복 제거
            seen_ids = set()
            unique_posts = []
            for post in merged_posts:
                post_id = post.get('id')
                if post_id and post_id not in seen_ids:
                    seen_ids.add(post_id)
                    unique_posts.append(post)
            
            logger.info(f"병합 완료: 총 {len(unique_posts)}개 고유 뉴스")
            
            return {
                'posts': unique_posts,
                'total_count': len(unique_posts),
                'page': page,
                'page_size': self.page_size,
                'from_cache': False
            }
                    
        except Exception as e:
            logger.error(f"뉴스 가져오기 중 오류 발생: {e}")
            return None
    
    async def _fetch_community_news(self, page: int = 1) -> Optional[Dict]:
        """Community API에서 뉴스를 가져옵니다."""
        try:
            params = {
                'page': page,
                'page_size': self.page_size,
                'category': 'user_news',
                'sort': 'created_at_desc',
                'search': ''
            }
            
            async with self.session.get(self.community_api_url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Community API 호출 실패: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Community API 호출 중 오류 발생: {e}")
            return None
    
    async def _fetch_news_api(self, page: int = 1) -> Optional[Dict]:
        """News API에서 뉴스를 가져옵니다."""
        try:
            params = {
                'page': page,
                'page_size': self.page_size,
                'sort': 'created_at_desc'
            }
            
            async with self.session.get(self.news_api_url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"News API 호출 실패: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"News API 호출 중 오류 발생: {e}")
            return None
    
    def get_news_list(self, data: Dict) -> List[Dict]:
        """API 응답에서 뉴스 리스트를 추출합니다."""
        return data.get('posts', [])
    
    def is_breaking_news(self, news: Dict) -> bool:
        """뉴스가 속보인지 판단합니다."""
        title = news.get('title', '')
        content = news.get('content', '')
        community_tags = news.get('community_tags', [])
        tag_names = news.get('tag_names', [])  # News API의 태그 구조
        
        # 제목에서 속보 키워드 확인
        for keyword in self.breaking_keywords:
            if keyword in title:
                return True
        
        # 내용에서 속보 키워드 확인
        for keyword in self.breaking_keywords:
            if keyword in content:
                return True
        
        # 커뮤니티 태그에서 속보 관련 태그 확인 (Community API)
        for tag in community_tags:
            if any(keyword in tag for keyword in self.breaking_keywords):
                return True
        
        # 태그 이름에서 속보 관련 태그 확인 (News API)
        for tag in tag_names:
            if any(keyword in tag for keyword in self.breaking_keywords):
                return True
        
        # 특정 패턴 확인 (예: [속보], [긴급] 등)
        breaking_patterns = [
            r'\[속보\]', r'\[긴급\]', r'\[중요\]', r'\[특보\]',
            r'속보:', r'긴급:', r'중요:', r'특보:',
            r'🚨', r'⚡', r'🔥'
        ]
        
        for pattern in breaking_patterns:
            if re.search(pattern, title, re.IGNORECASE) or re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def is_important_news(self, news: Dict, threshold: int = 5, from_news_api: bool = False) -> bool:
        """뉴스가 중요한지 판단합니다 (속보가 아닌 경우)."""
        # 속보는 항상 중요하므로 별도 처리
        if self.is_breaking_news(news):
            return True
        
        # News API에서 온 뉴스만 중요 뉴스 구분 적용
        if not from_news_api:
            return False
            
        like_count = news.get('like_stats', {}).get('like_count', 0)
        view_count = news.get('view_count', 0)
        
        # 좋아요 수가 임계값을 넘거나 조회수가 높은 경우 중요 뉴스로 판단
        return like_count >= threshold or view_count >= 100
    
    def get_news_type(self, news: Dict) -> str:
        """뉴스 타입을 반환합니다."""
        if self.is_breaking_news(news):
            return "속보"
        elif self.is_important_news(news):
            return "중요"
        else:
            return "일반"
    
    def format_news_url(self, news_id: str, source_api: str = None) -> str:
        """뉴스 상세 페이지 URL을 생성합니다."""
        if source_api == 'news':
            # News API의 경우 news 라우터 사용
            return f"https://saveticker.com/news/{news_id}"
        else:
            # Community API의 경우 community 라우터 사용
            return f"https://saveticker.com/community/{news_id}"