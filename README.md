# 주식 뉴스 디스코드 봇 (AI 리포트 기능)

SaveTicker API를 활용하여 주식 관련 뉴스를 디스코드 채널에 자동으로 전송하는 봇입니다. **공식 뉴스는 즉시 알림**, **Community 뉴스는 AI 요약 리포트**로 처리하며, **채널 토픽 기반 필터링**을 지원합니다.

## 주요 기능

- 🔄 **자동 뉴스 모니터링**: 설정된 간격으로 새로운 뉴스를 자동으로 체크
- 🚨 **속보 감지**: 제목, 내용, 태그에서 속보 키워드를 자동 감지
- 📌 **핀 고정**: 속보와 중요 뉴스는 자동으로 핀 고정
- 🔔 **알림**: 속보는 @everyone, 중요 뉴스는 @everyone 알림
- 🖼️ **이미지 첨부**: 썸네일 이미지가 있는 경우 자동 첨부
- 🔗 **상세 링크**: 각 뉴스의 상세 페이지로 이동할 수 있는 링크 제공
- 📊 **통계 정보**: 좋아요, 조회수, 댓글 수 표시
- 🎯 **토픽 기반 필터링**: `american_stock` 토픽을 가진 채널에만 메시지 전송
- 💾 **파일 기반 캐시**: 이전 API 응답과 비교하여 새로운 뉴스만 감지
- 🔍 **중복 방지**: 처리된 뉴스 ID를 파일로 저장하여 중복 전송 방지
- 🔄 **듀얼 API 지원**: Community API와 News API를 동시에 사용하여 더 많은 뉴스 수집
- 🤖 **AI 요약 리포트**: Gemini AI를 활용한 Community 뉴스 1시간 주기 요약 리포트
- 📊 **실시간 시장 데이터**: 나스닥 주가, 공포탐욕지수 실시간 수집 및 분석
- 🏗️ **모듈화된 구조**: 각 기능별로 분리된 모듈로 유지보수성과 확장성 향상

## 뉴스 처리 시스템

### 📰 공식 뉴스 (News API) - 즉시 알림

