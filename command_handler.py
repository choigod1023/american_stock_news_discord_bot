import asyncio
import logging
from typing import List
import discord
from discord.ext import commands

from api_client import NewsAPIClient
from cache_manager import NewsCacheManager
from embed_builder import EmbedBuilder
from news_handler import NewsHandler

logger = logging.getLogger(__name__)

class CommandHandler:
    """Discord 명령어 처리를 담당하는 클래스"""
    
    def __init__(self, config, cache_manager: NewsCacheManager, embed_builder: EmbedBuilder, news_handler: NewsHandler):
        self.config = config
        self.cache_manager = cache_manager
        self.embed_builder = embed_builder
        self.news_handler = news_handler
    
    async def manual_news_check(self, ctx):
        """수동으로 뉴스를 체크합니다."""
        await ctx.send("뉴스를 확인 중입니다...")
        
        try:
            async with NewsAPIClient(
                self.config.API_URL,
                self.config.NEWS_API_URL,
                self.config.API_PAGE_SIZE, 
                self.config.BREAKING_NEWS_KEYWORDS
            ) as api_client:
                latest_news = await self.news_handler.get_manual_news(api_client, self.embed_builder, 3)
                
                if latest_news:
                    for news in latest_news:
                        news_type = api_client.get_news_type(news)
                        is_breaking = api_client.is_breaking_news(news)
                        # News API에서 온 뉴스만 중요 뉴스 구분 적용
                        from_news_api = news.get('_source_api') == 'news'
                        is_important = api_client.is_important_news(news, self.config.IMPORTANT_LIKE_THRESHOLD, from_news_api)
                        embed = await self.embed_builder.create_news_embed(news, api_client, news_type, is_breaking, is_important)
                        await ctx.send(embed=embed)
                        await asyncio.sleep(1)
                else:
                    await ctx.send("뉴스를 가져올 수 없습니다.")
        except Exception as e:
            await ctx.send(f"오류가 발생했습니다: {e}")
    
    async def bot_status(self, ctx, target_channels: List[discord.TextChannel]):
        """봇의 현재 상태를 확인합니다."""
        cache_stats = self.cache_manager.get_cache_stats()
        embed = await self.embed_builder.create_status_embed(target_channels, self.config, cache_stats)
        await ctx.send(embed=embed)
    
    async def list_target_channels(self, ctx, target_channels: List[discord.TextChannel]):
        """american_stock 토픽을 가진 채널 목록을 보여줍니다."""
        embed = await self.embed_builder.create_channels_embed(target_channels)
        await ctx.send(embed=embed)
    
    async def cache_info(self, ctx):
        """캐시 정보를 보여줍니다."""
        cache_stats = self.cache_manager.get_cache_stats()
        embed = await self.embed_builder.create_cache_embed(cache_stats)
        await ctx.send(embed=embed)
    
    async def clear_cache(self, ctx):
        """캐시를 초기화합니다."""
        try:
            # 관리자 권한 확인
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ 이 명령어는 관리자만 사용할 수 있습니다.")
                return
            
            success = self.cache_manager.clear_cache()
            if success:
                embed = discord.Embed(
                    title="🗑️ 캐시 초기화",
                    description="캐시가 성공적으로 초기화되었습니다.",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ 캐시 초기화 실패",
                    description="캐시 초기화 중 오류가 발생했습니다.",
                    color=0xff0000
                )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ 오류 발생: {e}")
    
    async def backup_cache(self, ctx):
        """캐시를 백업합니다."""
        try:
            # 관리자 권한 확인
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ 이 명령어는 관리자만 사용할 수 있습니다.")
                return
            
            backup_path = self.cache_manager.backup_cache()
            if backup_path:
                embed = discord.Embed(
                    title="💾 캐시 백업",
                    description=f"캐시가 성공적으로 백업되었습니다.\n경로: `{backup_path}`",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ 캐시 백업 실패",
                    description="캐시 백업 중 오류가 발생했습니다.",
                    color=0xff0000
                )
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ 오류 발생: {e}")
    
    async def test_breaking_news(self, ctx):
        """속보 감지 테스트를 합니다."""
        test_text = ctx.message.content.replace('!test_breaking ', '')
        if not test_text:
            await ctx.send("테스트할 텍스트를 입력해주세요. 예: `!test_breaking 속보 테스트`")
            return
        
        # 임시 뉴스 객체 생성
        test_news = {
            'title': test_text,
            'content': test_text,
            'community_tags': [],
            '_source_api': 'news'  # 테스트는 News API로 간주
        }
        
        async with NewsAPIClient(
            self.config.API_URL,
            self.config.NEWS_API_URL,
            self.config.API_PAGE_SIZE, 
            self.config.BREAKING_NEWS_KEYWORDS
        ) as api_client:
            is_breaking = api_client.is_breaking_news(test_news)
            news_type = api_client.get_news_type(test_news)
            
            # 제목 정리 테스트
            clean_title = self.embed_builder._clean_news_title(test_text)
            
            embed = await self.embed_builder.create_test_embed(test_text, clean_title, is_breaking, news_type)
            await ctx.send(embed=embed)



