# Environment Variables Setup Guide

## Required API Keys

### 1. Binance API (REQUIRED for Trading)
**Location:** `trading_bot/api/binance.py`

**Required Variables:**
- `BINANCE_API_KEY` - Your Binance API key
- `BINANCE_SECRET_KEY` - Your Binance secret key

**How to get:**
1. Go to https://www.binance.com/en/my/settings/api-management
2. Create a new API key
3. Copy both the API key and Secret key
4. **Important:** Enable "Enable Spot & Margin Trading" permission

**Add to `.env`:**
```bash
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_SECRET_KEY=your_actual_secret_key_here
```

### 2. OpenAI API (REQUIRED for AI Agent)
**Location:** `rag_engine/config.py`

**Required Variables:**
- `OPENAI_API_KEY` - Your OpenAI API key

**How to get:**
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key

**Add to `.env`:**
```bash
OPENAI_API_KEY=sk-your_actual_key_here
```

### 3. Security Key (REQUIRED)
**Location:** `trading_api/main.py`

**Required Variables:**
- `SECRET_KEY` - Random secret for JWT token signing

**Generate:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Add to `.env`:**
```bash
SECRET_KEY=your_generated_secret_key_here
```

## Optional API Keys

### 4. Pinecone API (OPTIONAL - uses local store if not set)
**Location:** `rag_engine/config.py`

**Optional Variables:**
- `PINECONE_API_KEY` - Your Pinecone API key
- `PINECONE_ENVIRONMENT` - Default: `us-west1-gcp`
- `PINECONE_INDEX_NAME` - Default: `financial-news`

**How to get:**
1. Go to https://app.pinecone.io/
2. Create an account and get your API key

**Add to `.env` (optional):**
```bash
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=financial-news
```

**Note:** If you don't set `PINECONE_API_KEY`, the system will automatically use a local vector store.

### 5. Email Configuration (OPTIONAL - for password reset)
**Location:** `trading_api/main.py`

**Optional Variables:**
- `SMTP_HOST` - SMTP server (e.g., `smtp.gmail.com`)
- `SMTP_PORT` - SMTP port (e.g., `587`)
- `SMTP_USER` - Your email address
- `SMTP_PASS` - Your email app password
- `SMTP_FROM` - From email address

**Add to `.env` (optional):**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_FROM=your_email@gmail.com
```

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API keys:**
   ```bash
   # Required
   BINANCE_API_KEY=your_key
   BINANCE_SECRET_KEY=your_secret
   OPENAI_API_KEY=your_key
   SECRET_KEY=your_generated_key
   
   # Optional
   PINECONE_API_KEY=your_key  # or leave empty for local store
   ```

3. **Verify your `.env` file is loaded:**
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('BINANCE_API_KEY:', 'SET' if os.getenv('BINANCE_API_KEY') else 'NOT SET')"
   ```

## Files That Read Environment Variables

1. **`trading_bot/api/binance.py`**
   - Reads: `BINANCE_API_KEY`, `BINANCE_SECRET_KEY`
   - **Required for:** Real trading, price fetching

2. **`rag_engine/config.py`**
   - Reads: `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, `PINECONE_INDEX_NAME`, `USE_LOCAL_STORE`
   - **Required for:** AI agent, market analysis

3. **`trading_api/main.py`**
   - Reads: `SECRET_KEY`, `SMTP_*` variables
   - **Required for:** Authentication, password reset

4. **`run_system.py`**
   - Reads: `PINECONE_API_KEY` (to decide local vs Pinecone store)

## Verification

After setting up your `.env` file, verify it works:

```bash
# Test Binance connection
python -c "from trading_bot.api.binance import get_binance_api; api = get_binance_api(); print('Binance API:', 'Connected' if api else 'Not configured')"

# Test OpenAI connection
python -c "from rag_engine.config import RAGConfig; config = RAGConfig(); print('OpenAI API:', 'Set' if config.OPENAI_API_KEY else 'Not set')"
```

## Troubleshooting

**Error: "BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables must be set"**
- Make sure your `.env` file is in the project root directory
- Verify the variable names are exactly `BINANCE_API_KEY` and `BINANCE_SECRET_KEY`
- Restart your Python processes after adding the keys

**Error: "OPENAI_API_KEY not found"**
- Check that your `.env` file has `OPENAI_API_KEY=sk-...`
- Make sure you're using `python-dotenv` and calling `load_dotenv()`

**System uses local store instead of Pinecone:**
- This is normal if `PINECONE_API_KEY` is not set
- Local store works fine for development
- Set `PINECONE_API_KEY` if you want cloud vector storage



