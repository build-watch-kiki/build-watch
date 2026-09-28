from faststream.rabbit import Channel, RabbitBroker, RabbitQueue

from buildwatch.settings import get_settings

settings = get_settings()

NEW_PHOTO_QUEUE = RabbitQueue(settings.broker.queue.new_photo, durable=True)
CV_RESULT_QUEUE = RabbitQueue(settings.broker.queue.cv_result, durable=True)
broker = RabbitBroker(
    settings.broker.RABBITMQ_DSN,
    default_channel=Channel(on_return_raises=True),
)
