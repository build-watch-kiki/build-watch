import logging

from faststream import FastStream

from buildwatchcv.infrastructure.broker import broker

logging.basicConfig(level=logging.INFO)

app = FastStream(broker)


@app.after_startup
async def declare_queues() -> None:
    from buildwatchcv.infrastructure.broker import CV_RESULT_QUEUE, NEW_PHOTO_QUEUE

    # Гарантирует создание очередей до первого publish (сообщение теряется, если очереди нет)
    await broker.declare_queue(NEW_PHOTO_QUEUE)
    await broker.declare_queue(CV_RESULT_QUEUE)


@app.after_startup
async def warmup_model() -> None:
    """Прогреть настроенную модель до приёма фото, не прерывая запуск при сбое."""
    from buildwatchcv.services.model import warmup

    await warmup()
