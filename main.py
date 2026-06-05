import argparse

from database.connection import init_db
from scheduler.job_runner import run_scraper_job, start_scheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="SERCOP scraper")
    parser.add_argument("--once", action="store_true", help="Run the scraper once and exit")
    args = parser.parse_args()

    init_db()
    if args.once:
        run_scraper_job()
    else:
        start_scheduler()


if __name__ == "__main__":
    main()
