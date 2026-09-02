"""
Main entry point for the Samsung Phone Query and Review System.
Usage:
    python run.py seed        # Seed database with fallback data
    python run.py scrape      # Scrape from GSMArena (requires internet)
    python run.py cli         # Run CLI chatbot
    python run.py api         # Start FastAPI server
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_seed():
    from scraper.seed_data import seed_database
    seed_database()


def cmd_scrape():
    from scraper.gsmarena_scraper import scrape_all_phones
    from config import SAMSUNG_PHONES
    scrape_all_phones(SAMSUNG_PHONES)


def cmd_cli():
    from chatbot.chatbot_cli import run_cli
    run_cli()


def cmd_api():
    import uvicorn
    from config import API_HOST, API_PORT
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    commands = {
        "seed": cmd_seed,
        "scrape": cmd_scrape,
        "cli": cmd_cli,
        "api": cmd_api,
    }
    fn = commands.get(command)
    if fn:
        fn()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)