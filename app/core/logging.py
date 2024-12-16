import logging
import watchtower
from app.core.config import settings


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # CloudWatch Handler (if configured)
    if settings.CLOUDWATCH_LOG_GROUP and settings.AWS_ACCESS_KEY_ID:
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group=settings.CLOUDWATCH_LOG_GROUP,
            stream_name=settings.CLOUDWATCH_LOG_STREAM,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_region_name=settings.AWS_REGION
        )
        cloudwatch_handler.setLevel(settings.LOG_LEVEL)
        logger.addHandler(cloudwatch_handler)

    return logger