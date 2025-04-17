from asgiref.sync import async_to_sync
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from channels.layers import get_channel_layer
import json
import asyncio

@require_POST
def example_post_view(request):
    # Parse JSON data from POST request
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Retrieve data
    name = data.get("name", "")
    email = data.get("email", "")


    # Send name and email to background worker
    channel_layer = get_channel_layer()
    asyncio.run(channel_layer.send("print-consumer", {
        "type": "test.print",
        "name": "test",
        "email": "email",
    }))

    asyncio.run(channel_layer.send("aprint-consumer", {
        "type": "test.print",
        "name": "test",
        "email": "email",
    }))

# Example response
    return JsonResponse({"message": f"Received data: name={name}, email={email}"}, status=200)
