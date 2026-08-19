import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.init_db import main as init_db_main
from scripts.generate_synthetic_data import generate_synthetic_data
from src.pipeline.orchestrator import IngestionPipelineOrchestrator
from config.logging_config import get_logger

logger = get_logger("run_pipeline")

def main():
    logger.info("Initializing database...")
    init_db_main()
    
    logger.info("Generating synthetic batch dataset...")
    synthetic_events = generate_synthetic_data(days=7, include_bad_records=True)
    
    logger.info("Executing Ingestion Pipeline Orchestrator...")
    orchestrator = IngestionPipelineOrchestrator()
    run_meta = orchestrator.run_pipeline(raw_events=synthetic_events)
    
    logger.info(
        f"Pipeline Run Completed! Run ID: {run_meta.run_id} | "
        f"Rows Ingested: {run_meta.rows_ingested} | Rows Failed: {run_meta.rows_failed} | "
        f"Status: {run_meta.status}"
    )

if __name__ == "__main__":
    main()
