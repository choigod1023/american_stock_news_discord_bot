import aiohttp
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from random import random

logger = logging.getLogger(__name__)

class MarketDataCollector:
    """실시간 시장 데이터 수집 클래스"""
    
    def __init__(self):
        self.nasdaq_url_primary = "https://query1.finance.yahoo.com/v8/finance/chart/%5EIXIC"  # NASDAQ Composite
        self.nasdaq_url_fallback = "https://query2.finance.yahoo.com/v8/finance/chart/%5EIXIC"
        self.fear_greed_url = "https://api.alternative.me/fng/"  # Fear & Greed Index
        self.session = None
        # 간단한 메모리 캐시 (429 등 실패 시 사용)
        self._nasdaq_cache: Optional[Dict] = None
        self._fear_greed_cache: Optional[Dict] = None
        # 공통 헤더 (간단한 User-Agent 추가)
        self._headers = {
            "User-Agent": "Mozilla/5.0 (compatible; StockNewsBot/1.0; +https://saveticker.com)"
        }
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(timeout=timeout, headers=self._headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request_with_backoff(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[Dict]:
        """백오프를 적용하여 JSON 응답을 요청합니다."""
        if not self.session:
            return None
        delay_base = 0.7
        last_status = None
        for attempt in range(max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    last_status = response.status
                    if response.status == 200:
                        return await response.json()
                    # 429 또는 5xx는 재시도
                    if response.status in (429, 500, 502, 503, 504):
                        backoff = delay_base * (2 ** attempt) + random() * 0.3
                        await asyncio.sleep(backoff)
                        continue
                    # 그 외 상태코드는 즉시 중단
                    logger.error(f"요청 실패: HTTP {response.status} for {url}")
                    return None
            except Exception as e:
                # 네트워크 오류 재시도
                backoff = delay_base * (2 ** attempt) + random() * 0.3
                logger.warning(f"요청 예외 발생 (재시도 {attempt+1}/{max_retries}): {e}")
                await asyncio.sleep(backoff)
                continue
        if last_status:
            logger.error(f"요청 반복 실패: HTTP {last_status} for {url}")
        return None

    async def get_nasdaq_price(self) -> Optional[Dict]:
        """나스닥 실시간 주가 정보를 가져옵니다."""
        try:
            # 1) 기본 엔드포인트 시도
            data = await self._request_with_backoff(self.nasdaq_url_primary)
            # 2) 실패 시 보조 엔드포인트 시도
            if data is None:
                data = await self._request_with_backoff(self.nasdaq_url_fallback)
            
            if data:
                # Yahoo Finance API 응답 구조 파싱
                chart = data.get('chart', {})
                result = chart.get('result', [])
                if result:
                    quote = result[0].get('meta', {})
                    current_price = quote.get('regularMarketPrice', 0)
                    previous_close = quote.get('previousClose', 0)
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
                    market_state = quote.get('marketState', 'CLOSED')
                    currency = quote.get('currency', 'USD')
                    parsed = {
                        'current_price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'previous_close': round(previous_close, 2),
                        'market_state': market_state,
                        'currency': currency,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'stale': False,
                    }
                    # 캐시 갱신
                    self._nasdaq_cache = parsed
                    return parsed
            # 실패: 캐시 반환
            if self._nasdaq_cache:
                cached = dict(self._nasdaq_cache)
                cached['stale'] = True
                logger.warning("나스닥 데이터가 새로고침되지 않아 캐시를 사용합니다 (stale).")
                return cached
            else:
                logger.error("나스닥 주가 API 전체 실패 및 캐시 없음")
                    
        except Exception as e:
            logger.error(f"나스닥 주가 조회 중 오류 발생: {e}")
        
        return None
    
    async def get_fear_greed_index(self) -> Optional[Dict]:
        """공포탐욕지수를 가져옵니다."""
        try:
            data = await self._request_with_backoff(self.fear_greed_url)
            if data:
                # Alternative.me Fear & Greed Index API 응답 구조 파싱
                fng_data = data.get('data', [])
                if fng_data:
                    current_data = fng_data[0]
                    value = current_data.get('value', '0')
                    value_classification = current_data.get('value_classification', 'Unknown')
                    timestamp = current_data.get('timestamp', '')
                    # 타임스탬프를 읽기 쉬운 형태로 변환
                    if timestamp:
                        try:
                            dt = datetime.fromtimestamp(int(timestamp))
                            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            formatted_time = timestamp
                    else:
                        formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    parsed = {
                        'value': int(value),
                        'classification': value_classification,
                        'timestamp': formatted_time,
                        'stale': False,
                    }
                    self._fear_greed_cache = parsed
                    return parsed
            # 실패 시 캐시 사용
            if self._fear_greed_cache:
                cached = dict(self._fear_greed_cache)
                cached['stale'] = True
                logger.warning("공포탐욕지수 데이터가 새로고침되지 않아 캐시를 사용합니다 (stale).")
                return cached
            else:
                logger.error("공포탐욕지수 API 전체 실패 및 캐시 없음")
                    
        except Exception as e:
            logger.error(f"공포탐욕지수 조회 중 오류 발생: {e}")
        
        return None
    
    async def get_market_summary(self) -> Dict:
        """종합 시장 정보를 가져옵니다."""
        nasdaq_data = await self.get_nasdaq_price()
        fear_greed_data = await self.get_fear_greed_index()
        
        return {
            'nasdaq': nasdaq_data,
            'fear_greed': fear_greed_data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
