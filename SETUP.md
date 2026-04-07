# Scrapped - Setup Guide

## Prerequisites

Before running the application, you need to install/configure:

### 1. Python (3.11+)
```powershell
# Download and install from https://www.python.org/downloads/
# Or via winget: winget install Python.Python.3.11
```

### 2. Poetry (Python package manager)
```powershell
# Via pip:
pip install poetry

# Or via winget:
winget install Poetry.Poetry
```

### 3. Redis (Celery broker)
```powershell
# Option A: Via Chocolatey (if installed)
choco install redis-64

# Option B: Download from https://github.com/microsoftarchive/redis/releases
# Or use Docker (see below)
```

### 4. PostgreSQL
```powershell
# Option A: Via Chocolatey
choco install postgresql

# Option B: Download from https://www.postgresql.org/download/
```

## Quick Start (Using Docker)

The easiest way to start infrastructure services:

```powershell
# Start Redis and PostgreSQL via Docker
docker run -d --name scrapped-redis -p 6379:6379 redis:alpine
docker run -d --name scrapped-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=scrapped -p 5432:5432 postgres:15
```

## Setup Instructions

### 1. Install Backend Dependencies
```powershell
cd backend
poetry install
```

### 2. Install Frontend Dependencies
```powershell
cd frontend
npm install
```

### 3. Create Environment File
Copy `backend/.env.example` to `backend/.env` and fill in:

```env
# App Settings
APP_NAME=Scrapped
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scrapped

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# JWT
JWT_SECRET_KEY=jwt-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# LinkedIn (optional - for scraping)
LINKEDIN_COOKIE_LI_AT=

# CNPJ Database (SQLite)
CNPJ_DB_PATH=../data/cnpj.db

# NLP Models
SPACY_MODEL=pt_core_news_lg
SENTENCE_TRANSFORMER_MODEL=paraphrase-multilingual-mpnet-base-v2
```

### 4. Download CNPJ Database
The SQLite database with Brazilian company data needs to be downloaded separately.

Option A - Using the cnpj-sqlite tool:
```powershell
# Follow instructions at: https://github.com/rictom/cnpj-sqlite
```

Option B - Pre-built database:
```powershell
# Download from: https://www.kaggle.com/datasets/ougabriel/brazilian-companies-cnpj-database
# Place as: backend/data/cnpj.db
```

## Running the Application

### Start Backend
```powershell
cd backend
poetry run uvicorn app.main:app --reload --port 8000
```

### Start Frontend
```powershell
cd frontend
npm run dev
```

### Start Celery Worker (for background tasks)
```powershell
cd backend
poetry run celery -A app.tasks.scraper worker --loglevel=info
```

## Google OAuth Setup

1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API (or People API)
4. Create OAuth 2.0 credentials
5. Set redirect URI to: `http://localhost:8000/auth/callback`
6. Add authorized JavaScript origins: `http://localhost:5173`