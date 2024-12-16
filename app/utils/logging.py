import logging

import watchtower

from app.core.config import settings


def setup_logger():
    # Create logger
    logger = logging.getLogger("api")
    logger.setLevel(settings.LOG_LEVEL)

    # Create formatters
    json_formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s", '
        '"path":"%(pathname)s", "line":%(lineno)d, %(extra)s}'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)

    # CloudWatch handler (if configured)
    if settings.CLOUDWATCH_LOG_GROUP and settings.AWS_ACCESS_KEY_ID:
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group=settings.CLOUDWATCH_LOG_GROUP,
            stream_name=settings.CLOUDWATCH_LOG_STREAM,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_region_name=settings.AWS_REGION
        )
        cloudwatch_handler.setFormatter(json_formatter)
        logger.addHandler(cloudwatch_handler)

    return logger


# Create logger instance
logger = setup_logger()
