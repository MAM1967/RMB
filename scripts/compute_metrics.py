 """
 Entrypoint script for computing weekly metrics.
 """

 from __future__ import annotations

 from backend.src.logging_config import configure_logging, get_logger

 logger = get_logger()


 def main() -> None:
    configure_logging()
    # TODO: implement real metrics computation against Supabase.
    logger.info("metrics_compute_started")
    logger.info("metrics_compute_completed")


 if __name__ == "__main__":
    main()

