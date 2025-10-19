import re
from datetime import datetime
from typing import Dict
import discord

from news.api_client import NewsAPIClient

class EmbedBuilder:
    """Discord 임베드 생성을 담당하는 클래스"""
    
    def __init__(self):
        pass
    
    async def create_news_embed(self, news: Dict, api_client: NewsAPIClient, news_type: str, is_breaking: bool, is_important: bool, allow_thumbnail: bool = True) -> discord.Embed:
        """뉴스 임베드를 생성합니다."""
        # 색상 설정
        if is_breaking:
            color = 0xff0000  # 빨간색 (속보)
            emoji = "⚡"
        elif is_important:
            color = 0xff6600  # 주황색 (중요)
            emoji = "🔥"
        else:
            color = 0x00ff00  # 초록색 (일반)
            emoji = "📈"
        
        # 제목에서 속보/중요뉴스 키워드 제거하고 깔끔한 헤드라인만 표시
        clean_title = self._clean_news_title(news.get('title', '제목 없음'))
        
        embed = discord.Embed(
            title=f"{emoji} {clean_title}",
            description=news.get('content', '내용 없음')[:1000] + ('...' if len(news.get('content', '')) > 1000 else ''),
            color=color,
            timestamp=datetime.now()
        )
        
        # 작성자 정보
        author_name = news.get('author_name', 'Unknown')
        author_points = news.get('author_points', 0)
        embed.set_author(name=f"{author_name} (포인트: {author_points:,})")
        
        # 뉴스 타입 표시
        embed.add_field(name="📋 분류", value=news_type, inline=True)
        
        # 통계 정보
        like_count = news.get('like_stats', {}).get('like_count', 0)
        view_count = news.get('view_count', 0)
        comment_count = news.get('comment_count', 0)
        
        embed.add_field(name="📊 통계", value=f"👍 {like_count} | 👁️ {view_count} | 💬 {comment_count}", inline=True)
        
        # 생성 시간
        created_at = news.get('created_at', '')
        if created_at:
            embed.add_field(name="📅 작성 시간", value=created_at[:19], inline=True)
        
        # 커뮤니티 태그
        community_tags = news.get('community_tags', [])
        if community_tags:
            tags_text = ', '.join(community_tags[:3])  # 최대 3개 태그만 표시
            embed.add_field(name="🏷️ 태그", value=tags_text, inline=False)
        
        # 상세 링크
        source_api = news.get('_source_api', 'community')
        news_url = api_client.format_news_url(news.get('id', ''), source_api)
        embed.add_field(name="🔗 상세 보기", value=f"[링크]({news_url})", inline=False)
        
        # 썸네일 (유효한 URL만 설정)
        if allow_thumbnail:
            thumbnail_url = news.get('thumbnail')
            normalized = self._normalize_url(thumbnail_url)
            if normalized:
                embed.set_thumbnail(url=normalized)
        
        # 푸터 설정
        if is_breaking:
            embed.set_footer(text="⚡ 속보 - 핀 고정됨")
        elif is_important:
            embed.set_footer(text="🔥 중요 뉴스 - 핀 고정됨")
        else:
            embed.set_footer(text="📈 일반 뉴스")
        
        return embed
    
    def _clean_news_title(self, title: str) -> str:
        """뉴스 제목에서 속보/중요뉴스 키워드를 제거하고 깔끔하게 정리합니다."""
        if not title:
            return "제목 없음"
        
        # 제거할 키워드들 (대소문자 구분 없이)
        keywords_to_remove = [
            '속보', '긴급', '중요', '특보', '긴급속보', '특별속보',
            'BREAKING', 'URGENT', 'IMPORTANT', 'ALERT'
        ]
        
        # [속보], (속보), 【속보】 등의 패턴 제거
        patterns_to_remove = [
            r'\[속보\]', r'\(속보\)', r'【속보】', r'\[긴급\]', r'\(긴급\)', r'【긴급】',
            r'\[중요\]', r'\(중요\)', r'【중요】', r'\[특보\]', r'\(특보\)', r'【특보】',
            r'\[BREAKING\]', r'\(BREAKING\)', r'\[URGENT\]', r'\(URGENT\)',
            r'속보:', r'긴급:', r'중요:', r'특보:', r'BREAKING:', r'URGENT:'
        ]
        
        clean_title = title
        
        # 패턴 제거
        for pattern in patterns_to_remove:
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
        
        # 키워드 제거 (단어 경계 고려)
        for keyword in keywords_to_remove:
            # 단어 경계를 고려하여 키워드 제거
            pattern = r'\b' + re.escape(keyword) + r'\b'
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
        
        # 여러 공백을 하나로 정리하고 앞뒤 공백 제거
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        # 콜론이나 대시 뒤의 공백 정리
        clean_title = re.sub(r'^[:\-\s]+', '', clean_title)
        
        return clean_title if clean_title else "제목 없음"
    
    async def create_status_embed(self, target_channels, config, cache_stats) -> discord.Embed:
        """봇 상태 임베드를 생성합니다."""
        embed = discord.Embed(
            title="🤖 봇 상태",
            color=0x00ff00
        )
        
        # 타겟 채널 정보
        if target_channels:
            channel_list = []
            for channel in target_channels[:5]:  # 최대 5개만 표시
                channel_list.append(f"#{channel.name} ({channel.guild.name})")
            channel_text = "\n".join(channel_list)
            if len(target_channels) > 5:
                channel_text += f"\n... 외 {len(target_channels) - 5}개 채널"
        else:
            channel_text = "american_stock 토픽을 가진 채널 없음"
        
        embed.add_field(name="타겟 채널 (american_stock)", value=channel_text, inline=False)
        embed.add_field(name="업데이트 간격", value=f"{config.UPDATE_INTERVAL}초", inline=True)
        embed.add_field(name="속보 키워드", value=f"{', '.join(config.BREAKING_NEWS_KEYWORDS)}", inline=False)
        embed.add_field(name="중요 뉴스 기준", value=f"{config.IMPORTANT_LIKE_THRESHOLD} 좋아요", inline=True)
        
        # 캐시 통계 정보 추가
        embed.add_field(name="처리된 뉴스", value=f"{cache_stats['total_processed_news']}개", inline=True)
        embed.add_field(name="캐시된 뉴스 ID", value=f"{cache_stats['unique_news_ids']}개", inline=True)
        embed.add_field(name="마지막 업데이트", value=cache_stats['last_update'][:19] if cache_stats['last_update'] else "없음", inline=True)
        embed.add_field(name="봇 상태", value="🟢 실행 중", inline=True)
        
        return embed
    
    async def create_channels_embed(self, target_channels) -> discord.Embed:
        """채널 목록 임베드를 생성합니다."""
        if not target_channels:
            embed = discord.Embed(
                title="📋 타겟 채널 목록",
                description="american_stock 토픽을 가진 채널이 없습니다.",
                color=0xff6600
            )
            embed.add_field(
                name="채널 토픽 설정 방법", 
                value="1. 채널 설정으로 이동\n2. 채널 토픽에 'american_stock' 추가\n3. 저장", 
                inline=False
            )
        else:
            embed = discord.Embed(
                title="📋 타겟 채널 목록",
                description=f"american_stock 토픽을 가진 {len(target_channels)}개 채널",
                color=0x00ff00
            )
            
            for i, channel in enumerate(target_channels, 1):
                embed.add_field(
                    name=f"{i}. #{channel.name}",
                    value=f"서버: {channel.guild.name}\n토픽: {channel.topic[:100]}{'...' if len(channel.topic) > 100 else ''}",
                    inline=False
                )
        
        return embed
    
    async def create_cache_embed(self, cache_stats) -> discord.Embed:
        """캐시 정보 임베드를 생성합니다."""
        embed = discord.Embed(
            title="💾 캐시 정보",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📊 처리 통계", 
            value=f"총 처리된 뉴스: {cache_stats['total_processed_news']}개\n고유 뉴스 ID: {cache_stats['unique_news_ids']}개", 
            inline=False
        )
        
        embed.add_field(
            name="🕒 시간 정보", 
            value=f"마지막 업데이트: {cache_stats['last_update'][:19] if cache_stats['last_update'] else '없음'}\n마지막 API 응답: {cache_stats['last_response_time'][:19] if cache_stats['last_response_time'] else '없음'}", 
            inline=False
        )
        
        embed.add_field(
            name="📁 캐시 파일", 
            value=f"뉴스 캐시: `{cache_stats['cache_files']['news_cache']}`\n응답 캐시: `{cache_stats['cache_files']['last_response']}`", 
            inline=False
        )
        
        embed.add_field(
            name="📈 마지막 응답", 
            value=f"뉴스 개수: {cache_stats['last_response_news_count']}개", 
            inline=True
        )
        
        return embed
    
    async def create_test_embed(self, test_text: str, clean_title: str, is_breaking: bool, news_type: str) -> discord.Embed:
        """속보 감지 테스트 임베드를 생성합니다."""
        embed = discord.Embed(
            title="🧪 속보 감지 테스트",
            color=0xff0000 if is_breaking else 0x00ff00
        )
        embed.add_field(name="입력 텍스트", value=test_text, inline=False)
        embed.add_field(name="정리된 제목", value=clean_title, inline=False)
        embed.add_field(name="속보 여부", value="⚡ 속보 감지됨" if is_breaking else "📈 일반 뉴스", inline=True)
        embed.add_field(name="뉴스 타입", value=news_type, inline=True)
        
        return embed

    def _normalize_url(self, url: str) -> str:
        """상대 경로를 절대 URL로 변환하고, 잘못된 값은 None으로 반환합니다."""
        if not url or not isinstance(url, str):
            return None
        u = url.strip()
        if u.startswith('http://') or u.startswith('https://'):
            return u
        if u.startswith('/'):
            # SaveTicker API의 상대 경로를 절대 경로로 변환
            return 'https://api.saveticker.com' + u
        return None
