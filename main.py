import argparse

from database.connection import init_db
from scheduler.job_runner import run_scraper_job, start_scheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="SERCOP scraper")
    parser.add_argument("--once", action="store_true", help="Run the scraper once and exit")
    parser.add_argument("--web", action="store_true", help="Start the quotation web interface")
    args = parser.parse_args()

    init_db()
    if args.web:
        from web.app import run_web_app

        run_web_app()
    elif args.once:
        run_scraper_job()
    else:
        start_scheduler()


if __name__ == "__main__":
    main()
