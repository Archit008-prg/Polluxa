import sys
from pathlib import Path
from datetime import date, timedelta

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import engine, SessionLocal, init_database
from src.database.models import DimDate
from config.logging_config import get_logger

logger = get_logger("init_db")

def seed_calendar_dimension(start_year: int = 2025, end_year: int = 2027):
    """Populates dim_date table with calendar dates."""
    db = SessionLocal()
    try:
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        curr_date = start_date
        
        records = []
        existing_keys = set(r[0] for r in db.query(DimDate.date_key).all())
        
        while curr_date <= end_date:
            date_key = int(curr_date.strftime("%Y%m%d"))
            if date_key not in existing_keys:
                records.append(DimDate(
                    date_key=date_key,
                    full_date=curr_date,
                    day_of_week=curr_date.strftime("%A"),
                    month=curr_date.month,
                    month_name=curr_date.strftime("%B"),
                    quarter=(curr_date.month - 1) // 3 + 1,
                    year=curr_date.year,
                    is_weekend=curr_date.weekday() >= 5
                ))
            curr_date += timedelta(days=1)
            
        if records:
            db.bulk_save_objects(records)
            db.commit()
            logger.info(f"Seeded {len(records)} calendar records into dim_date.")
        else:
            logger.info("dim_date is already fully seeded.")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed dim_date: {e}")
        raise e
    finally:
        db.close()

def main():
    logger.info("Initializing database tables...")
    init_database()
    logger.info("Seeding dimension tables...")
    seed_calendar_dimension()
    logger.info("Database initialization complete!")

if __name__ == "__main__":
    main()
