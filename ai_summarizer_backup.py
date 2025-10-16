import logging
from typing import List, Dict, Optional
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

try:
    from google import genai
    logger.info("Google genai 클라이언트 방식 사용")
except ImportError:
    import google.generativeai as genai
    logger.info("google-generativeai 라이브러리 방식 사용")

# 유명한 주식 종목 리스트 (우선순위 순)
FAMOUS_STOCKS = [
    # 메가테크 (FAANG+)
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NFLX', 'TSLA', 'NVDA',
    # 반도체
    'AMD', 'INTC', 'QCOM', 'AVGO', 'TXN', 'AMAT', 'LRCX', 'KLAC', 'MU', 'MRVL',
    # 금융
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP', 'V', 'MA',
    # 헬스케어
    'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
    # 에너지
    'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'MPC', 'VLO', 'PSX', 'KMI',
    # 기타 대형주
    'BRK.B', 'BRK.A', 'PG', 'KO', 'WMT', 'HD', 'VZ', 'T', 'DIS', 'NKE', 'MCD',
    'BA', 'CAT', 'IBM', 'GE', 'F', 'GM', 'UBER', 'LYFT', 'SPOT', 'SQ', 'PYPL',
    # 암호화폐 관련
    'COIN', 'MSTR', 'RIOT', 'MARA', 'HUT', 'BITF', 'CAN', 'ARB', 'BIT',
    # AI/클라우드
    'SNOW', 'CRWD', 'ZS', 'OKTA', 'DDOG', 'NET', 'PLTR', 'AI', 'C3AI'
]

# 유명한 주식이 포함된 뉴스인지 판단하는 함수
def contains_famous_stock(title: str, content: str = "") -> tuple:
    """제목이나 내용에 유명한 주식이 포함되어 있는지 확인합니다."""
    text = (title + " " + content).upper()
    
    for stock in FAMOUS_STOCKS:
        if stock in text:
            return True, stock
    
    return False, None

def get_stock_priority(title: str, content: str = "") -> int:
    """주식의 우선순위를 반환합니다 (낮은 숫자가 높은 우선순위)."""
    contains_stock, stock_symbol = contains_famous_stock(title, content)
    
    if contains_stock:
        # FAMOUS_STOCKS 리스트에서의 인덱스를 우선순위로 사용
        try:
            return FAMOUS_STOCKS.index(stock_symbol)
        except ValueError:
            return 999  # 리스트에 없는 경우 낮은 우선순위
    else:
        return 999  # 유명한 주식이 없으면 낮은 우선순위

