from .consumer_decorators import requeue_task
from channels.consumer import AsyncConsumer, SyncConsumer


class PrintAsyncConsumer(AsyncConsumer):
    """
    An example consumer that simply pretends to do some work
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