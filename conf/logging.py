import sys

from loguru import logger

from conf.settings import settings



# 配置应用统一使用的日志输出格式。
def setup_logger():
    logger.remove()

    logger.configure(extra={"module":"unknown"})
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        enqueue=False,
        backtrace=False,
        diagnose=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} |"
            "{level} |"
            "{extra[module]} |"
            "{message}"
        )
    )


app_logger = logger

