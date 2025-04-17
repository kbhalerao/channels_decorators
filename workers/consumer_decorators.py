import asyncio
import inspect
import logging
import time
import traceback
from functools import wraps
from typing import Callable, Any
from channels.layers import get_channel_layer
from django.utils.timezone import now

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
    assert args[0].scope['type'] == 'channel', "These decorators can only be used on background tasks"
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


def run_continously(interval: int) -> Callable:
    """
    A decorator to run a function periodically. Useful for setting up a periodic task like a cron job.

    Please note that if the function passed to it raises an exception, the scheduler will stop running
    immediately.
    :param interval: Minimum interval between two successive runs of the function
    :return:
    """

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            channel_name, _, message = _examine_task(func, *args)
            while True:
                try:
                    message["last_run"] = now()
                    await func(*args, **kwargs)
                    message["last_run_successful"] = True
                    if (now() - message["last_run"]).total_seconds() < interval:
                        await asyncio.sleep(int(interval - (now() - message["last_run"]).total_seconds()) + 1)
                    else:
                        await get_channel_layer().send(channel_name, message)
                        break
                except Exception as e:
                    logger.error(f"Error occurred in function {func.__name__}: {e}. Exiting scheduler")
                    break


        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            channel_name, _, message = _examine_task(func, *args)
            while True:
                try:
                    message["last_run"] = now()
                    func(*args, **kwargs)
                    message["last_run_successful"] = True
                    if (now() - message["last_run"]).total_seconds() < interval:
                        time.sleep(int(interval - (now() - message["last_run"]).total_seconds()) + 1)
                    else:
                        asyncio.run(get_channel_layer().send(channel_name, message))
                        break
                except Exception as e:
                    logger.error(f"Error occurred in function {func.__name__}: {e}. Exiting scheduler")
                    break

        return async_wrapper if is_async else sync_wrapper

    return decorator


def rate_limiter(min_time_between_runs=1) -> Callable:
    """
    Limits how frequency a task can be run. Stores the last run
    time stamp in the consumer class.
    :param min_time_between_runs: in seconds
    :return:
    """
    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            consumer = args[0]
            last_run = getattr(consumer, f"last_run__{func.__name__}", None)
            if last_run is not None:
                if (now() - last_run).total_seconds() < min_time_between_runs:
                    logger.info(f"Task {func.__name__} is rate limited. Sleeping for {min_time_between_runs - (now() - last_run).total_seconds()} seconds")
                    await asyncio.sleep(min_time_between_runs - (now() - last_run).total_seconds())
            setattr(consumer, f"last_run__{func.__name__}", now())
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            consumer = args[0]
            last_run = getattr(consumer, f"last_run__{func.__name__}", None)
            if last_run is not None:
                if (now() - last_run).total_seconds() < min_time_between_runs:
                    logger.info(f"Task {func.__name__} is rate limited. Sleeping for {min_time_between_runs - (now() - last_run).total_seconds()} seconds")
                    time.sleep(min_time_between_runs - (now() - last_run).total_seconds())
            setattr(consumer, f"last_run__{func.__name__}", now())
            return func(*args, **kwargs)

        return async_wrapper if is_async else sync_wrapper
    return decorator