**데이터 소스**: `NEWS_API_URL` (https://api.saveticker.com/api/news/list)

#### 🚨 속보 (Breaking News)

- **판단 기준**: 제목, 내용, 태그에 속보 키워드 포함
- **처리 방식**:
  - @everyone 알림
  - 메시지 핀 고정
  - 빨간색 임베드
  - ⚡ 이모지 표시

#### 🔥 중요 뉴스 (Important News)

- **판단 기준**: 좋아요 5개 이상 또는 조회수 100 이상
- **처리 방식**:
  - @everyone 알림
  - 메시지 핀 고정
  - 주황색 임베드
  - 🔥 이모지 표시

#### 📈 일반 뉴스 (Regular News)

- **처리 방식**:
  - 알림 없음
  - 핀 고정 없음
  - 초록색 임베드
  - 📈 이모지 표시

### 🤖 Community 뉴스 (Community API) - AI 리포트

**데이터 소스**: `API_URL` (https://api.saveticker.com/api/community/list)

- **처리 방식**: 즉시 알림 없음, 1시간 주기 AI 요약 리포트로 처리
- **AI 요약**: Gemini AI가 최근 Community 뉴스들과 실시간 시장 데이터를 분석하여 종합 리포트 생성
- **리포트 내용**:
  - 📈 상승 요인 뉴스 (긍정적 영향)
  - 📉 하락 요인 뉴스 (부정적 영향)
  - 🎯 섹터별 주요 이슈 (기술, 금융, 에너지, 헬스케어, AI, 반도체 등)
  - 🔥 강세 테마 분석 (현재 주목받는 투자 테마)
  - 💡 핵심 키워드 (5개 이내)
  - 📊 시장 심리 분석 (공포탐욕지수와 뉴스 연관성)
  - 🎲 전체적인 시장 동향 평가 및 전망
- **실시간 시장 데이터**:
  - 📊 나스닥 실시간 주가 (변동률, 시장 상태)
  - 😨📈 공포탐욕지수 (시장 심리 지표)

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

**주요 의존성**:

- `discord.py`: Discord 봇 개발
- `google-generativeai`: Gemini AI API 연동
- `aiohttp`: 비동기 HTTP 클라이언트
- `python-dotenv`: 환경 변수 관리

### 2. 환경 변수 설정

```env
# 디스코드 봇 토큰
DISCORD_TOKEN=your_discord_bot_token_here

# API 설정
API_URL=USER_API_URL
NEWS_API_URL=NEWS_API_URL
API_PAGE_SIZE=20

# 속보 판단 키워드 (쉼표로 구분)
BREAKING_NEWS_KEYWORDS=속보,긴급,중요,특보,긴급속보,특별속보

# 일반 중요 메시지 판단 기준 (좋아요 수)
IMPORTANT_LIKE_THRESHOLD=5

# 업데이트 간격 (초)
UPDATE_INTERVAL=10

# AI 리포트 설정 (필수)
GEMINI_API_KEY=your_gemini_api_key_here
REPORT_INTERVAL=3600
REPORT_PAGE_SIZE=100
```

> **참고**: `DISCORD_CHANNEL_ID`는 더 이상 필요하지 않습니다. 봇은 `american_stock` 토픽을 가진 모든 채널에 자동으로 메시지를 전송합니다.

### 3. Gemini API 키 설정

1. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키를 발급받으세요
2. `.env` 파일의 `GEMINI_API_KEY`에 발급받은 키를 입력하세요

**⚠️ 중요**: Gemini API 키가 없거나 잘못된 경우 AI 요약 대신 기본 요약이 제공됩니다.

**API 키 설정 예시**:

```env
GEMINI_API_KEY=AIzaSyC...  # 실제 API 키로 교체
```

**문제 해결**:

- API 키가 없으면 "기본 요약" 모드로 동작
- API 키 오류 시 로그에 상세한 오류 메시지 표시
- 모든 모델 초기화 실패 시에도 기본 뉴스 요약 제공

### 4. 디스코드 봇 생성

1. [Discord Developer Portal](https://discord.com/developers/applications)에 접속
2. "New Application" 클릭하여 새 애플리케이션 생성
3. "Bot" 탭에서 봇 생성
4. "Token"을 복사하여 `.env` 파일에 입력
5. "OAuth2" > "URL Generator"에서 다음 권한 선택:

   - `Send Messages`
   - `Embed Links`
   - `Attach Files`
   - `Manage Messages` (핀 고정을 위해)
   - `Mention Everyone` (@everyone 알림을 위해)

6. **중요**: "Bot" 탭에서 "Privileged Gateway Intents" 섹션에서:
   - `MESSAGE CONTENT INTENT`는 **활성화하지 마세요** (필요하지 않음)
   - 다른 privileged intents도 비활성화 상태로 유지

### 4. 채널 토픽 설정

봇이 메시지를 전송할 채널의 토픽을 설정하세요:

1. 뉴스를 받고 싶은 채널에서 채널 설정으로 이동
2. "채널 토픽"에 `american_stock` 추가
3. 저장

봇은 이 토픽을 가진 모든 채널에 자동으로 뉴스를 전송합니다.

## 캐시 시스템

봇은 효율적인 중복 방지를 위해 파일 기반 캐시 시스템을 사용합니다:

### 캐시 파일

- **`cache/news_cache.json`**: 처리된 뉴스 ID들을 저장
- **`cache/last_response.json`**: 마지막 API 응답의 해시와 메타데이터 저장

### 동작 방식

1. **듀얼 API 호출**: Community API와 News API를 병렬로 호출하여 더 많은 뉴스 수집 (DESC 정렬로 최신 뉴스가 리스트 앞에 위치)
2. **역순 처리**: 각 API 결과를 뒤에서부터 읽어와서 최신 뉴스가 인덱스 0번에 오도록 함
3. **데이터 병합**: 두 API의 결과를 ID 기준으로 중복 제거하여 병합
4. **API 응답 비교**: 현재 응답과 이전 응답의 해시를 비교하여 변경사항 감지
5. **새로운 뉴스 필터링**: 처리되지 않은 뉴스 ID만 추출
6. **캐시 업데이트**: 새로운 뉴스 ID를 캐시 파일에 저장
7. **중복 방지**: 이미 처리된 뉴스는 다시 전송하지 않음

### 캐시 관리

- **자동 백업**: 캐시 파일은 자동으로 관리되며 필요시 백업 가능
- **통계 추적**: 총 처리된 뉴스 수, 고유 뉴스 ID 수 등 추적
- **관리자 명령어**: 캐시 초기화, 백업, 정보 확인 기능 제공

## 실행

```bash
python discord_bot.py
# 또는
python run.py
```

## 명령어

### 일반 명령어

- `!news`: 수동으로 최신 뉴스 3개를 확인
- `!status`: 봇의 현재 상태 확인
- `!channels`: `american_stock` 토픽을 가진 채널 목록 확인
- `!test_breaking [텍스트]`: 속보 감지 테스트

### 캐시 관리 명령어 (관리자 전용)

- `!cache`: 캐시 정보 및 통계 확인
- `!clear_cache`: 캐시 초기화 (모든 저장된 뉴스 ID 삭제)
- `!backup_cache`: 현재 캐시를 백업

## 속보 감지 키워드

기본적으로 다음 키워드들이 속보로 감지됩니다:

- 속보
- 긴급
- 중요
- 특보
- 긴급속보
- 특별속보

또한 다음 패턴도 감지됩니다:

- `[속보]`, `[긴급]`, `[중요]`, `[특보]`
- `속보:`, `긴급:`, `중요:`, `특보:`
- 🚨, ⚡, 🔥 이모지

## 파일 구조

```
america/
├── discord_bot.py          # 메인 봇 파일 (간소화됨)
├── news_handler.py         # 뉴스 처리 및 전송 로직
├── embed_builder.py        # Discord 임베드 생성
├── image_handler.py        # 이미지 처리 및 전송
├── command_handler.py      # Discord 명령어 처리
├── api_client.py          # API 클라이언트 및 속보 감지 로직
├── cache_manager.py       # 파일 기반 캐시 관리자
├── ai_summarizer.py       # Gemini AI 요약 처리
├── report_scheduler.py    # 1시간 주기 리포트 스케줄링
├── report_builder.py      # AI 리포트 임베드 생성
├── market_data.py         # 실시간 시장 데이터 수집 (나스닥, 공포탐욕지수)
├── config.py              # 설정 관리
├── requirements.txt       # 의존성 목록
├── config.env.example     # 환경 변수 예시
├── run.py                 # 실행 파일
├── .gitignore             # Git 무시 파일 목록
├── cache/                 # 캐시 파일 저장 디렉토리
│   ├── news_cache.json    # 처리된 뉴스 ID 저장
│   └── last_response.json # 마지막 API 응답 정보
└── README.md              # 이 파일
```

## 모듈별 설명

### 🏗️ **핵심 모듈**

- **`discord_bot.py`**: 메인 봇 클래스, 모듈 조합 및 명령어 등록
- **`news_handler.py`**: 뉴스 API 호출, 데이터 처리, 채널별 전송 관리
- **`embed_builder.py`**: Discord 임베드 생성, 제목 정리, 다양한 임베드 타입 지원
- **`command_handler.py`**: 모든 Discord 명령어 처리 및 사용자 권한 관리
- **`image_handler.py`**: 이미지 다운로드, 첨부, 오류 처리

### 🔧 **유틸리티 모듈**

- **`api_client.py`**: 듀얼 API 지원, 속보 감지, 뉴스 분류
- **`cache_manager.py`**: 파일 기반 캐시, 중복 방지, 통계 추적
- **`config.py`**: 환경 변수 관리, 설정 검증

### 🤖 **AI 리포트 모듈**

- **`ai_summarizer.py`**: Gemini AI 연동, 뉴스 요약 생성, 프롬프트 관리, 시장 데이터 분석
- **`report_scheduler.py`**: 1시간 주기 스케줄링, Community 뉴스 수집, 리포트 생성 트리거
- **`report_builder.py`**: AI 요약 결과를 Discord 임베드로 변환, 리포트 포맷팅, 시장 데이터 표시
- **`market_data.py`**: 실시간 나스닥 주가, 공포탐욕지수 수집, Yahoo Finance API 연동

## 모듈화의 장점

### 🎯 **단일 책임 원칙**

- 각 모듈이 하나의 명확한 역할을 담당
- 코드 수정 시 영향 범위 최소화
- 버그 발생 시 원인 파악 용이

### 🔧 **유지보수성**

- 기능별로 분리되어 수정이 쉬움
- 새로운 기능 추가 시 해당 모듈만 수정
- 코드 리뷰 및 테스트 용이

### 📈 **확장성**

- 새로운 명령어나 임베드 타입 쉽게 추가
- 다른 프로젝트에서 모듈 재사용 가능
- 독립적인 모듈 테스트 가능

### 🏗️ **아키텍처**

- 의존성 주입을 통한 느슨한 결합
- 메인 봇 파일 80% 코드 감소 (499줄 → 95줄)
- 명확한 모듈 간 인터페이스

## 로깅

봇은 콘솔에 다음과 같은 로그를 출력합니다:

- 봇 시작/종료
- 새로운 뉴스 발견
- 속보/중요 뉴스 핀 고정
- 오류 발생 시 상세 정보

## 문제 해결

### 봇이 시작되지 않는 경우

- `.env` 파일의 토큰이 올바른지 확인
- 봇이 서버에 초대되어 있는지 확인

### "privileged intents" 오류가 발생하는 경우

- Discord Developer Portal > Bot 탭에서 "Privileged Gateway Intents" 섹션 확인
- `MESSAGE CONTENT INTENT`가 활성화되어 있다면 **비활성화**하세요
- 우리 봇은 메시지 내용을 읽을 필요가 없으므로 이 intent가 필요하지 않습니다

### 메시지가 전송되지 않는 경우

- 봇의 권한 설정 확인
- 채널 토픽에 `american_stock`이 포함되어 있는지 확인 (`!channels` 명령어로 확인 가능)

### 핀 고정이 되지 않는 경우

- 봇에 "메시지 관리" 권한이 있는지 확인
- 채널의 핀 고정 제한 수에 도달했는지 확인

### 속보가 감지되지 않는 경우

- `BREAKING_NEWS_KEYWORDS` 설정 확인
- `!test_breaking` 명령어로 테스트

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
