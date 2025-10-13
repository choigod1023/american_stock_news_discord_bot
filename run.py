#!/usr/bin/env python3
"""
주식 뉴스 디스코드 봇 실행 파일
"""

import sys
import os
from discord_bot import main

if __name__ == "__main__":
    try:
        print("🤖 주식 뉴스 디스코드 봇을 시작합니다...")
        print("🚨 속보 감지 기능이 활성화되었습니다.")
        main()
    except KeyboardInterrupt:
        print("\n👋 봇을 종료합니다.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")
        sys.exit(1)