import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict
import aiohttp
from io import BytesIO
import discord

from .api_client import NewsAPIClient
from .cache_manager import NewsCacheManager

logger = logging.getLogger(__name__)

class NewsHandler:
    """뉴스 처리 및 전송을 담당하는 클래스"""
    
    def __init__(self, config, cache_manager: NewsCacheManager):
        self.config = config
        self.cache_manager = cache_manager
    
    async def process_and_send_news(self, target_channels: List[discord.TextChannel], embed_builder, image_handler):
        """뉴스를 처리하고 채널에 전송합니다."""
        try:
            async with NewsAPIClient(
                self.config.API_URL,
                self.config.NEWS_API_URL,
                self.config.API_PAGE_SIZE, 
                self.config.BREAKING_NEWS_KEYWORDS
            ) as api_client:
                data = await api_client.fetch_news()
                if not data:
                    return
                
                # (예외 우선 처리) 응답 변경 여부와 무관하게 요약형 커뮤니티 포스트는 즉시 전송 시도
                try:
                    all_posts = api_client.get_news_list(data)
                    summary_candidates = [p for p in all_posts if p.get('_source_api') == 'community' and self._is_summary_style_post(p)]
                    for post in summary_candidates:
                        post_id = post.get('id')
                        if post_id and self.cache_manager.has_sent_summary(post_id):
                            continue
                        title = post.get('title', '제목 없음')
                        url = api_client.format_news_url(post.get('id', ''), post.get('_source_api', 'community'))
                        # 임베드로 전송
                        embed = discord.Embed(
                            title="🧾 커뮤니티 요약",
                            description=title,
                            color=0x00bfff,
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="🔗 상세 보기", value=f"[링크]({url})", inline=False)
                        for channel in target_channels:
                            try:
                                await channel.send(embed=embed)
                                await asyncio.sleep(0.3)
                            except Exception as e:
                                logger.error(f"요약형 커뮤니티 포스트 전송 실패: {e}")
                        if post_id:
                            self.cache_manager.mark_sent_summary(post_id)
                except Exception as e:
                    logger.warning(f"요약형 포스트 선전송 처리 중 경고: {e}")

                # API 응답이 변경되었는지 확인
                if not self.cache_manager.has_response_changed(data):
                    logger.info("API 응답에 변경사항이 없습니다.")
                    return
                
                # 새로운 뉴스만 필터링 (파일 기반 캐시 사용)
                new_news = self.cache_manager.get_new_news(data)
                
                # NEWS_API_URL 뉴스만 즉시 전송, Community 뉴스는 리포트용으로 제외
                news_api_news = [news for news in new_news if news.get('_source_api') == 'news']
                
                if news_api_news:
                    logger.info(f"{len(news_api_news)}개의 새로운 공식 뉴스를 {len(target_channels)}개 채널에 전송합니다.")
                    for channel in target_channels:
                        await self._send_news_to_channel(channel, news_api_news, api_client, embed_builder, image_handler)
                
                # Community 뉴스는 로그만 남기고 리포트에서 처리
                community_news = [news for news in new_news if news.get('_source_api') == 'community']
                if community_news:
                    logger.info(f"{len(community_news)}개의 Community 뉴스는 리포트에서 처리됩니다.")

                    # 예외: '장전/장마감/장중 뉴스 한줄 요약(모음)' 스타일은 즉시 텍스트 메시지로 전송
                    summary_posts = [n for n in community_news if self._is_summary_style_post(n)]
                    if summary_posts:
                        logger.info(f"요약형 커뮤니티 포스트 {len(summary_posts)}개를 즉시 메시지로 전송합니다.")
                        for post in summary_posts:
                            post_id = post.get('id')
                            if post_id and self.cache_manager.has_sent_summary(post_id):
                                continue
                            title = post.get('title', '제목 없음')
                            url = api_client.format_news_url(post.get('id', ''), post.get('_source_api', 'community'))
                            embed = discord.Embed(
                                title="🧾 커뮤니티 요약",
                                description=title,
                                color=0x00bfff,
                                timestamp=datetime.now()
                            )
                            embed.add_field(name="🔗 상세 보기", value=f"[링크]({url})", inline=False)
                            for channel in target_channels:
                                try:
                                    await channel.send(embed=embed)
                                    await asyncio.sleep(0.5)
                                except Exception as e:
                                    logger.error(f"요약형 커뮤니티 포스트 전송 실패: {e}")
                            if post_id:
                                self.cache_manager.mark_sent_summary(post_id)
                
        except Exception as e:
            logger.error(f"뉴스 체크 중 오류 발생: {e}")
    
    async def _send_news_to_channel(self, channel, news_list: List[Dict], api_client: NewsAPIClient, embed_builder, image_handler):
        """뉴스 리스트를 디스코드 채널에 전송합니다. (NEWS_API_URL 뉴스만 처리)"""
        for news in news_list:
            try:
                # NEWS_API_URL 뉴스만 처리 (이미 필터링되어 들어옴)
                news_type = api_client.get_news_type(news)
                is_breaking = api_client.is_breaking_news(news)
                from_news_api = True  # 이미 NEWS_API_URL 뉴스만 들어옴
                is_important = api_client.is_important_news(news, self.config.IMPORTANT_LIKE_THRESHOLD, from_news_api)
                
                # 임베드 생성 (썸네일 허용)
                embed = await embed_builder.create_news_embed(news, api_client, news_type, is_breaking, is_important, allow_thumbnail=True)
                
                # 메시지 전송 - 이모지와 정리된 헤드라인 포함
                clean_title = embed_builder._clean_news_title(news.get('title', '제목 없음'))
                
                # 공식 뉴스 API: 기존 규칙 적용
                if is_breaking:
                    message_content = f"@everyone ⚡ {clean_title}"
                elif is_important:
                    message_content = f"@everyone 🔥 {clean_title}"
                else:
                    message_content = f"📈 {clean_title}"
                
                try:
                    message = await channel.send(content=message_content, embed=embed)
                except Exception as send_err:
                    # 썸네일 URL 문제가 의심되면 썸네일 없이 재시도
                    logger.warning(f"메시지 전송 실패, 썸네일 제거 후 재시도: {send_err}")
                    embed_no_thumb = await embed_builder.create_news_embed(
                        news, api_client, news_type, is_breaking, is_important, allow_thumbnail=False
                    )
                    message = await channel.send(content=message_content, embed=embed_no_thumb)
                
                # 속보이거나 중요 뉴스인 경우 핀 고정
                if is_breaking or is_important:
                    try:
                        await message.pin()
                        logger.info(f"{news_type} 뉴스 핀 고정: {news.get('title', 'Unknown')}")
                    except discord.Forbidden:
                        logger.warning("메시지 핀 고정 권한이 없습니다.")
                
                # 이미지가 있으면 첨부
                thumbnail_url = news.get('thumbnail')
                if thumbnail_url:
                    await image_handler.send_image_attachment(channel, thumbnail_url, news.get('title', 'News Image'))
                
                # 잠시 대기 (API 제한 방지)
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"뉴스 전송 중 오류 발생: {e}")

    def _is_summary_style_post(self, news: Dict) -> bool:
        """커뮤니티 요약형 포스트인지 판단합니다 (예: 장전 뉴스 한줄 요약 모음)."""
        title = (news.get('title') or '').strip()
        if not title:
            return False
        # 간단 규칙: 제목에 '요약'이 포함되면 요약형으로 간주
        if '요약' in title:
            return True
        # 대표 패턴들: 장전/장마감/장중 + (뉴스)? + 한줄 요약( 모음)
        patterns = [
            r"장전\s*뉴스?.*한[\s]*줄\s*요약(\s*모음)?",
            r"장마감\s*뉴스?.*한[\s]*줄\s*요약(\s*모음)?",
            r"장중\s*뉴스?.*한[\s]*줄\s*요약(\s*모음)?",
            r"한[\s]*줄\s*요약\s*모음",
        ]
        for pattern in patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True
        return False
    
    async def get_manual_news(self, api_client: NewsAPIClient, embed_builder, count: int = 3) -> List[Dict]:
        """수동 뉴스 체크를 위한 뉴스 데이터를 가져옵니다."""
        data = await api_client.fetch_news()
        if data:
            news_list = api_client.get_news_list(data)
            return news_list[:count]
        return []
