import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from discord.ext import tasks

from core.config import Config
from ai.ai_summarizer import AISummarizer
from .report_builder import ReportBuilder
from news.market_data import MarketDataCollector
from core.stock_utils import format_news_with_stock_info

logger = logging.getLogger(__name__)

class ReportScheduler:
    def __init__(self, config: Config, target_channels: List, embed_builder):
        """리포트 스케줄러를 초기화합니다."""
        self.config = config
        self.target_channels = target_channels
        self.embed_builder = embed_builder
        self.ai_summarizer = AISummarizer(config.GEMINI_API_KEY)
        self.report_builder = ReportBuilder()
        
    def start_scheduler(self):
        """리포트 스케줄러를 시작합니다."""
        if not self.generate_report.is_running():
            self.generate_report.start()
            logger.info("리포트 스케줄러가 시작되었습니다.")
    
    def stop_scheduler(self):
        """리포트 스케줄러를 중지합니다."""
        if self.generate_report.is_running():
            self.generate_report.stop()
            logger.info("리포트 스케줄러가 중지되었습니다.")
    
    @tasks.loop(seconds=Config.REPORT_INTERVAL)
    async def generate_report(self):
        """1시간마다 Community 뉴스를 수집하고 AI 리포트를 생성합니다."""
        try:
            logger.info("1시간 주기 리포트 생성을 시작합니다.")
            
            # Community API에서 최근 뉴스 수집
            community_news = await self._fetch_community_news_for_report()
            
            if not community_news:
                logger.info("리포트용 뉴스가 없습니다.")
                return
            
            logger.info(f"리포트용 뉴스 {len(community_news)}개를 수집했습니다.")
            
            # 시장 데이터 수집 (나스닥 주가, 공포탐욕지수)
            async with MarketDataCollector() as market_collector:
                market_data = await market_collector.get_market_summary()
                logger.info("시장 데이터 수집 완료")
            
            # AI 요약 생성 (시장 데이터 포함)
            summary = await self.ai_summarizer.summarize_news_with_market_data(community_news, market_data)
            
            if not summary:
                logger.warning("AI 요약 생성에 실패했습니다.")
                return
            
            # Discord 필드 길이 제한 검증 (임베드에 맞게)
            if len(summary) > 800:  # Discord 임베드에 맞게 800자로 제한
                logger.warning(f"요약 길이가 너무 깁니다 ({len(summary)}자). 800자로 제한합니다.")
                summary = summary[:797] + "..."
            
            # 주요 헤드라인 생성 (유명 종목 우선, 상위 5개)
            headlines = format_news_with_stock_info(community_news, max_items=5)

            # 리포트 임베드 생성 (시장 데이터 + 주요 헤드라인 포함)
            report_embed = self.report_builder.create_report_embed(summary, len(community_news), market_data, headlines)
            
            # 모든 타겟 채널에 리포트 전송
            for channel in self.target_channels:
                try:
                    await channel.send(embed=report_embed)
                    logger.info(f"리포트를 {channel.name}에 전송했습니다.")
                    await asyncio.sleep(1)  # API 제한 방지
                except Exception as e:
                    logger.error(f"리포트 전송 실패 ({channel.name}): {e}")
                    
        except Exception as e:
            logger.error(f"리포트 생성 중 오류 발생: {e}")
    
    async def _fetch_community_news_for_report(self) -> List[Dict]:
        """Community API에서 리포트용 뉴스를 수집합니다."""
        try:
            async with aiohttp.ClientSession() as session:
                # 최근 뉴스 수집을 위해 더 많은 데이터를 가져와서 필터링
                # page_size가 너무 크면 API에서 422 오류가 발생할 수 있으므로 제한
                max_page_size = min(self.config.REPORT_PAGE_SIZE * 2, 100)  # 최대 100개로 제한
                params = {
                    'page': 1,
                    'page_size': max_page_size,
                    'category': 'user_news',
                    'sort': 'created_at_desc',
                    'search': ''
                }
                
                async with session.get(self.config.API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get('posts', [])
                        
                        # 뉴스 중복 방지 및 최신 뉴스 우선순위 적용
                        filtered_news = self._filter_and_prioritize_news(posts)
                        
                        logger.info(f"필터링된 뉴스 {len(filtered_news)}개를 수집했습니다.")
                        return filtered_news
                    elif response.status == 422:
                        # 422 오류 시 page_size를 줄여서 재시도
                        logger.warning(f"HTTP 422 오류 발생, page_size를 줄여서 재시도합니다.")
                        fallback_params = params.copy()
                        fallback_params['page_size'] = 50  # 더 작은 값으로 재시도
                        
                        async with session.get(self.config.API_URL, params=fallback_params) as fallback_response:
                            if fallback_response.status == 200:
                                data = await fallback_response.json()
                                posts = data.get('posts', [])
                                filtered_news = self._filter_and_prioritize_news(posts)
                                logger.info(f"재시도 성공: 필터링된 뉴스 {len(filtered_news)}개를 수집했습니다.")
                                return filtered_news
                            else:
                                error_text = await fallback_response.text()
                                logger.error(f"재시도도 실패: HTTP {fallback_response.status}")
                                logger.error(f"API 응답: {error_text}")
                                return []
                    else:
                        # 더 자세한 오류 정보 로깅
                        error_text = await response.text()
                        logger.error(f"Community API 호출 실패: HTTP {response.status}")
                        logger.error(f"API 응답: {error_text}")
                        logger.error(f"요청 파라미터: {params}")
                        return []
                        
        except Exception as e:
            logger.error(f"Community 뉴스 수집 중 오류 발생: {e}")
            return []
    
    def _filter_and_prioritize_news(self, posts: List[Dict]) -> List[Dict]:
        """뉴스를 필터링하고 우선순위를 적용합니다."""
        from datetime import datetime, timedelta
        import re
        
        # 최근 2시간 내 뉴스만 고려 (더 넓은 범위에서 최신 뉴스 선별)
        cutoff_time = datetime.now() - timedelta(hours=2)
        
        filtered_posts = []
        seen_titles = set()  # 제목 기반 중복 방지
        seen_content_hashes = set()  # 내용 기반 중복 방지
        
        for post in posts:
            try:
                # 시간 필터링
                created_at_str = post.get('created_at', '')
                if created_at_str:
                    # ISO 형식 시간 파싱
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    if created_at.replace(tzinfo=None) < cutoff_time:
                        continue
                
                # 제목 정규화 및 중복 체크
                title = post.get('title', '').strip()
                if not title:
                    continue
                
                # 제목 정규화 (특수문자, 공백 정리)
                normalized_title = re.sub(r'[^\w\s]', '', title.lower())
                normalized_title = re.sub(r'\s+', ' ', normalized_title).strip()
                
                if normalized_title in seen_titles:
                    continue
                
                # 내용 기반 중복 체크 (첫 100자 해시)
                content = post.get('content', '')
                content_hash = hash(content[:100]) if content else 0
                if content_hash in seen_content_hashes:
                    continue
                
                # 중요도 점수 계산
                importance_score = self._calculate_importance_score(post)
                post['_importance_score'] = importance_score
                
                filtered_posts.append(post)
                seen_titles.add(normalized_title)
                seen_content_hashes.add(content_hash)
                
                # 최대 개수 제한
                if len(filtered_posts) >= self.config.REPORT_PAGE_SIZE:
                    break
                    
            except Exception as e:
                logger.warning(f"뉴스 필터링 중 오류: {e}")
                continue
        
        # 중요도 점수 기준으로 정렬 (높은 점수 우선)
        filtered_posts.sort(key=lambda x: x.get('_importance_score', 0), reverse=True)
        
        return filtered_posts[:self.config.REPORT_PAGE_SIZE]
    
    def _calculate_importance_score(self, post: Dict) -> int:
        """뉴스의 중요도 점수를 계산합니다."""
        score = 0
        
        # 좋아요 수 (가중치 높음)
        like_count = post.get('like_stats', {}).get('like_count', 0)
        score += like_count * 3
        
        # 조회수
        view_count = post.get('view_count', 0)
        score += min(view_count // 10, 50)  # 조회수는 최대 50점
        
        # 댓글 수
        comment_count = post.get('comment_count', 0)
        score += comment_count * 2
        
        # 제목에 중요한 키워드가 있는지 확인
        title = post.get('title', '').lower()
        important_keywords = [
            '속보', '긴급', '중요', '특보', '급등', '급락', '폭등', '폭락',
            'ai', '반도체', '테슬라', '애플', '구글', '마이크로소프트', '아마존',
            'nvidia', 'amd', '인텔', '삼성', 'sk하이닉스', 'lg', '현대차',
            'fed', '연준', '금리', '인플레이션', 'gdp', '고용지표'
        ]
        
        for keyword in important_keywords:
            if keyword in title:
                score += 10
        
        # 최근성 보너스 (최근 30분 내면 보너스)
        try:
            created_at_str = post.get('created_at', '')
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                time_diff = datetime.now() - created_at.replace(tzinfo=None)
                if time_diff.total_seconds() < 1800:  # 30분
                    score += 20
        except:
            pass
        
        return score
    
    async def manual_report_generation(self):
        """수동으로 리포트를 생성합니다 (테스트용)."""
        logger.info("수동 리포트 생성을 시작합니다.")
        await self.generate_report()
