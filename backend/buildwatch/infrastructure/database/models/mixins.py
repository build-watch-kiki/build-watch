from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class CreatedAtMixin:
    """Миксин с полем времени создания записи"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


class UpdatedAtMixin:
    """Миксин с полем времени обновления записи"""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now(),
    )


class DeadlinesMixin:
    """Миксин с интервалом дат и проверкой start_dt < end_dt"""

    start_dt: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_dt: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @declared_attr.directive
    def __table_args__(cls) -> tuple:
        return (
            CheckConstraint(
                "start_dt < end_dt", name=f"ck_{cls.__tablename__}_start_before_end"
            ),
        )
