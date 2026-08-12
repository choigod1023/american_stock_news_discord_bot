# Stock News Discord Bot (with AI Reports)

[한국어](README.md) · [日本語](README.ja.md) · **English**

A bot that automatically posts stock news to Discord channels using the SaveTicker API. **Official news is delivered instantly**, **community news becomes an AI summary report**, and delivery is filtered by **channel topic**.

## Features

- 🔄 **Automatic news monitoring**: checks for new articles on a configurable interval
- 🚨 **Breaking-news detection**: automatically detects breaking keywords in title, body, and tags
- 📌 **Pinning**: breaking and important news are pinned automatically
- 🔔 **Alerts**: both breaking and important news trigger @everyone
- 🖼️ **Image attachments**: thumbnails are attached automatically when present
- 🔗 **Detail links**: a link to each article's detail page
- 📊 **Statistics**: likes, views, and comment counts
- 🎯 **Topic-based filtering**: only posts to channels whose topic contains `american_stock`
- 💾 **File-based cache**: compares against the previous API response to detect only new items
- 🔍 **Deduplication**: processed article IDs are persisted to a file to prevent resends
- 🔄 **Dual API support**: uses the Community API and the News API together to gather more news
- 🤖 **AI summary reports**: hourly Gemini AI summaries of community news
- 📊 **Live market data**: collects and analyzes the NASDAQ price and the fear & greed index in real time
- 🏗️ **Modular structure**: separated per-feature modules improve maintainability and extensibility

## News-processing system

### 📰 Official news (News API) — instant alerts