class AISummarizer:
    def __init__(self, api_key: str):
        """Gemini AI 요약기를 초기화합니다."""
        self.model = None
        self.client = None
        
        if not api_key:
            logger.error("Gemini API 키가 제공되지 않았습니다.")
            return
            
        try:
            # 새로운 Google genai 클라이언트 방식 시도
            if hasattr(genai, 'Client'):
                self.client = genai.Client()
                logger.info("Google genai 클라이언트 초기화 성공")
                self.model = "gemini-2.5-flash"  # 기본 모델명
            else:
                # 기존 방식
                genai.configure(api_key=api_key)
                logger.info("Gemini API 설정 완료 (기존 방식)")
                
                # GenerativeModel 방식 시도
                if hasattr(genai, 'GenerativeModel'):
                    model_names = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.5-flash-lite']
                    for model_name in model_names:
                        try:
                            self.model = genai.GenerativeModel(model_name)
                            logger.info(f"Gemini 모델 초기화 성공: {model_name}")
                            break
                        except Exception as e:
                            logger.warning(f"모델 {model_name} 초기화 실패: {e}")
                            continue
                else:
                    # 구버전: 직접 generate_content 함수 사용
                    logger.info("GenerativeModel 클래스 없음, 직접 generate_content 사용")
                    self.model = "gemini-pro"  # 기본 모델명 저장
                    
        except Exception as e:
            logger.error(f"Gemini API 설정 실패: {e}")
            return
        
        if self.model is None and self.client is None:
            logger.error("모든 Gemini 모델 초기화 실패")
        else:
            logger.info("Gemini AI 요약기 초기화 완료")
        
    async def summarize_news(self, news_list: List[Dict]) -> Optional[str]:
        """뉴스 목록을 AI로 요약합니다."""
        if not news_list:
            return None
        
        if self.model is None:
            logger.error("Gemini AI 모델이 초기화되지 않았습니다. 기본 요약을 생성합니다.")
            return self._create_fallback_summary(news_list)
            
        try:
            # 뉴스 데이터를 텍스트로 변환
            news_text = self._format_news_for_ai(news_list)
            
            # AI 프롬프트 생성
            prompt = self._create_summary_prompt(news_text)
            
            # AI 요약 요청 (다양한 API 방식 지원)
            try:
                if self.client:
                    # 새로운 Google genai 클라이언트 방식
                    response = self.client.models.generate_content(
                        model=self.model, 
                        contents=prompt
                    )
                elif isinstance(self.model, str):
                    # 구버전: Client 객체를 통한 호출
                    try:
                        client = genai.Client()
                        response = client.models.generate_content(
                            model=self.model, 
                            contents=prompt
                        )
                    except Exception as e:
                        logger.error(f"구버전 Client 호출 실패: {e}")
                        return None
                else:
                    # 최신 버전 API 호출
                    response = self.model.generate_content(prompt)
                
                # 응답 텍스트 추출 (다양한 버전 호환)
                if self.client:
                    # 새로운 클라이언트 방식 응답 처리
                    if hasattr(response, 'text') and response.text:
                        logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 처리")
                        return response.text
                    else:
                        logger.warning("새로운 클라이언트 방식 응답이 비어있습니다.")
                        return None
                elif hasattr(response, 'text') and response.text:
                    logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 처리")
                    return response.text
                elif hasattr(response, 'parts') and response.parts:
                    # parts에서 텍스트 추출
                    text_content = ""
                    for part in response.parts:
                        if hasattr(part, 'text') and part.text:
                            text_content += part.text
                    if text_content:
                        logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 처리")
                        return text_content
                elif hasattr(response, 'candidates') and response.candidates:
                    # 구버전 응답 구조
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts'):
                                text_content = ""
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        text_content += part.text
                                if text_content:
                                    logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 처리")
                                    return text_content
                else:
                    logger.warning("AI 요약 응답이 비어있습니다.")
                    return None
                    
            except Exception as api_e:
                logger.error(f"Gemini API 호출 실패: {api_e}")
                return None
                
        except Exception as e:
            logger.error(f"AI 요약 중 오류 발생: {e}")
            return None
    
    async def summarize_news_with_market_data(self, news_list: List[Dict], market_data: Dict) -> Optional[str]:
        """뉴스 목록과 시장 데이터를 AI로 요약합니다."""
        if not news_list:
            return None
        
        if self.model is None:
            logger.error("Gemini AI 모델이 초기화되지 않았습니다. 기본 요약을 생성합니다.")
            return self._create_fallback_summary_with_market_data(news_list, market_data)
            
        try:
            # 뉴스 데이터를 텍스트로 변환
            news_text = self._format_news_for_ai(news_list)
            
            # 시장 데이터를 텍스트로 변환
            market_text = self._format_market_data_for_ai(market_data)
            
            # AI 프롬프트 생성 (시장 데이터 포함)
            prompt = self._create_enhanced_summary_prompt(news_text, market_text)
            
            # AI 요약 요청 (다양한 API 방식 지원)
            try:
                if self.client:
                    # 새로운 Google genai 클라이언트 방식
                    response = self.client.models.generate_content(
                        model=self.model, 
                        contents=prompt
                    )
                elif isinstance(self.model, str):
                    # 구버전: Client 객체를 통한 호출
                    try:
                        client = genai.Client()
                        response = client.models.generate_content(
                            model=self.model, 
                            contents=prompt
                        )
                    except Exception as e:
                        logger.error(f"구버전 Client 호출 실패: {e}")
                        return None
                else:
                    # 최신 버전 API 호출
                    response = self.model.generate_content(prompt)
                
                # 응답 텍스트 추출 (다양한 버전 호환)
                if hasattr(response, 'text') and response.text:
                    logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 + 시장 데이터 처리")
                    return response.text
                elif hasattr(response, 'parts') and response.parts:
                    # parts에서 텍스트 추출
                    text_content = ""
                    for part in response.parts:
                        if hasattr(part, 'text') and part.text:
                            text_content += part.text
                    if text_content:
                        logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 + 시장 데이터 처리")
                        return text_content
                elif hasattr(response, 'candidates') and response.candidates:
                    # 구버전 응답 구조
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts'):
                                text_content = ""
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        text_content += part.text
                                if text_content:
                                    logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 + 시장 데이터 처리")
                                    return text_content
                else:
                    logger.warning("AI 요약 응답이 비어있습니다.")
                    return None
                    
            except Exception as api_e:
                logger.error(f"Gemini API 호출 실패: {api_e}")
                return None
                
        except Exception as e:
            logger.error(f"AI 요약 중 오류 발생: {e}")
            return None
    
    def _format_news_for_ai(self, news_list: List[Dict]) -> str:
        """뉴스 목록을 AI가 이해하기 쉬운 형태로 변환합니다."""
        formatted_news = []
        
        for i, news in enumerate(news_list[:50], 1):  # 최대 50개만 처리
            title = news.get('title', '제목 없음')
            content = news.get('content', '내용 없음')
            author = news.get('author_name', 'Unknown')
            created_at = news.get('created_at', '')
            community_tags = news.get('community_tags', [])
            like_count = news.get('like_stats', {}).get('like_count', 0)
            view_count = news.get('view_count', 0)
            
            # 내용이 너무 길면 잘라내기
            if len(content) > 500:
                content = content[:500] + "..."
            
            # 태그 정보 추가
            tags_info = f"태그: {', '.join(community_tags)}" if community_tags else "태그: 없음"
            
            news_item = f"""
뉴스 {i}:
제목: {title}
작성자: {author} (좋아요: {like_count}, 조회수: {view_count})
시간: {created_at}
{tags_info}
내용: {content}
"""
            formatted_news.append(news_item)
        
        return "\n".join(formatted_news)
    
    def _create_summary_prompt(self, news_text: str) -> str:
        """AI 요약을 위한 프롬프트를 생성합니다."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        prompt = f"""
