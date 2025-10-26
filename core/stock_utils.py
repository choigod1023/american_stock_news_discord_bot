"""
주식 관련 유틸리티 함수들
"""
from collections import Counter
from typing import List, Dict, Tuple

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

def contains_famous_stock(title: str, content: str = "") -> Tuple[bool, str]:
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
        try:
            return FAMOUS_STOCKS.index(stock_symbol)
        except ValueError:
            return 999  # 리스트에 없는 경우 낮은 우선순위
    else:
        return 999  # 유명한 주식이 없으면 낮은 우선순위

def sort_news_by_stock_priority(news_list: List[Dict]) -> List[Dict]:
    """뉴스 목록을 유명한 주식 우선순위로 정렬합니다."""
    def sort_key(news):
        title = news.get('title', '')
        content = news.get('content', '')
        stock_priority = get_stock_priority(title, content)
        popularity = news.get('like_stats', {}).get('like_count', 0) + news.get('view_count', 0) * 0.1
        
        # 유명한 주식이 있으면 우선순위, 없으면 인기도 기준
        if stock_priority < 999:
            return (0, stock_priority, popularity)
        else:
            return (1, popularity, 0)
    
    return sorted(news_list, key=sort_key)

def get_popular_tags(news_list: List[Dict], top_n: int = 5) -> List[Tuple[str, int]]:
    """뉴스 목록에서 인기 태그를 추출합니다."""
    all_tags = []
    for news in news_list:
        tags = news.get('community_tags', [])
        all_tags.extend(tags)
    
    if not all_tags:
        return []
    
    tag_counts = Counter(all_tags)
    return tag_counts.most_common(top_n)

def format_news_with_stock_info(news_list: List[Dict], max_items: int = 10) -> str:
    """뉴스 목록을 주식 정보와 함께 포맷팅합니다.
    
    중복 제거 및 품질 필터링이 적용됩니다.
    """
    import re
    
    # 1단계: 품질 필터링 (너무 짧거나 의미없는 뉴스 제외)
    filtered_news = []
    for news in news_list:
        title = news.get('title', '').strip()
        content = news.get('content', '').strip()
        
        # 제목이 없으면 제외
        if not title:
            continue
        
        # 제목이 너무 짧으면 제외 (3글자 이하)
        if len(title) < 3:
            continue
        
        # 내용 필터링 (긴 내용 우선)
        content_length = len(content) if content else 0
        
        # 인기도 점수
        like_count = news.get('like_stats', {}).get('like_count', 0)
        view_count = news.get('view_count', 0)
        popularity_score = like_count * 2 + view_count * 0.1
        
        filtered_news.append({
            'original': news,
            'title': title,
            'content_length': content_length,
            'popularity_score': popularity_score
        })
    
    # 2단계: 중복 제거 (제목 기반 정규화)
    seen_titles = set()
    unique_news = []
    for item in filtered_news:
        # 제목 정규화 (특수문자, 공백 제거)
        normalized_title = re.sub(r'[^\w\s]', '', item['title']).lower()
        normalized_title = re.sub(r'\s+', ' ', normalized_title).strip()
        
        # 중복 체크
        if normalized_title not in seen_titles:
            seen_titles.add(normalized_title)
            unique_news.append(item)
    
    # 3단계: 우선순위 정렬 (유명 주식 > 인기도 > 내용 길이)
    def sort_key(item):
        news = item['original']
        title = item['title']
        content = news.get('content', '')
        
        contains_stock, stock_symbol = contains_famous_stock(title, content)
        stock_priority = get_stock_priority(title, content)
        
        # 우선순위 계산
        if stock_priority < 999:  # 유명 주식 포함
            return (0, stock_priority, item['popularity_score'], item['content_length'])
        else:
            # 유명 주식이 없으면 인기도와 내용 길이 기준
            return (1, -item['popularity_score'], -item['content_length'])
    
    sorted_news = sorted(unique_news, key=sort_key)
    
    # 4단계: 최종 포맷팅
    formatted_items = []
    for i, item in enumerate(sorted_news[:max_items], 1):
        news = item['original']
        title = news.get('title', '제목 없음')
        author = news.get('author_name', 'Unknown')
        contains_stock, stock_symbol = contains_famous_stock(title, news.get('content', ''))
        stock_info = f" [{stock_symbol}]" if contains_stock else ""
        formatted_items.append(f"{i}. {title} (by {author}){stock_info}")
    
    return "\n".join(formatted_items) if formatted_items else "주요 헤드라인이 없습니다."



