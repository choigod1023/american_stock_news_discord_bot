import logging
import aiohttp
from io import BytesIO
import discord

logger = logging.getLogger(__name__)

class ImageHandler:
    """이미지 처리 및 전송을 담당하는 클래스"""
    
    def __init__(self):
        pass
    
    async def send_image_attachment(self, channel, image_url: str, filename: str):
        """이미지를 첨부파일로 전송합니다."""
        try:
            normalized = self._normalize_url(image_url)
            if not normalized:
                logger.warning("유효하지 않은 이미지 URL, 첨부를 건너뜁니다.")
                return
            async with aiohttp.ClientSession() as session:
                async with session.get(normalized) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        file = discord.File(BytesIO(image_data), filename=f"{filename}.jpg")
                        await channel.send(file=file)
                        logger.info(f"이미지 첨부 완료: {filename}")
                    else:
                        logger.warning(f"이미지 다운로드 실패: HTTP {response.status}")
        except Exception as e:
            logger.error(f"이미지 첨부 중 오류 발생: {e}")

    def _normalize_url(self, url: str) -> str:
        if not url or not isinstance(url, str):
            return None
        u = url.strip()
        if u.startswith('http://') or u.startswith('https://'):
            return u
        if u.startswith('/'):
            return 'https://api.saveticker.com' + u
        return None
