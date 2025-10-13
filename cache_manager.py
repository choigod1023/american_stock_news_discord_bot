import json
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)

class NewsCacheManager:
    """뉴스 데이터를 파일로 저장하고 비교하는 캐시 관리자"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.news_cache_file = os.path.join(cache_dir, "news_cache.json")
        self.last_response_file = os.path.join(cache_dir, "last_response.json")
        
        # 캐시 디렉토리 생성
        os.makedirs(cache_dir, exist_ok=True)
        
        # 기존 캐시 로드
        self.news_cache = self._load_news_cache()
        self.last_response = self._load_last_response()
    
    def _load_news_cache(self) -> Dict:
        """뉴스 캐시 파일을 로드합니다."""
        try:
            if os.path.exists(self.news_cache_file):
                with open(self.news_cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # JSON에서 로드된 list를 set으로 변환
                    news_ids_list = cache.get('news_ids', [])
                    cache['news_ids'] = set(news_ids_list)
                    logger.info(f"뉴스 캐시 로드 완료: {len(cache['news_ids'])}개 뉴스")
                    return cache
        except Exception as e:
            logger.error(f"뉴스 캐시 로드 실패: {e}")
        
        return {
            "news_ids": set(),
            "last_update": None,
            "total_processed": 0
        }
    
    def _load_last_response(self) -> Dict:
        """마지막 API 응답을 로드합니다."""
        try:
            if os.path.exists(self.last_response_file):
                with open(self.last_response_file, 'r', encoding='utf-8') as f:
                    response = json.load(f)
                    logger.info(f"마지막 API 응답 로드 완료: {response.get('timestamp', 'Unknown')}")
                    return response
        except Exception as e:
            logger.error(f"마지막 API 응답 로드 실패: {e}")
        
        return {
            "timestamp": None,
            "response_hash": None,
            "news_count": 0
        }
    
    def _save_news_cache(self):
        """뉴스 캐시를 파일에 저장합니다."""
        try:
            # set을 list로 변환 (JSON 직렬화를 위해)
            cache_to_save = self.news_cache.copy()
            cache_to_save["news_ids"] = list(cache_to_save["news_ids"])
            
            with open(self.news_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_to_save, f, ensure_ascii=False, indent=2)
            logger.info(f"뉴스 캐시 저장 완료: {len(self.news_cache['news_ids'])}개 뉴스")
        except Exception as e:
            logger.error(f"뉴스 캐시 저장 실패: {e}")
    
    def _save_last_response(self, response_data: Dict):
        """마지막 API 응답을 파일에 저장합니다."""
        try:
            with open(self.last_response_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            logger.info(f"마지막 API 응답 저장 완료: {response_data.get('timestamp', 'Unknown')}")
        except Exception as e:
            logger.error(f"마지막 API 응답 저장 실패: {e}")
    
    def _generate_response_hash(self, response_data: Dict) -> str:
        """API 응답 데이터의 해시를 생성합니다."""
        try:
            # 뉴스 리스트만 추출하여 해시 생성
            news_list = response_data.get('posts', [])
            news_data = []
            
            for news in news_list:
                news_data.append({
                    'id': news.get('id'),
                    'title': news.get('title'),
                    'content': news.get('content'),
                    'created_at': news.get('created_at')
                })
            
            # 정렬하여 일관된 해시 생성
            news_data.sort(key=lambda x: x.get('id', ''))
            
            data_string = json.dumps(news_data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(data_string.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"응답 해시 생성 실패: {e}")
            return ""
    
    def get_new_news(self, current_response: Dict) -> List[Dict]:
        """현재 응답에서 새로운 뉴스만 필터링합니다."""
        try:
            current_news_list = current_response.get('posts', [])
            new_news = []
            
            # news_ids가 set이 아닌 경우 set으로 변환
            if not isinstance(self.news_cache['news_ids'], set):
                self.news_cache['news_ids'] = set(self.news_cache['news_ids'])
            
            for news in current_news_list:
                news_id = news.get('id')
                if news_id and news_id not in self.news_cache['news_ids']:
                    new_news.append(news)
                    self.news_cache['news_ids'].add(news_id)
                    self.news_cache['total_processed'] += 1
            
            # 새로운 뉴스가 있으면 캐시 업데이트
            if new_news:
                self.news_cache['last_update'] = datetime.now().isoformat()
                self._save_news_cache()
                logger.info(f"새로운 뉴스 {len(new_news)}개 감지")
            
            return new_news
            
        except Exception as e:
            logger.error(f"새로운 뉴스 필터링 실패: {e}")
            return []
    
    def has_response_changed(self, current_response: Dict) -> bool:
        """API 응답이 변경되었는지 확인합니다."""
        try:
            current_hash = self._generate_response_hash(current_response)
            last_hash = self.last_response.get('response_hash')
            
            # 해시가 다르면 응답이 변경됨
            if current_hash != last_hash:
                # 새로운 응답 정보 저장
                self.last_response = {
                    "timestamp": datetime.now().isoformat(),
                    "response_hash": current_hash,
                    "news_count": len(current_response.get('posts', []))
                }
                self._save_last_response(self.last_response)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"응답 변경 확인 실패: {e}")
            return True  # 오류 시 안전하게 변경되었다고 가정
    
    def get_cache_stats(self) -> Dict:
        """캐시 통계 정보를 반환합니다."""
        return {
            "total_processed_news": self.news_cache.get('total_processed', 0),
            "unique_news_ids": len(self.news_cache.get('news_ids', set())),
            "last_update": self.news_cache.get('last_update'),
            "last_response_time": self.last_response.get('timestamp'),
            "last_response_news_count": self.last_response.get('news_count', 0),
            "cache_files": {
                "news_cache": self.news_cache_file,
                "last_response": self.last_response_file
            }
        }
    
    def clear_cache(self):
        """캐시를 초기화합니다."""
        try:
            # 메모리 캐시 초기화
            self.news_cache = {
                "news_ids": set(),
                "last_update": None,
                "total_processed": 0
            }
            self.last_response = {
                "timestamp": None,
                "response_hash": None,
                "news_count": 0
            }
            
            # 파일 삭제
            if os.path.exists(self.news_cache_file):
                os.remove(self.news_cache_file)
            if os.path.exists(self.last_response_file):
                os.remove(self.last_response_file)
            
            logger.info("캐시 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"캐시 초기화 실패: {e}")
            return False
    
    def backup_cache(self, backup_dir: str = "cache_backup"):
        """캐시를 백업합니다."""
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"cache_backup_{timestamp}")
            
            os.makedirs(backup_path, exist_ok=True)
            
            if os.path.exists(self.news_cache_file):
                shutil.copy2(self.news_cache_file, backup_path)
            if os.path.exists(self.last_response_file):
                shutil.copy2(self.last_response_file, backup_path)
            
            logger.info(f"캐시 백업 완료: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"캐시 백업 실패: {e}")
            return None