다음은 {current_time} 기준으로 수집된 주식/경제 관련 뉴스들입니다. 
이 뉴스들을 분석하여 1시간 주요 동향 리포트를 작성해주세요.

**요구사항:**
1. 상승 요인 뉴스 (긍정적 영향)
2. 하락 요인 뉴스 (부정적 영향)  
3. 섹터별 주요 이슈 (기술, 금융, 에너지, 헬스케어 등)
4. 핵심 키워드 (5개 이내)
5. 전체적인 시장 동향 평가

**형식:**
- 간결하고 명확한 문장 사용
- 각 섹션별로 구분하여 작성
- 전문 용어는 쉽게 설명
- 한국어로 작성

**뉴스 데이터:**
{news_text}

위 뉴스들을 바탕으로 종합적인 시장 동향 리포트를 작성해주세요.
"""
        return prompt
    
    def _format_market_data_for_ai(self, market_data: Dict) -> str:
        """시장 데이터를 AI가 이해하기 쉬운 형태로 변환합니다."""
        market_text = ""
        
        # 나스닥 데이터
        nasdaq = market_data.get('nasdaq', {})
        if nasdaq:
            market_text += f"""
📊 나스닥 실시간 정보:
- 현재가: {nasdaq.get('current_price', 'N/A')} {nasdaq.get('currency', 'USD')}
- 변동: {nasdaq.get('change', 'N/A')} ({nasdaq.get('change_percent', 'N/A')}%)
- 전일종가: {nasdaq.get('previous_close', 'N/A')}
- 시장상태: {nasdaq.get('market_state', 'N/A')}
"""
        
        # 공포탐욕지수 데이터
        fear_greed = market_data.get('fear_greed', {})
        if fear_greed:
            market_text += f"""
