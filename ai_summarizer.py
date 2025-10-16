"""
리팩토링된 AI 요약기 모듈
모듈화된 구조로 재사용성과 유지보수성 향상
"""
import logging
from typing import List, Dict, Optional
from google import genai
from gemini_client import GeminiClient
from news_formatter import NewsFormatter
from fallback_summarizer import FallbackSummarizer

logger = logging.getLogger(__name__)

class AISummarizer:
    """모듈화된 AI 요약기 클래스"""
    
    def __init__(self, api_key: str):
        """AI 요약기를 초기화합니다."""
        self.gemini_client = GeminiClient(api_key)
        self.news_formatter = NewsFormatter()
        self.fallback_summarizer = FallbackSummarizer()
        
        if not self.gemini_client.is_available():
            logger.warning("Gemini AI 클라이언트가 사용 불가능합니다. 기본 요약 모드로 동작합니다.")
    
    async def summarize_news(self, news_list: List[Dict]) -> Optional[str]:
        """뉴스 목록을 AI로 요약합니다."""
        if not news_list:
            return None
        
        if not self.gemini_client.is_available():
            logger.error("Gemini AI 모델이 초기화되지 않았습니다. 기본 요약을 생성합니다.")
            return self.fallback_summarizer.create_fallback_summary(news_list)
        
        try:
            # 뉴스 데이터를 텍스트로 변환
            news_text = self.news_formatter.format_news_for_ai(news_list)
            
            # AI 프롬프트 생성
            prompt = self.news_formatter.create_summary_prompt(news_text)
            
            # AI 요약 요청
            response = self.gemini_client.generate_content(prompt)
            
            if response:
                # 응답에서 텍스트 추출
                ai_summary = self.gemini_client.extract_text_from_response(response)
                if ai_summary:
                    logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 처리")
                    return ai_summary
                else:
                    logger.warning("AI 응답에서 텍스트를 추출할 수 없습니다.")
                    return self.fallback_summarizer.create_fallback_summary(news_list)
            else:
                logger.error("Gemini API 호출 실패")
                return self.fallback_summarizer.create_fallback_summary(news_list)
                
        except Exception as e:
            logger.error(f"AI 요약 중 오류 발생: {e}")
            return self.fallback_summarizer.create_fallback_summary(news_list)
    
    async def summarize_news_with_market_data(self, news_list: List[Dict], market_data: Dict) -> Optional[str]:
        """뉴스 목록과 시장 데이터를 AI로 요약합니다."""
        if not news_list:
            return None
        
        if not self.gemini_client.is_available():
            logger.error("Gemini AI 모델이 초기화되지 않았습니다. 기본 요약을 생성합니다.")
            return self.fallback_summarizer.create_fallback_summary_with_market_data(news_list, market_data)
        
        try:
            # 뉴스 데이터를 텍스트로 변환
            news_text = self.news_formatter.format_news_for_ai(news_list)
            
            # 시장 데이터를 텍스트로 변환
            market_text = self.news_formatter.format_market_data_for_ai(market_data)
            
            # 임베드용 초간단 한 줄 요약 프롬프트 생성
            prompt = self.news_formatter.create_concise_one_liner_prompt(news_text, market_text, max_chars=200)
            
            # AI 요약 요청
            response = self.gemini_client.generate_content(prompt)
            
            if response:
                # 응답에서 텍스트 추출
                ai_summary = self.gemini_client.extract_text_from_response(response)
                # 안전장치: 개행 제거 및 길이 제한 적용
                if ai_summary:
                    ai_summary = " ".join(ai_summary.splitlines()).strip()
                    if len(ai_summary) > 200:
                        ai_summary = ai_summary[:197] + "..."
                if ai_summary:
                    logger.info(f"AI 요약 완료: {len(news_list)}개 뉴스 + 시장 데이터 처리")
                    return ai_summary
                else:
                    logger.warning("AI 응답에서 텍스트를 추출할 수 없습니다.")
                    return self.fallback_summarizer.create_fallback_summary_with_market_data(news_list, market_data)
            else:
                logger.error("Gemini API 호출 실패")
                return self.fallback_summarizer.create_fallback_summary_with_market_data(news_list, market_data)
                
        except Exception as e:
            logger.error(f"AI 요약 중 오류 발생: {e}")
            return self.fallback_summarizer.create_fallback_summary_with_market_data(news_list, market_data)
    
    def is_available(self) -> bool:
        """AI 서비스가 사용 가능한지 확인"""
        return self.gemini_client.is_available()