import logging

from fastapi import status

logger = logging.getLogger(__name__)


class BuildWatchException(Exception):
    """Базовое исключение приложения с HTTP-статусом"""

    def __init__(
        self,
        detail: str = "Internal Server Error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)
        logger.error(self.detail)


class NotImplementedException(BuildWatchException):
    """Запрошенная операция не реализована"""

    def __init__(self):
        super().__init__(
            detail="Запрос еще не реализован",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
        )


class NotFoundException(BuildWatchException):
    """Запрошенный ресурс не найден"""

    def __init__(self, message: str | None = None):
        super().__init__(
            detail=message or "Не найдено",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class WrongDatesException(BuildWatchException):
    """Некорректный интервал дат"""

    def __init__(self, message: str | None = None):
        super().__init__(
            detail=message or "Дата начала не может совпадать с датой конца работ",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
