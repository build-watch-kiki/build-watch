from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from buildwatch.infrastructure.database.models.base import Base
from buildwatch.infrastructure.database.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from buildwatch.infrastructure.database.models.core.stages import StagesORM


class TechniquesORM(Base, CreatedAtMixin):
    """Строительная техника"""

    __tablename__ = "techniques"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(127))
    name_ru: Mapped[str] = mapped_column(String(127))
    color: Mapped[str] = mapped_column(String(7), nullable=False, server_default="#FF0000")

    stage_links: Mapped[list[StageTechniquesORM]] = relationship(
        back_populates="technique",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    stages: AssociationProxy[list[StagesORM]] = association_proxy(
        "stage_links", "stage"
    )


class StageTechniquesORM(Base, CreatedAtMixin):
    """Связь этапа и техники"""

    __tablename__ = "stage_techniques"

    id: Mapped[int] = mapped_column(primary_key=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id", ondelete="CASCADE"))
    technique_id: Mapped[int] = mapped_column(
        ForeignKey("techniques.id", ondelete="CASCADE")
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("stage_id", "technique_id", name="uq_stage_id_technique_id"),
        CheckConstraint("quantity >= 1", name="ck_stage_techniques_quantity_positive"),
    )

    stage: Mapped[StagesORM] = relationship(
        back_populates="technique_links", lazy="joined"
    )
    technique: Mapped[TechniquesORM] = relationship(
        back_populates="stage_links", lazy="joined"
    )
