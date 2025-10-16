"""
AI 실패 시 기본 요약 생성 모듈
"""
import logging
from typing import List, Dict
from datetime import datetime
from stock_utils import sort_news_by_stock_priority, get_popular_tags, format_news_with_stock_info
from google import genai

logger = logging.getLogger(__name__)

class FallbackSummarizer:
    """AI가 작동하지 않을 때 기본 요약을 생성하는 클래스"""
    
    @staticmethod
    def create_fallback_summary(news_list: List[Dict]) -> str:
        """AI가 작동하지 않을 때 기본 요약을 생성합니다."""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            summary = f"📊 **{current_time} 시장 동향 요약** (기본 요약)\n\n"
            
            # 인기 뉴스 (유명한 주식 우선 + 좋아요/조회수 기준) 분석
            popular_news = sort_news_by_stock_priority(news_list)[:5]
            
            summary += "🔥 **인기 뉴스 (트렌드 분석):**\n"
            for i, news in enumerate(popular_news, 1):
                title = news.get('title', '제목 없음')
                author = news.get('author_name', 'Unknown')
                like_count = news.get('like_stats', {}).get('like_count', 0)
                view_count = news.get('view_count', 0)
                summary += f"{i}. {title} (by {author}) 👍{like_count} 👁️{view_count}\n"
            
            # 태그 분석으로 트렌드 파악
            top_tags = get_popular_tags(news_list, 5)
            if top_tags:
                summary += f"\n🏷️ **인기 키워드/태그:**\n"
                for tag, count in top_tags:
                    summary += f"• {tag} ({count}회 언급)\n"
            
            summary += f"\n📰 **전체 뉴스 헤드라인 (유명한 주식 우선):**\n"
            summary += format_news_with_stock_info(news_list, 10)
            
            summary += f"\n📈 **분석된 뉴스 수**: {len(news_list)}개\n"
            summary += "⚠️ **참고**: AI 분석이 일시적으로 불가능하여 기본 요약을 제공합니다.\n"
            
            # Discord 필드 길이 제한 (1024자)
            if len(summary) > 1024:
                summary = summary[:1020] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"기본 요약 생성 중 오류: {e}")
            return f"📊 시장 동향 요약 (오류 발생)\n\n분석된 뉴스: {len(news_list)}개\nAI 분석 서비스가 일시적으로 불가능합니다."
    
    @staticmethod
    def create_fallback_summary_with_market_data(news_list: List[Dict], market_data: Dict) -> str:
        """AI가 작동하지 않을 때 시장 데이터를 포함한 기본 요약을 생성합니다."""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            summary = f"📊 **{current_time} 시장 동향 요약** (기본 요약)\n\n"
            
            # 시장 데이터 정보 추가
            nasdaq = market_data.get('nasdaq', {})
            fear_greed = market_data.get('fear_greed', {})
            
            if nasdaq:
                change_emoji = "📈" if nasdaq.get('change', 0) >= 0 else "📉"
                stale_suffix = " (캐시 데이터)" if nasdaq.get('stale') else ""
                summary += f"**📊 나스닥**: {nasdaq.get('current_price', 'N/A')} ({nasdaq.get('change_percent', 'N/A')}%){stale_suffix}\n"
            
            if fear_greed:
                fg_value = fear_greed.get('value', 0)
                fg_emoji = "😍" if fg_value >= 75 else "😊" if fg_value >= 55 else "😐" if fg_value >= 45 else "😰" if fg_value >= 25 else "😱"
                stale_suffix = " (캐시 데이터)" if fear_greed.get('stale') else ""
                summary += f"**{fg_emoji} 공포탐욕지수**: {fg_value} ({fear_greed.get('classification', 'N/A')}){stale_suffix}\n"
            
            # 인기 뉴스 분석
            popular_news = sort_news_by_stock_priority(news_list)[:5]
            
            summary += "\n🔥 **인기 뉴스 (트렌드 분석):**\n"
            for i, news in enumerate(popular_news, 1):
                title = news.get('title', '제목 없음')
                author = news.get('author_name', 'Unknown')
                like_count = news.get('like_stats', {}).get('like_count', 0)
                view_count = news.get('view_count', 0)
                summary += f"{i}. {title} (by {author}) 👍{like_count} 👁️{view_count}\n"
            
            # 태그 분석
            top_tags = get_popular_tags(news_list, 5)
            if top_tags:
                summary += f"\n🏷️ **인기 키워드/태그:**\n"
                for tag, count in top_tags:
                    summary += f"• {tag} ({count}회 언급)\n"
            
            summary += "\n📰 **전체 뉴스 헤드라인 (유명한 주식 우선):**\n"
            summary += format_news_with_stock_info(news_list, 10)
            
            summary += f"\n📈 **분석된 뉴스 수**: {len(news_list)}개\n"
            summary += "⚠️ **참고**: AI 분석이 일시적으로 불가능하여 기본 요약을 제공합니다.\n"
            
            # Discord 필드 길이 제한 (1024자)
            if len(summary) > 1024:
                summary = summary[:1020] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"기본 요약 생성 중 오류: {e}")
            return f"📊 시장 동향 요약 (오류 발생)\n\n분석된 뉴스: {len(news_list)}개\nAI 분석 서비스가 일시적으로 불가능합니다."