😨📈 공포탐욕지수:
- 지수: {fear_greed.get('value', 'N/A')}
- 분류: {fear_greed.get('classification', 'N/A')}
"""
        
        return market_text
    
    def _create_enhanced_summary_prompt(self, news_text: str, market_text: str) -> str:
        """시장 데이터를 포함한 향상된 AI 요약 프롬프트를 생성합니다."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        prompt = f"""
다음은 {current_time} 기준으로 수집된 주식/경제 관련 뉴스들과 실시간 시장 데이터입니다. 
이 정보들을 종합 분석하여 시장 동향 리포트를 작성해주세요.

**요구사항:**
1. 📈 상승 요인 뉴스 (긍정적 영향)
2. 📉 하락 요인 뉴스 (부정적 영향)  
3. 🎯 섹터별 주요 이슈 (기술, 금융, 에너지, 헬스케어, AI, 반도체 등)
4. 🔥 강세 테마 분석 (현재 주목받는 투자 테마)
   - 좋아요/조회수가 높은 뉴스들을 중심으로 분석
   - 반복적으로 언급되는 키워드나 섹터 식별
   - 커뮤니티 태그에서 트렌드 파악
   - 구체적인 투자 테마 3-5개 제시
5. 💡 핵심 키워드 (5개 이내)
6. 📊 시장 심리 분석 (공포탐욕지수와 뉴스 연관성)
7. 🎲 전체적인 시장 동향 평가 및 전망

**형식:**
- 간결하고 명확한 문장 사용
- 각 섹션별로 구분하여 작성
- 전문 용어는 쉽게 설명
- 한국어로 작성
- 이모지를 활용하여 가독성 향상
- **중요**: 유명한 대형주(FAANG+, TSLA, NVDA 등)가 포함된 뉴스를 우선적으로 언급

**실시간 시장 데이터:**
{market_text}

**뉴스 데이터:**
{news_text}

