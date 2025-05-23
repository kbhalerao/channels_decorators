"""
ASGI config for consumer_helpers project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'consumer_helpers.settings')

from workers.consumers import PrintSyncConsumer, PrintAsyncConsumer, RepeatedAsyncExecutor, RepeatedSyncExecutor, \
    RateLimitedAsyncExecutor, RateLimitedExecutor
from channels.routing import ProtocolTypeRouter, ChannelNameRouter

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "channel": ChannelNameRouter({
        "print-consumer": PrintSyncConsumer.as_asgi(),
        "aprint-consumer": PrintAsyncConsumer.as_asgi(),
        "arepeat": RepeatedAsyncExecutor.as_asgi(),
        "repeat": RepeatedSyncExecutor.as_asgi(),
        "throttle": RateLimitedExecutor.as_asgi(),
        "athrottle": RateLimitedAsyncExecutor.as_asgi(),
    }),
})
