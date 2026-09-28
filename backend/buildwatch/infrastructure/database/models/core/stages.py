from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from buildwatch.infrastructure.database.models.base import Base
from buildwatch.infrastructure.database.models.mixins import (
    CreatedAtMixin,
    DeadlinesMixin,
)

if TYPE_CHECKING:
    from buildwatch.infrastructure.database.models.core.projects import (
        ProjectsORM,
        WorkTypesORM,
    )
    from buildwatch.infrastructure.database.models.core.techniques import (
        StageTechniquesORM,
        TechniquesORM,
    )


class StagesORM(Base, DeadlinesMixin, CreatedAtMixin):
    """Этап строительства с иерархией и привязкой к проекту"""

    __tablename__ = "stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("stages.id", ondelete="SET NULL"),
        default=None,
    )
    work_type_id: Mapped[int] = mapped_column(
        ForeignKey("work_types.id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(255))

    parent: Mapped[StagesORM | None] = relationship(
        back_populates="children",
        remote_side="StagesORM.id",
        lazy="joined",
    )
    children: Mapped[list[StagesORM]] = relationship(
        back_populates="parent",
        cascade="all",
        lazy="selectin",
    )
    project: Mapped[ProjectsORM] = relationship(back_populates="stages", lazy="joined")
    work_type: Mapped[WorkTypesORM] = relationship(lazy="joined")

    technique_links: Mapped[list[StageTechniquesORM]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    techniques: AssociationProxy[list[TechniquesORM]] = association_proxy(
        "technique_links", "technique"
    )
