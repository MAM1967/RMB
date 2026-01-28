 """
 Central logging configuration for the RMB backend.
 """

 import logging

 import structlog


 def configure_logging() -> None:
    """Configure structlog-based structured logging for the application."""
    logging.basicConfig(level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )


 def get_logger() -> structlog.types.WrappedLogger:
    """Return a structlog logger instance."""
    return structlog.get_logger()

