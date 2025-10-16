import discord
from discord.ext import commands, tasks
import logging
from typing import List
from google import genai

from config import Config
from cache_manager import NewsCacheManager
from embed_builder import EmbedBuilder
from image_handler import ImageHandler
from news_handler import NewsHandler
from command_handler import CommandHandler
from report_scheduler import ReportScheduler

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce verbosity from google-genai library
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("google_genai.models").setLevel(logging.WARNING)

class StockNewsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # message_content intent는 privileged intent이므로 제거
        # 우리 봇은 메시지 내용을 읽을 필요가 없음
        super().__init__(command_prefix='!', intents=intents)
        
        self.config = Config()
        self.config.validate()
        
        # 모듈 초기화
        self.cache_manager = NewsCacheManager()
        self.embed_builder = EmbedBuilder()
        self.image_handler = ImageHandler()
        self.news_handler = NewsHandler(self.config, self.cache_manager)
        self.command_handler = CommandHandler(self.config, self.cache_manager, self.embed_builder, self.news_handler)
        self.report_scheduler = None  # on_ready에서 초기화
        
    async def on_ready(self):
        logger.info(f'{self.user}로 로그인했습니다!')
        logger.info(f'속보 키워드: {self.config.BREAKING_NEWS_KEYWORDS}')
        
        # american_stock 토픽을 가진 채널들 찾기
        target_channels = await self.find_channels_by_topic('american_stock')
        logger.info(f'american_stock 토픽을 가진 채널 {len(target_channels)}개를 찾았습니다.')
        
        # 리포트 스케줄러 초기화
        self.report_scheduler = ReportScheduler(self.config, target_channels, self.embed_builder)
        
        # 뉴스 체크 작업 시작 (NEWS_API_URL만 처리)
        if not self.check_news.is_running():
            self.check_news.start()
        
        # 리포트 스케줄러 시작 (Community 뉴스 AI 요약)
        self.report_scheduler.start_scheduler()
        logger.info("뉴스 체크 및 리포트 스케줄러가 시작되었습니다.")
    
    async def find_channels_by_topic(self, topic: str) -> List[discord.TextChannel]:
        """특정 토픽을 가진 텍스트 채널들을 찾습니다."""
        target_channels = []
        
        for guild in self.guilds:
            for channel in guild.text_channels:
                # 채널 토픽이 설정되어 있고, 지정된 토픽을 포함하는 경우
                if channel.topic and topic in channel.topic:
                    target_channels.append(channel)
                    logger.info(f'타겟 채널 발견: {guild.name} - #{channel.name}')
        
        return target_channels
    
    async def on_command_error(self, ctx, error):
        logger.error(f'명령어 오류: {error}')
    
    @tasks.loop(seconds=Config.UPDATE_INTERVAL)
    async def check_news(self):
        """주기적으로 뉴스를 체크하고 디스코드에 전송합니다."""
        try:
            # american_stock 토픽을 가진 채널들 찾기
            target_channels = await self.find_channels_by_topic('american_stock')
            if not target_channels:
                logger.warning("american_stock 토픽을 가진 채널을 찾을 수 없습니다.")
                return
            
            # 뉴스 처리 및 전송
            await self.news_handler.process_and_send_news(target_channels, self.embed_builder, self.image_handler)
                
        except Exception as e:
            logger.error(f"뉴스 체크 중 오류 발생: {e}")
    
    # 명령어들 - 각각 모듈화된 핸들러로 위임
    @commands.command(name='news')
    async def manual_news_check(self, ctx):
        """수동으로 뉴스를 체크합니다."""
        await self.command_handler.manual_news_check(ctx)
    
    @commands.command(name='status')
    async def bot_status(self, ctx):
        """봇의 현재 상태를 확인합니다."""
        target_channels = await self.find_channels_by_topic('american_stock')
        await self.command_handler.bot_status(ctx, target_channels)
    
    @commands.command(name='channels')
    async def list_target_channels(self, ctx):
        """american_stock 토픽을 가진 채널 목록을 보여줍니다."""
        target_channels = await self.find_channels_by_topic('american_stock')
        await self.command_handler.list_target_channels(ctx, target_channels)
    
    @commands.command(name='cache')
    async def cache_info(self, ctx):
        """캐시 정보를 보여줍니다."""
        await self.command_handler.cache_info(ctx)
    
    @commands.command(name='clear_cache')
    async def clear_cache(self, ctx):
        """캐시를 초기화합니다."""
        await self.command_handler.clear_cache(ctx)
    
    @commands.command(name='backup_cache')
    async def backup_cache(self, ctx):
        """캐시를 백업합니다."""
        await self.command_handler.backup_cache(ctx)
    
    @commands.command(name='test_breaking')
    async def test_breaking_news(self, ctx):
        """속보 감지 테스트를 합니다."""
        await self.command_handler.test_breaking_news(ctx)

def main():
    bot = StockNewsBot()
    bot.run(bot.config.DISCORD_TOKEN)

if __name__ == "__main__":
    main()