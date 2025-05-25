import logging

LOGGER = logging.getLogger(__name__)


def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] - <%(name)s> - %(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler()],
    )


def initialize() -> None:
    """Initialize the application."""
    setup_logging()


initialize()
