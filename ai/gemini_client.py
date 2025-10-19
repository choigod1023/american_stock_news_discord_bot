"""
Gemini AI 클라이언트 모듈
다양한 Gemini API 버전을 지원하는 통합 클라이언트
"""
import logging

from typing import Optional, Union

logger = logging.getLogger(__name__)

class GeminiClient:
    """다양한 Gemini API 버전을 지원하는 통합 클라이언트"""
    
    def __init__(self, api_key: str = None):
        self.client = None
        self.model = None
        self.api_type = None
        
        # API 키가 있으면 설정
        if api_key:
            self._setup_client(api_key)
    
    def _setup_client(self, api_key: str):
        """클라이언트 초기화"""
        try:
            # 새로운 Google genai 클라이언트 방식 시도
            from google import genai
            
            if hasattr(genai, 'Client'):
                self.client = genai.Client()
                self.api_type = 'new_client'
                logger.info("Google genai 클라이언트 초기화 성공")
            else:
                # 기존 방식
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.api_type = 'legacy'
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
                    # 구버전: 모델명만 저장
                    logger.info("GenerativeModel 클래스 없음, 직접 generate_content 사용")
                    self.model = "gemini-pro"
                    
        except ImportError:
            # google-generativeai 라이브러리 방식
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.api_type = 'legacy'
            logger.info("google-generativeai 라이브러리 방식 사용")
            
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
                self.model = "gemini-pro"
        
        except Exception as e:
            logger.error(f"Gemini API 설정 실패: {e}")
            self.api_type = 'failed'
    
    def is_available(self) -> bool:
        """클라이언트가 사용 가능한지 확인"""
        return self.client is not None or self.model is not None
    
    def generate_content(self, prompt: str, model_name: str = "gemini-2.5-flash") -> Optional[object]:
        """콘텐츠 생성"""
        if not self.is_available():
            logger.error("Gemini 클라이언트가 사용 불가능합니다.")
            return None
        
        try:
            if self.api_type == 'new_client':
                # 새로운 클라이언트 방식
                response = self.client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
            elif isinstance(self.model, str):
                # 구버전: Client 객체를 통한 호출
                from google import genai
                client = genai.Client()
                response = client.models.generate_content(
                    model=self.model, 
                    contents=prompt
                )
            else:
                # 최신 버전 API 호출
                response = self.model.generate_content(prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            return None
    
    def extract_text_from_response(self, response) -> Optional[str]:
        """응답에서 텍스트 추출 (다양한 버전 호환)"""
        if not response:
            return None
        
        try:
            # 새로운 클라이언트 방식 응답 처리
            if hasattr(response, 'text') and response.text:
                return response.text
            
            # 기존 방식 응답 처리
            if hasattr(response, 'parts') and response.parts:
                text_content = ""
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_content += part.text
                if text_content:
                    return text_content
            
            # 구버전 응답 구조
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            text_content = ""
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_content += part.text
                            if text_content:
                                return text_content
            
            logger.warning("응답에서 텍스트를 추출할 수 없습니다.")
            return None
            
        except Exception as e:
            logger.error(f"응답 텍스트 추출 중 오류: {e}")
            return None

