# Django Channels Consumer Helpers

This project provides a collection of useful decorators and utilities to enhance Django Channels consumers, making it easier to implement background workers, rate limiting, and task management in your WebSocket applications.

## Features

- **Background Task Management**: Control execution flow of background tasks with decorators
- **Rate Limiting**: Prevent tasks from executing too frequently
- **Task Requeuing**: Automatically requeue tasks with failure handling
- **Support for Both Sync and Async Consumers**: Decorators intelligently handle both synchronous and asynchronous code

## Available Decorators

### `rate_limiter`

Limits how frequently a task can be executed. Automatically detects whether your consumer method is sync or async.

```python
from workers.consumer_decorators import rate_limiter

class RateLimitedExecutor(SyncConsumer):
    @rate_limiter(min_time_between_runs=5)  # Minimum 5 seconds between runs
    def test_print(self, message):
        print("Received: " + message["name"])

# Also works with AsyncConsumer
class AsyncRateLimitedExecutor(AsyncConsumer):
    @rate_limiter(min_time_between_runs=5)
    async def test_print(self, message):
        print("Received: " + message["name"])
```

### `requeue_task`

Handles task failures by examining exceptions and optionally requeuing the task for retry.

```python
from workers.consumer_decorators import requeue_task

class AsyncRequeableTask(AsyncConsumer):
    @requeue_task(max_retries=3, delay=2)
    async def my_task(self, message):
        # Task implementation that might fail
        # If it fails, the decorator will handle requeuing
```

### `run_continously`

Runs a task continuously in the background with control over execution flow.

```python
from workers.consumer_decorators import run_continously

class AsyncCronStyleExecutor(AsyncConsumer):
    @run_continously(interval=3)
    async def background_task(self):
        # This code will run continuously
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/username/django-channels-consumer-helpers.git
```

2. Install in your Django project:
```bash
pip install -e /path/to/django-channels-consumer-helpers
```

3. Add to your Django project's settings:
```python
INSTALLED_APPS = [
    # ...
    'consumer_helpers',
    # ...
]
```

## Requirements

- Django 3.2+
- Channels 3.0+
- Python 3.9+

## Usage Notes

- Decorators automatically detect if your consumer methods are synchronous or asynchronous
- Use appropriate consumer types (SyncConsumer or AsyncConsumer) based on your application needs
- When using `rate_limiter` with SyncConsumer, be aware that time.sleep() will block the thread

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.