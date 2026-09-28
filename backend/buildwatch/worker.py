"""Dedicated FastStream process for backend CV results."""

import logging

from faststream import FastStream

from buildwatch.infrastructure.broker import broker
import buildwatch.photos.worker  # noqa: F401 - register RabbitMQ consumers
from buildwatch.settings import get_settings

logging.basicConfig(level=get_settings().log.level)

app = FastStream(broker)