위 정보들을 종합 분석하여 투자자들이 참고할 수 있는 실용적인 시장 동향 리포트를 작성해주세요.
"""
        return prompt
    
    def _create_fallback_summary(self, news_list: List[Dict]) -> str:
        """AI가 작동하지 않을 때 기본 요약을 생성합니다."""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            summary = f"📊 **{current_time} 시장 동향 요약** (기본 요약)\n\n"
            
            # 최근 10개 뉴스 요약
            recent_news = news_list[:10]
            
            # 인기 뉴스 (유명한 주식 우선 + 좋아요/조회수 기준) 분석
            def sort_key(news):
                title = news.get('title', '')
                content = news.get('content', '')
                stock_priority = get_stock_priority(title, content)
                popularity = news.get('like_stats', {}).get('like_count', 0) + news.get('view_count', 0) * 0.1
                
                # 유명한 주식이 있으면 우선순위, 없으면 인기도 기준
                if stock_priority < 999:  # 유명한 주식이 있는 경우
                    return (0, stock_priority, popularity)  # 유명한 주식 우선
                else:
                    return (1, popularity, 0)  # 일반 뉴스는 인기도 기준
            
            popular_news = sorted(news_list, key=sort_key)[:5]
            
            summary += "🔥 **인기 뉴스 (트렌드 분석):**\n"
            for i, news in enumerate(popular_news, 1):
                title = news.get('title', '제목 없음')
                author = news.get('author_name', 'Unknown')
                like_count = news.get('like_stats', {}).get('like_count', 0)
                view_count = news.get('view_count', 0)
                summary += f"{i}. {title} (by {author}) 👍{like_count} 👁️{view_count}\n"
            
            # 태그 분석으로 트렌드 파악
            all_tags = []
            for news in news_list:
                tags = news.get('community_tags', [])
                all_tags.extend(tags)
            
            if all_tags:
                tag_counts = Counter(all_tags)
                top_tags = tag_counts.most_common(5)
                summary += f"\n🏷️ **인기 키워드/태그:**\n"
                for tag, count in top_tags:
                    summary += f"• {tag} ({count}회 언급)\n"
            
            summary += f"\n📰 **전체 뉴스 헤드라인 (유명한 주식 우선):**\n"
            # 전체 뉴스도 유명한 주식 우선순위로 정렬
            sorted_all_news = sorted(news_list, key=lambda x: (
                get_stock_priority(x.get('title', ''), x.get('content', ''))
            ))
            for i, news in enumerate(sorted_all_news[:10], 1):
                title = news.get('title', '제목 없음')
                author = news.get('author_name', 'Unknown')
                # 유명한 주식이 포함된 경우 표시
                contains_stock, stock_symbol = contains_famous_stock(title, news.get('content', ''))
                stock_info = f" [{stock_symbol}]" if contains_stock else ""
                summary += f"{i}. {title} (by {author}){stock_info}\n"
            
            summary += f"\n📈 **분석된 뉴스 수**: {len(news_list)}개\n"
            summary += "⚠️ **참고**: AI 분석이 일시적으로 불가능하여 기본 요약을 제공합니다.\n"
            
            # Discord 필드 길이 제한 (1024자)
            if len(summary) > 1024:
                summary = summary[:1020] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"기본 요약 생성 중 오류: {e}")
            return f"📊 시장 동향 요약 (오류 발생)\n\n분석된 뉴스: {len(news_list)}개\nAI 분석 서비스가 일시적으로 불가능합니다."
    
    def _create_fallback_summary_with_market_data(self, news_list: List[Dict], market_data: Dict) -> str:
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
            
            # 인기 뉴스 (유명한 주식 우선 + 좋아요/조회수 기준) 분석
            def sort_key_market(news):
                title = news.get('title', '')
                content = news.get('content', '')
                stock_priority = get_stock_priority(title, content)
                popularity = news.get('like_stats', {}).get('like_count', 0) + news.get('view_count', 0) * 0.1
                
                # 유명한 주식이 있으면 우선순위, 없으면 인기도 기준
                if stock_priority < 999:  # 유명한 주식이 있는 경우
                    return (0, stock_priority, popularity)  # 유명한 주식 우선
                else:
                    return (1, popularity, 0)  # 일반 뉴스는 인기도 기준
            
            popular_news = sorted(news_list, key=sort_key_market)[:5]
            
            summary += "\n🔥 **인기 뉴스 (트렌드 분석):**\n"
            for i, news in enumerate(popular_news, 1):
                title = news.get('title', '제목 없음')
                author = news.get('author_name', 'Unknown')
                like_count = news.get('like_stats', {}).get('like_count', 0)
                view_count = news.get('view_count', 0)
                summary += f"{i}. {title} (by {author}) 👍{like_count} 👁️{view_count}\n"
            
            # 태그 분석으로 트렌드 파악
            all_tags = []
            for news in news_list:
                tags = news.get('community_tags', [])
                all_tags.extend(tags)
            
            if all_tags:
                tag_counts = Counter(all_tags)
                top_tags = tag_counts.most_common(5)
                summary += f"\n🏷️ **인기 키워드/태그:**\n"
                for tag, count in top_tags:
                    summary += f"• {tag} ({count}회 언급)\n"
            
            summary += "\n📰 **전체 뉴스 헤드라인 (유명한 주식 우선):**\n"
            # 전체 뉴스도 유명한 주식 우선순위로 정렬
            sorted_all_news = sorted(news_list, key=lambda x: (
                get_stock_priority(x.get('title', ''), x.get('content', ''))
            ))
            for i, news in enumerate(sorted_all_news[:10], 1):
                title = news.get('title', '제목 없음')
                author = news.get('author_name', 'Unknown')
                # 유명한 주식이 포함된 경우 표시
                contains_stock, stock_symbol = contains_famous_stock(title, news.get('content', ''))
                stock_info = f" [{stock_symbol}]" if contains_stock else ""
                summary += f"{i}. {title} (by {author}){stock_info}\n"
            
            summary += f"\n📈 **분석된 뉴스 수**: {len(news_list)}개\n"
            summary += "⚠️ **참고**: AI 분석이 일시적으로 불가능하여 기본 요약을 제공합니다.\n"
            
            # Discord 필드 길이 제한 (1024자)
            if len(summary) > 1024:
                summary = summary[:1020] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"기본 요약 생성 중 오류: {e}")
            return f"📊 시장 동향 요약 (오류 발생)\n\n분석된 뉴스: {len(news_list)}개\nAI 분석 서비스가 일시적으로 불가능합니다."
