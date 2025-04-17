from .consumer_decorators import requeue_task, run_continously, rate_limiter

from channels.consumer import AsyncConsumer, SyncConsumer


class PrintAsyncConsumer(AsyncConsumer):
    """
    An example consumer that simply pretends to do some work, but fails
    and has to be retried.
    """

    @requeue_task(max_retries=3, delay=2)
    async def test_print(self, message):
        print("Received: " + message["name"])
        print("Received: " + message["email"])

        assert False


class PrintSyncConsumer(SyncConsumer):
    """
    An example consumer that simply pretends to do some work
    """

    @requeue_task(max_retries=3, delay=2)
    def test_print(self, message):
        print("Received: " + message["name"])
        print("Received: " + message["email"])

        assert False


class RepeatedAsyncExecutor(AsyncConsumer):
    """
    send a message like this to kick it off:
    asyncio.run(channel_layer.send("arepeat", {
        "type": "test.print",
        "name": "test",
        "email": "email",
    }))

    """

    @run_continously(interval=3)
    async def test_print(self, message):
        print("Received: " + message["name"])
        print(f"Last ran at {message.get('last_run')}, with success={message.get('last_run_successful')}")


class RepeatedSyncExecutor(SyncConsumer):
    """
    send a message like this to kick it off:
    asyncio.run(channel_layer.send("repeat", {
        "type": "test.print",
        "name": "test",
        "email": "email",
    }))

    """

    @run_continously(interval=3)
    def test_print(self, message):
        print("Received: " + message["name"])
        print(f"Last ran at {message.get('last_run')}, with success={message.get('last_run_successful')}")


class RateLimitedExecutor(SyncConsumer):
    """
    Send multiple messages to kick it off, and watch it limit
    the execution rate.

    asyncio.run(channel_layer.send("throttle", {
        "type": "test.print",
        "name": "test",
        "email": "email",
    }))
    """

    @rate_limiter(min_time_between_runs=5)
    def test_print(self, message):
        print("Received: " + message["name"])


class RateLimitedAsyncExecutor(AsyncConsumer):
    """
    Send multiple messages to kick it off, and watch it limit
    the execution rate.

    asyncio.run(channel_layer.send("athrottle", {
        "type": "test.print",
        "name": "test",
        "email": "email",
    }))
    """

    @rate_limiter(min_time_between_runs=5)
    async def test_print(self, message):
        print("Received: " + message["name"])
