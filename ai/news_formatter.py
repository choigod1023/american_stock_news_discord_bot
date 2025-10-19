"""
뉴스 포맷팅 관련 모듈
"""
from typing import List, Dict
from datetime import datetime
from core.stock_utils import sort_news_by_stock_priority, get_popular_tags, format_news_with_stock_info

class NewsFormatter:
    """뉴스 포맷팅 클래스"""
    
    @staticmethod
    def format_news_for_ai(news_list: List[Dict], max_items: int = 50) -> str:
        """뉴스 목록을 AI가 이해하기 쉬운 형태로 변환합니다."""
        formatted_news = []
        
        for i, news in enumerate(news_list[:max_items], 1):
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
    
    @staticmethod
    def format_market_data_for_ai(market_data: Dict) -> str:
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
    
    @staticmethod
    def create_summary_prompt(news_text: str) -> str:
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
    
    @staticmethod
    def create_enhanced_summary_prompt(news_text: str, market_text: str) -> str:
        """시장 데이터를 포함한 간결한 AI 요약 프롬프트를 생성합니다."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        prompt = f"""
{current_time} 기준 주식/경제 뉴스와 시장 데이터를 분석하여 **Discord 임베드에 들어갈 간결한 요약**을 작성하세요.

**중요 제약사항:**
- 전체 요약을 **800자 이내**로 제한하세요
- Discord 임베드 필드 길이 제한(1024자)을 고려하세요
- 불필요한 수식어와 장황한 설명을 피하세요

**요구사항 (간결하게):**
1. **시장 현황** (1-2문장): 나스닥 방향성 + 공포탐욕지수 해석
2. **주요 이슈** (2-3개): 가장 중요한 상승/하락 요인만 간단히
3. **핵심 키워드** (3-5개): 현재 시장을 움직이는 주요 키워드

**형식 (중요!):**
- 각 섹션 사이에 **줄바꿈**을 넣어 가독성을 높이세요
- 짧고 명확한 문장 사용
- 이모지 최소화 (필요시에만)
- 전문 용어는 쉬운 말로 설명
- 한국어로 작성
- **중복 방지**: 유사한 뉴스는 통합

**출력 형식 예시:**
시장 현황: [나스닥 정보 + 공포탐욕지수 해석]

주요 이슈:
- [이슈 1]
- [이슈 2]
- [이슈 3]

핵심 키워드: [키워드1, 키워드2, 키워드3, 키워드4, 키워드5]

**시장 데이터:**
{market_text}

**뉴스 데이터:**
{news_text}

위 정보를 바탕으로 **800자 이내의 간결하고 가독성 좋은 시장 요약**을 작성하세요.
"""
        return prompt

    @staticmethod
    def create_concise_one_liner_prompt(news_text: str, market_text: str, max_chars: int = 200) -> str:
        """임베드에 들어갈 한 줄 요약 프롬프트를 생성합니다.

        요구사항:
        - 한 줄로만 작성 (줄바꿈 금지)
        - 최대 {max_chars}자 이내
        - 핵심 지수/방향성/대표 종목만 포함 (예: "나스닥 +0.8%, 공포탐욕 62(탐욕), AI/반도체 강세: NVDA TSLA")
        - 불필요한 수식어, 장황한 설명, 마크다운, 이모지 최소화
        - 한국어로 응답
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        prompt = f"""
현재 시간: {current_time}
아래 시장 데이터와 뉴스 요약을 참고해, 디스코드 임베드 설명에 넣을 초간단 한 줄 요약을 생성하세요.

규칙:
- 반드시 한 줄로만 작성하세요. 줄바꿈(\n)을 포함하지 마세요.
- 공백 포함 최대 {max_chars}자 이내로 제한하세요.
- 시장 방향(상승/하락/보합)과 대략의 변동률, 공포탐욕지수 레벨, 가장 눈에 띄는 섹터/테마 1~2개, 대표 종목 1~3개만 담으세요.
- 불필요한 수식어, 긴 문장, 설명, 마크다운, 이모지는 사용하지 마세요.
- 출력 예시: "나스닥 +0.8%, 공포탐욕 62(탐욕), AI/반도체 강세: NVDA TSLA"

시장 데이터:
{market_text}

뉴스 데이터:
{news_text}

요청: 위 정보를 압축해 한 줄 요약만 출력하세요. 줄바꿈이나 추가 설명 금지.
"""
        return prompt

