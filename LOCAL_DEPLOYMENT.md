# Local Deployment Guide - Finance Tracker

This guide explains how to run the Finance Tracker application locally for development.

## Quick Start

### 1. Clone and Setup

```bash
cd /Users/njpinton/projects/git/finance
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Application

**Option A: Using the startup script (RECOMMENDED)**

```bash
./start_local.sh
```

**Option B: Manual startup**

```bash
source .venv/bin/activate
python run.py
```

The application will be available at `http://localhost:5001`

## What's Configured for Local Development

### ✅ Automatic Configuration

The following are now configured automatically for local development:

- **SECRET_KEY**: Uses `dev-secret-key-change-in-production` if not set
- **FLASK_ENV**: Defaults to `development` (debug mode enabled)
- **DATABASE**: Uses SQLite at `data/finance.db` by default
- **PORT**: Defaults to 5001 (customizable via `FLASK_PORT` env var)

### ✅ No Manual Environment Variables Needed

You **do not** need to set these anymore:
- `SECRET_KEY` (auto-generated for dev)
- `DATABASE_URL` (auto-detected as SQLite)

### ⚠️ Optional Environment Variables

If you want to customize behavior:

```bash
# Use a different port
export FLASK_PORT=5002
./start_local.sh

# Use a custom SECRET_KEY (for security)
export SECRET_KEY="your-custom-secret-key"
./start_local.sh

# Use production mode (not recommended locally)
export FLASK_ENV=production
./start_local.sh
```

## Database

The application uses SQLite for local development:

- **Location**: `data/finance.db`
- **Auto-creation**: The database is created automatically on first run
- **Real BDO Deals**: 10 real credit card deals are pre-loaded in the database

## Features Available Locally

- ✅ User registration and authentication
- ✅ Dashboard with financial overview
- ✅ Transaction management
- ✅ Budget tracking
- ✅ **Real BDO credit card deals** (10 campaigns with live images)
- ✅ Investment tracking
- ✅ Receipt OCR (requires `GOOGLE_API_KEY` env var for Gemini API)
- ✅ All other features

## Accessing the Application

Once the server is running:

- **Login/Register**: http://localhost:5001/auth/register
- **Dashboard**: http://localhost:5001/dashboard
- **Deals Page**: http://localhost:5001/deals
- **Transactions**: http://localhost:5001/transactions
- **API Endpoint**: http://localhost:5001/api/deals (requires authentication)

## Development Notes

### Debug Mode

Debug mode is enabled by default in local development:
- Code changes automatically reload the server
- Detailed error pages are shown
- Debugger is available in the browser

### Database Location

If you need to reset the database:

```bash
rm data/finance.db
./start_local.sh
```

The application will recreate the database on first run.

### Testing

To test the deals feature with real BDO data:

1. Start the server: `./start_local.sh`
2. Register a new user at http://localhost:5001/auth/register
3. Log in and navigate to http://localhost:5001/deals
4. You'll see 10 real BDO credit card promotional campaigns with live images

## Troubleshooting

### "Address already in use" Error

```bash
# Kill process on port 5001
lsof -ti:5001 | xargs kill -9
./start_local.sh
```

### "No module named 'flask'" Error

Make sure virtual environment is activated:

```bash
source .venv/bin/activate
pip install -r requirements.txt
./start_local.sh
```

### Database Connection Issues

```bash
# Remove old database and restart
rm data/finance.db
./start_local.sh
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Environment mode (development/production) |
| `FLASK_PORT` | `5001` | Port to run server on |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Session encryption key |
| `DATABASE_URL` | `sqlite:///data/finance.db` | Database connection string |
| `GOOGLE_API_KEY` | (optional) | Gemini API key for receipt OCR |
| `DEFAULT_CURRENCY` | `PHP` | Default currency for the application |

## Security Warning

⚠️ **IMPORTANT**: The development `SECRET_KEY` is insecure.

**For production deployment:**
1. Set a strong `SECRET_KEY` via environment variables
2. Change `FLASK_ENV` to `production`
3. Use PostgreSQL or other production database
4. Use HTTPS

See `deploy.sh` for production deployment instructions.

## Next Steps

- For Cloud Run deployment, see `deploy.sh`
- For production configuration, update environment variables in Cloud Secret Manager
- For real data synchronization, use the BDO deals scraper in `services/deals/scrapers/`
