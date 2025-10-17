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
    """뉴스 목록을 주식 정보와 함께 포맷팅합니다."""
    formatted_items = []
    sorted_news = sort_news_by_stock_priority(news_list)
    
    for i, news in enumerate(sorted_news[:max_items], 1):
        title = news.get('title', '제목 없음')
        author = news.get('author_name', 'Unknown')
        contains_stock, stock_symbol = contains_famous_stock(title, news.get('content', ''))
        stock_info = f" [{stock_symbol}]" if contains_stock else ""
        formatted_items.append(f"{i}. {title} (by {author}){stock_info}")
    
    return "\n".join(formatted_items)


