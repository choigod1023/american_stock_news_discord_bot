import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from discord.ext import tasks

from config import Config
from ai_summarizer import AISummarizer
from report_builder import ReportBuilder
from market_data import MarketDataCollector

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
            
            # 리포트 임베드 생성 (시장 데이터 포함)
            report_embed = self.report_builder.create_report_embed(summary, len(community_news), market_data)
            
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
                # 최근 1시간 내 뉴스만 수집하기 위해 현재 시간 기준으로 설정
                params = {
                    'page': 1,
                    'page_size': self.config.REPORT_PAGE_SIZE,
                    'category': 'user_news',
                    'sort': 'created_at_desc',
                    'search': ''
                }
                
                async with session.get(self.config.API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get('posts', [])
                        
                        # 최근 뉴스들만 가져오기 (시간 제한 없음, page_size로 제한)
                        recent_news = posts[:self.config.REPORT_PAGE_SIZE]
                        
                        logger.info(f"최근 뉴스 {len(recent_news)}개를 수집했습니다.")
                        return recent_news
                    else:
                        logger.error(f"Community API 호출 실패: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Community 뉴스 수집 중 오류 발생: {e}")
            return []
    
    async def manual_report_generation(self):
        """수동으로 리포트를 생성합니다 (테스트용)."""
        logger.info("수동 리포트 생성을 시작합니다.")
        await self.generate_report()
