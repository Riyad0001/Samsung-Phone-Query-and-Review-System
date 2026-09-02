# Samsung Phone Query and Review System

A FastAPI-based Samsung phone catalogue with a browser dashboard, phone specification search, comparisons, chatbot queries, and generated product reviews.

The application stores phone data in SQLite. Records can be loaded from the included fallback dataset or collected from GSMArena. The API also exposes a query engine and a multi-agent review workflow.

## Features

- Browse, search, sort, and delete Samsung phone records from the web dashboard.
- Seed the database with fallback phone data for reliable offline setup.
- Scrape configured Samsung phone pages from GSMArena.
- Ask questions about phone specifications, including display, camera, battery, processor, price, and performance.
- Compare two phones by specification.
- Generate rule-based product reviews with pros, cons, ratings, and a score.
- Use the optional embedding and FAISS dependencies for semantic retrieval.
- Access the interactive FastAPI documentation at `/docs`.

## Requirements

- Python 3.10 or newer is recommended.
- Internet access is needed to install dependencies and use the GSMArena scraper.
- The dependencies include PyTorch, Transformers, Sentence Transformers, and FAISS, so installation may take some time and disk space.

## Installation

From the project directory, create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell prevents activation, run this once for the current user or activate the environment from another shell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Load Data

Seed the local SQLite database with the built-in fallback records:

```powershell
python run.py seed
```

To scrape the Samsung models configured in `config.py`:

```powershell
python run.py scrape
```

The API and frontend scraper use the fallback dataset automatically if GSMArena is unavailable or rate-limits the request.

## Run the Application

Start the FastAPI server:

```powershell
python run.py api
```

Open the dashboard at [http://localhost:8888/ui/](http://localhost:8888/ui/). The API root is available at [http://localhost:8888/api](http://localhost:8888/api), and interactive documentation is available at [http://localhost:8888/docs](http://localhost:8888/docs).

The server initializes the database and query services at startup. If the database is empty, run the seed command or use **Seed Database** in the dashboard.

## CLI Chatbot

Run the command-line chatbot with:

```powershell
python run.py cli
```

The CLI reads phone data from the same local database as the API.

## API Overview

All request bodies that accept a query use this shape:

```json
{
  "query": "Compare Galaxy S24 and Galaxy S23"
}
```

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/phones` | List all phones |
| `GET` | `/api/phone/{name}` | Get one phone's specifications |
| `DELETE` | `/api/phone/{name}` | Delete one phone |
| `DELETE` | `/api/phones` | Delete all phones |
| `POST` | `/api/query` | Ask a question about Samsung phones |
| `POST` | `/api/review` | Generate a product or comparison review |
| `POST` | `/api/compare` | Compare two phones |
| `POST` | `/api/scrape` | Scrape configured GSMArena pages |
| `POST` | `/api/seed` | Insert fallback phone data |

Example request:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8888/api/query `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{"query":"What are the camera specs of Galaxy S23?"}'
```

Convenience routes `/`, `/phones`, and `/phone/{name}` redirect to the frontend or corresponding API routes.

## Project Structure

```text
api/        FastAPI application and HTTP routes
agents/     Specification and review agents
chatbot/    CLI chatbot, query engine, and RAG-oriented response logic
database/   SQLAlchemy model, engine, and session helpers
frontend/   Static HTML, CSS, and JavaScript dashboard
scraper/    GSMArena scraper and fallback seed data
config.py   Database, scraper, model, and server configuration
run.py      Command-line entry point
test_*.py   API, frontend, redirect, deletion, and integration checks
```

## Configuration

The defaults in `config.py` can be overridden with environment variables:

- `DATABASE_URL`: SQLAlchemy database URL. Defaults to the local `samsung_phones.db` file.
- `API_HOST`: API bind address. Defaults to `0.0.0.0`.
- `API_PORT`: API port. Defaults to `8888`.

The configured scrape targets and Hugging Face model names are also defined in `config.py`.

## Testing

Run the test files with:

```powershell
python -m pytest
```

The test scripts also include standalone HTTP checks and may start temporary local servers on ports `8765` and `8769`.

## Notes

- The database is created automatically when the application starts.
- Seeding is idempotent for records with the same GSMArena URL.
- Scraping external websites can be slow, fail, or be rate-limited; use the seed command when deterministic local data is preferred."# Samsung-Phone-Query-and-Review-System" 
