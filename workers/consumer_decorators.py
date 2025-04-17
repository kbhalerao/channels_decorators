import asyncio
import inspect
import logging
import time
import traceback
from functools import wraps
from typing import Callable, Any
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def _handle_task_error(
        func_name: str,
        error: Exception,
        channel_name: str,
        message: dict,
        retries: int,
        max_retries: int,
        delay: int
) -> bool:
    """Helper function to log error information and display traceback."""
    tb_lines = traceback.format_tb(error.__traceback__)
    logger.error(f"Error occurred in function {func_name}: {error}")
    logger.info(f"Requeuing task on channel layer '{channel_name}' again in {delay} seconds...")

    if retries >= max_retries:
        logger.error("Maximum retries reached. Task failed.")
        logger.error("Traceback (last 10 lines): \n" + "".join(tb_lines[-10:]))
        return False
    return True


def _examine_task(func, *args):
    """Helper function to extract channel name and message from task."""
    channel_name = args[0].scope['channel']
    message = args[1] if len(args) > 1 else {}
    current_retries = message.get('retries', 0)
    if current_retries > 0:
        logger.info(f"Retrying task {func.__name__} attempt {current_retries + 1}...")
    return channel_name, current_retries, message


def requeue_task(max_retries: int = 3, delay: int = 10) -> Callable:
    """
    A decorator for wrapping background worker functions (both sync and async).
    Provides the ability to retry the function for a specified number of times.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Delay in seconds before retrying (default: 10)

    Returns:
        Decorated function with retry capability

    Raises:
        ValueError: If channel_name is not provided
    """

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            channel_name, current_retries, message = _examine_task(func, *args)

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                should_retry = _handle_task_error(
                    func.__name__, e, channel_name, message,
                    current_retries, max_retries, delay
                )

                if should_retry:
                    await asyncio.sleep(delay)
                    message["retries"] = current_retries + 1
                    await get_channel_layer().send(channel_name, message)
                return None

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            channel_name, current_retries, message = _examine_task(func, *args)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                should_retry = _handle_task_error(
                    func.__name__, e, channel_name, message,
                    current_retries, max_retries, delay
                )

                if should_retry:
                    time.sleep(delay)
                    message["retries"] = current_retries + 1
                    asyncio.run(get_channel_layer().send(channel_name, message))
                return None

        return async_wrapper if is_async else sync_wrapper

    return decorator