**Data source**: `NEWS_API_URL` (https://api.saveticker.com/api/news/list)

#### 🚨 Breaking news

- **Criteria**: breaking keywords in title, body, or tags
- **Handling**:
  - @everyone alert
  - Message pinned
  - Red embed
  - ⚡ emoji

#### 🔥 Important news

- **Criteria**: 5 or more likes, or 100 or more views
- **Handling**:
  - @everyone alert
  - Message pinned
  - Orange embed
  - 🔥 emoji

#### 📈 Regular news

- **Handling**:
  - No alert
  - Not pinned
  - Green embed
  - 📈 emoji

### 🤖 Community news (Community API) — AI reports

**Data source**: `API_URL` (https://api.saveticker.com/api/community/list)

- **Handling**: no instant alerts; delivered as an hourly AI summary report
- **AI summary**: Gemini AI analyzes recent community news together with live market data to produce a consolidated report
- **Report contents**:
  - 📈 Bullish drivers (positive impact)
  - 📉 Bearish drivers (negative impact)
  - 🎯 Key issues by sector (tech, financials, energy, healthcare, AI, semiconductors, …)
  - 🔥 Strong-theme analysis (investment themes currently in focus)
  - 💡 Key keywords (up to five)
  - 📊 Market-sentiment analysis (relating the fear & greed index to the news)
  - 🎲 An overall assessment and outlook on market direction
- **Live market data**:
  - 📊 Live NASDAQ price (change rate, market status)
  - 😨📈 Fear & greed index (a market-sentiment indicator)

## Installation and setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies**:

- `discord.py`: Discord bot development
- `google-generativeai`: Gemini AI API integration
- `aiohttp`: async HTTP client
- `python-dotenv`: environment variable management

### 2. Environment variables

```env
# Discord bot token
DISCORD_TOKEN=your_discord_bot_token_here

# API settings
API_URL=USER_API_URL
NEWS_API_URL=NEWS_API_URL
API_PAGE_SIZE=20

# Breaking-news keywords (comma separated)
BREAKING_NEWS_KEYWORDS=속보,긴급,중요,특보,긴급속보,특별속보

# Threshold for "important" messages (like count)
IMPORTANT_LIKE_THRESHOLD=5

# Update interval (seconds)
UPDATE_INTERVAL=10

# AI report settings (required)
GEMINI_API_KEY=your_gemini_api_key_here
REPORT_INTERVAL=3600
REPORT_PAGE_SIZE=100
```

> **Note**: `DISCORD_CHANNEL_ID` is no longer needed. The bot posts automatically to every channel whose topic contains `american_stock`.

### 3. Gemini API key

1. Issue a key at [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Put it in `GEMINI_API_KEY` in your `.env`

**⚠️ Important**: without a valid Gemini API key, a basic summary is produced instead of the AI summary.

**Example**:

```env
GEMINI_API_KEY=AIzaSyC...  # replace with your real key
```

**Troubleshooting**:

- Without a key, the bot runs in "basic summary" mode
- Key errors are logged with detailed messages
- Even if every model fails to initialize, a basic news summary is still produced

**Discord limits**:

- Each embed field is capped at 1024 characters
- Long summaries are truncated at 1020 characters with a trailing "..."
- The whole embed is capped at 6000 characters

### 4. Creating the Discord bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" to create one
3. Create the bot under the "Bot" tab
4. Copy the "Token" into your `.env`
5. Under "OAuth2" > "URL Generator", select these permissions:

   - `Send Messages`
   - `Embed Links`
   - `Attach Files`
   - `Manage Messages` (for pinning)
   - `Mention Everyone` (for @everyone alerts)

6. **Important**: in the "Bot" tab's "Privileged Gateway Intents" section:
   - Do **not** enable `MESSAGE CONTENT INTENT` (it isn't needed)
   - Leave the other privileged intents disabled as well

### 5. Setting the channel topic

Set the topic on the channels the bot should post to:

1. Open channel settings for the channel that should receive news
2. Add `american_stock` to the "channel topic"
3. Save

The bot posts to every channel carrying that topic.

## Cache system

The bot uses a file-based cache for efficient deduplication:

### Cache files

- **`cache/news_cache.json`**: stores processed article IDs
- **`cache/last_response.json`**: stores the hash and metadata of the last API response

### How it works

1. **Dual API calls**: the Community API and News API are called in parallel to gather more news (DESC sorting puts the newest first)
2. **Reverse processing**: each API's results are read from the end so the newest article ends up at index 0
3. **Merge**: results from both APIs are merged and deduplicated by ID
4. **Response comparison**: the current response hash is compared against the previous one to detect changes
5. **New-article filtering**: only unprocessed article IDs are extracted
6. **Cache update**: new article IDs are written to the cache file
7. **Deduplication**: already-processed articles are never resent

### Cache management

- **Automatic backup**: cache files are managed automatically and can be backed up on demand
- **Statistics**: tracks total processed articles, unique article IDs, and more
- **Admin commands**: reset, back up, and inspect the cache

## Running

```bash
python run.py
```

> **Note**: `run.py` is the main entry point; it imports the `discord_bot.discord_bot` module to start the bot.

## Commands

### General

- `!news`: manually fetch the three most recent articles
- `!status`: check the bot's current state
- `!channels`: list channels whose topic contains `american_stock`
- `!test_breaking [text]`: test breaking-news detection

### Cache management (admin only)

- `!cache`: view cache info and statistics
- `!clear_cache`: reset the cache (delete all stored article IDs)
- `!backup_cache`: back up the current cache

## Breaking-news keywords

By default these keywords mark an article as breaking:

- 속보 (breaking)
- 긴급 (urgent)
- 중요 (important)
- 특보 (special report)
- 긴급속보 (urgent breaking)
- 특별속보 (special breaking)

These patterns are also detected:

- `[속보]`, `[긴급]`, `[중요]`, `[특보]`
- `속보:`, `긴급:`, `중요:`, `특보:`
- The 🚨, ⚡, and 🔥 emoji

## File structure

```
america/
├── run.py                 # main entry point
├── requirements.txt       # dependencies
├── config.env.example     # example environment variables
├── README.md              # this file
├── cache/                 # cache file directory
│   ├── news_cache.json    # processed article IDs
│   └── last_response.json # last API response info
├── core/                  # core configuration and utilities
│   ├── __init__.py
│   ├── config.py          # configuration management
│   └── stock_utils.py     # stock-related utility functions
├── ai/                    # AI modules
│   ├── __init__.py
│   ├── ai_summarizer.py   # Gemini AI summarization
│   ├── gemini_client.py   # Gemini API client
│   ├── fallback_summarizer.py # basic summary when AI fails
│   └── news_formatter.py  # news formatting and prompt construction
├── news/                  # news processing
│   ├── __init__.py
│   ├── api_client.py      # API client and breaking-news detection
│   ├── news_handler.py    # news processing and delivery
│   ├── cache_manager.py   # file-based cache manager
│   └── market_data.py     # live market-data collection
└── discord_bot/           # Discord bot
    ├── __init__.py
    ├── discord_bot.py     # main bot file
    ├── command_handler.py # Discord command handling
    ├── embed_builder.py   # Discord embed construction
    ├── image_handler.py   # image handling and delivery
    ├── report_builder.py  # AI report embed construction
    └── report_scheduler.py # hourly report scheduling
```

## Module descriptions

### 🏗️ **core/ — core modules**

- **`config.py`**: environment variables, configuration validation, centralized settings
- **`stock_utils.py`**: stock utility functions, ticker priority sorting, tag analysis

### 🤖 **ai/ — AI modules**

- **`ai_summarizer.py`**: Gemini AI integration, summary generation, market-data analysis
- **`gemini_client.py`**: Gemini API client, model initialization and management
- **`fallback_summarizer.py`**: basic summaries when AI fails — the safety net
- **`news_formatter.py`**: news formatting, AI prompt construction, market-data conversion

### 📰 **news/ — news processing**

- **`api_client.py`**: dual-API support, breaking-news detection, classification and collection
- **`news_handler.py`**: news API calls, data processing, per-channel delivery
- **`cache_manager.py`**: file-based cache, deduplication, statistics tracking
- **`market_data.py`**: live NASDAQ price and fear & greed index collection via the Yahoo Finance API

### 💬 **discord_bot/ — Discord bot**

- **`discord_bot.py`**: the main bot class, module composition, and command registration
- **`command_handler.py`**: all Discord command handling and user-permission management
- **`embed_builder.py`**: Discord embed construction, title cleanup, multiple embed types
- **`image_handler.py`**: image download, attachment, and error handling
- **`report_builder.py`**: converting AI summaries into Discord embeds and formatting reports
- **`report_scheduler.py`**: hourly scheduling, community-news collection, report generation trigger

## Why the modular structure

### 🎯 **Single responsibility**

- Each module has one clear role
- Per-feature directories make the structure explicit
- Changes have a minimal blast radius
- Bugs are easier to trace

### 🔧 **Maintainability**

- Feature separation makes edits easy
- New features touch only the relevant directory
- Easier code review and testing
- Explicit inter-module dependencies

### 📈 **Extensibility**

- New features are just a module in the right directory
- Modules can be reused in other projects
- Modules can be tested independently
- Plugin-style feature growth

### 🏗️ **Architecture**

- A layered directory structure manages dependencies
- `__init__.py` standardizes each module's interface
- Clear interfaces between modules
- A package-based import system

### 📁 **Benefits of the directory layout**

- **`core/`**: central management of configuration and utilities
- **`ai/`**: AI features managed independently
- **`news/`**: news-processing logic encapsulated
- **`discord_bot/`**: Discord bot features separated
- Each directory can be developed and tested on its own

## Logging

The bot writes the following to the console:

- Bot start/stop
- New articles discovered
- Breaking/important news pinned
- Detailed information on errors

## Troubleshooting

### The bot won't start

- Check the token in `.env`
- Check the bot has been invited to the server

### A "privileged intents" error

- Check the "Privileged Gateway Intents" section under Discord Developer Portal > Bot
- If `MESSAGE CONTENT INTENT` is enabled, **disable it**
- This bot never needs to read message content, so the intent isn't required

### Messages aren't being sent

- Check the bot's permissions
- Check the channel topic contains `american_stock` (verify with `!channels`)

### Pinning doesn't work

- Check the bot has the "Manage Messages" permission
- Check whether the channel has hit its pin limit

### Breaking news isn't detected

- Check the `BREAKING_NEWS_KEYWORDS` setting
- Test with the `!test_breaking` command

## License

Released under the MIT License.

---

## 👤 Contribution & development environment

| Item | Detail |
|---|---|
| **Contribution share** | **100%** (solo development) |
| **Commits** | 18 / 18 (mine / all human commits) |
| **Contributors** | 1 |

<sub>Counting basis: commits reachable from **every branch** on origin (merge commits and empty commits excluded), counted by commit author email with one person’s multiple addresses merged; bot and automation commits are excluded.</sub>
