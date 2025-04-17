from django.test import TestCase
from django.urls import reverse
from .consumers import PrintSyncConsumer, PrintAsyncConsumer
from channels.testing import ApplicationCommunicator
import asyncio


# Create your tests here.

class ExamplePostViewTest(TestCase):
    def test_example_post_view(self):
        url = reverse("example_post_view")

        # Test successful request
        response = self.client.post(
            url,
            data='{"name": "John", "email": "john@example.com"}',
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"message": "Received data: name=John, email=john@example.com"}
        )


class PrintSyncConsumerTest(TestCase):
    async def test_print_consumer(self):
        # Create an ApplicationCommunicator for the consumer
        communicator = ApplicationCommunicator(PrintSyncConsumer.as_asgi(),
                                               {"type": "test.print",
                                                "name": "John",
                                                "email": "john@example.com"})

        # Call the consumer with the message
        await communicator.send_input({"type": "test.print", "name": "John", "email": "john@example.com"})

        # Allow for messages or side effects (stdout in this case) to process
        await asyncio.sleep(0.1)

    async def test_print_async_consumer(self):
        # Create an ApplicationCommunicator for the consumer
        communicator = ApplicationCommunicator(PrintAsyncConsumer.as_asgi(),
                                               {"type": "test.print",
                                                "name": "John",
                                                "email": "john@example.com"})

        # Call the consumer with the message
        await communicator.send_input({"type": "test.print", "name": "John", "email": "john@example.com"})

        # Allow for messages or side effects (stdout in this case) to process
        await asyncio.sleep(0.1)
