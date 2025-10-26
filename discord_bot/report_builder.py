import discord
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class ReportBuilder:
    def __init__(self):
        """리포트 임베드 빌더를 초기화합니다."""
        pass
    
    def create_report_embed(self, ai_summary: str, news_count: int, market_data: Dict = None, headlines: str = "") -> discord.Embed:
        """AI 요약 결과를 Discord 임베드로 변환합니다."""
        try:
            current_time = datetime.now()
            
            # 리포트 임베드 생성
            title = "🤖 AI 시장 동향 리포트"
            if market_data:
                nasdaq = market_data.get('nasdaq', {})
                if nasdaq and nasdaq.get('change', 0) != 0:
                    change_percent = nasdaq.get('change_percent', 0)
                    if change_percent > 0:
                        title = f"📈 AI 시장 리포트 - 나스닥 +{change_percent:.2f}%"
                    else:
                        title = f"📉 AI 시장 리포트 - 나스닥 {change_percent:.2f}%"
            
            embed = discord.Embed(
                title=title,
                description="Community 뉴스 AI 요약 + 실시간 시장 분석",
                color=0x00bfff,  # 딥 스카이 블루
                timestamp=current_time
            )
            
            # 요약 내용 설정 (Discord 필드 최대 길이: 2000자로 확장)
            if len(ai_summary) > 2000:
                ai_summary = ai_summary[:1997] + "..."
            
            embed.add_field(
                name="📊 1시간 주요 동향",
                value=ai_summary,
                inline=False
            )

            # 주요 헤드라인 (디스코드 필드 최대 길이: 1024자)
            if headlines:
                truncated_headlines = headlines if len(headlines) <= 1024 else headlines[:1020] + "..."
                embed.add_field(
                    name="📰 주요 헤드라인",
                    value=truncated_headlines,
                    inline=False
                )
            
            # 시장 데이터 정보 추가
            market_info = ""
            if market_data:
                nasdaq = market_data.get('nasdaq', {})
                fear_greed = market_data.get('fear_greed', {})
                
                if nasdaq:
                    change_emoji = "📈" if nasdaq.get('change', 0) >= 0 else "📉"
                    stale_suffix = " (stale)" if nasdaq.get('stale') else ""
                    market_info += f"{change_emoji} **나스닥**: {nasdaq.get('current_price', 'N/A')} ({nasdaq.get('change_percent', 'N/A')}%){stale_suffix}\n"
                
                if fear_greed:
                    fg_value = fear_greed.get('value', 0)
                    if fg_value >= 75:
                        fg_emoji = "😍"
                    elif fg_value >= 55:
                        fg_emoji = "😊"
                    elif fg_value >= 45:
                        fg_emoji = "😐"
                    elif fg_value >= 25:
                        fg_emoji = "😰"
                    else:
                        fg_emoji = "😱"
                    
                    fg_stale_suffix = " (stale)" if fear_greed.get('stale') else ""
                    market_info += f"{fg_emoji} **공포탐욕지수**: {fg_value} ({fear_greed.get('classification', 'N/A')}){fg_stale_suffix}\n"
            
            # 시장 정보 필드 길이 제한
            if len(market_info) > 1024:
                market_info = market_info[:1020] + "..."
            
            # 강화된 투자자 정보 생성
            investor_info = self._create_enhanced_investor_info(market_data, news_count, current_time)
            
            # 투자자 정보 필드 길이 제한
            if len(investor_info) > 1024:
                investor_info = investor_info[:1020] + "..."
            
            embed.add_field(
                name="💼 투자자 정보",
                value=investor_info,
                inline=True
            )
            
            # 시장 정보 (간소화)
            embed.add_field(
                name="📊 시장 정보",
                value=market_info if market_info else "시장 데이터 없음",
                inline=True
            )
            
            # 푸터 설정
            embed.set_footer(
                text="🤖 AI 요약 | 1시간 주기 리포트",
                icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"  # 로봇 이모지 (선택사항)
            )
            
            # 썸네일 설정 (선택사항)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1234567890123456789/1234567890123456789/chart.png")
            
            return embed
            
        except Exception as e:
            logger.error(f"리포트 임베드 생성 중 오류 발생: {e}")
            # 오류 발생 시 기본 임베드 반환
            return self._create_error_embed(str(e))
    
    def _create_error_embed(self, error_message: str) -> discord.Embed:
        """오류 발생 시 표시할 기본 임베드를 생성합니다."""
        embed = discord.Embed(
            title="⚠️ 리포트 생성 오류",
            description=f"AI 리포트 생성 중 오류가 발생했습니다.\n오류: {error_message}",
            color=0xff0000,  # 빨간색
            timestamp=datetime.now()
        )
        
        embed.set_footer(text="다음 시간에 다시 시도됩니다.")
        return embed
    
    def create_test_report_embed(self) -> discord.Embed:
        """테스트용 리포트 임베드를 생성합니다."""
        embed = discord.Embed(
            title="🧪 테스트 리포트",
            description="AI 리포트 시스템 테스트",
            color=0x00ff00,  # 초록색
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 테스트 내용",
            value="• 시스템 정상 작동 확인\n"
                  "• AI 연동 테스트 완료\n"
                  "• 임베드 생성 테스트 완료",
            inline=False
        )
        
        embed.set_footer(text="🧪 테스트 모드")
        return embed
    
    def _create_enhanced_investor_info(self, market_data: Dict, news_count: int, current_time) -> str:
        """강화된 투자자 정보를 생성합니다."""
        investor_info = ""
        
        # 시장 상황 분석
        nasdaq = market_data.get('nasdaq', {}) if market_data else {}
        fear_greed = market_data.get('fear_greed', {}) if market_data else {}
        
        # 시장 심리 분석
        if fear_greed:
            fg_value = fear_greed.get('value', 0)
            if fg_value >= 75:
                market_sentiment = "😍 극도 탐욕 (과열 주의)"
                advice = "고점 매도 고려"
            elif fg_value >= 55:
                market_sentiment = "😊 탐욕 (상승 추세)"
                advice = "적정 매수 기회"
            elif fg_value >= 45:
                market_sentiment = "😐 중립 (보합세)"
                advice = "관망 또는 분할 매수"
            elif fg_value >= 25:
                market_sentiment = "😰 공포 (하락 압력)"
                advice = "저점 매수 기회"
            else:
                market_sentiment = "😱 극도 공포 (과매도)"
                advice = "대량 매수 기회"
            
            investor_info += f"🎯 **시장 심리**: {market_sentiment}\n"
            investor_info += f"💡 **투자 조언**: {advice}\n"
        
        # 나스닥 분석 및 리스크 평가
        if nasdaq:
            change_percent = nasdaq.get('change_percent', 0)
            
            if change_percent > 1:
                trend = "📈 강한 상승세"
                risk_level = "🟡 중간"
            elif change_percent > 0:
                trend = "📈 상승세"
                risk_level = "🟢 낮음"
            elif change_percent > -1:
                trend = "📊 보합세"
                risk_level = "🟡 중간"
            else:
                trend = "📉 하락세"
                risk_level = "🟠 높음"
            
            investor_info += f"📊 **나스닥 추세**: {trend}\n"
            investor_info += f"⚠️ **리스크**: {risk_level}\n"
        
        # 시장 강도 분석 (변동률 + 심리 지표 조합)
        if nasdaq and fear_greed:
            change_percent = nasdaq.get('change_percent', 0)
            fg_value = fear_greed.get('value', 50)
            
            # 강도 계산: 변동률 절댓값 + 심리 지표
            strength_score = abs(change_percent) + (fg_value / 10)
            
            if strength_score > 15:
                market_strength = "💪 매우 강세"
            elif strength_score > 10:
                market_strength = "📈 강세"
            elif strength_score > 5:
                market_strength = "📊 보합"
            elif strength_score > 2:
                market_strength = "📉 약세"
            else:
                market_strength = "⚠️ 매우 약세"
            
            investor_info += f"🎯 **시장 강도**: {market_strength}\n"
            
            # 변동률 크기별 시장 안정성 판단
            volatility = abs(change_percent)
            if volatility > 2:
                stability = "🔴 불안정"
            elif volatility > 1:
                stability = "🟡 보통"
            else:
                stability = "🟢 안정"
            
            investor_info += f"📊 **시장 안정성**: {stability}\n"
        
        # 업데이트 시간
        investor_info += f"📅 **업데이트**: {current_time.strftime('%H:%M')}\n"
        
        return investor_info
