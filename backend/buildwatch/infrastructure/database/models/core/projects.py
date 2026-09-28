from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from buildwatch.infrastructure.database.models.base import Base
from buildwatch.infrastructure.database.models.mixins import (
    CreatedAtMixin,
    DeadlinesMixin,
)

if TYPE_CHECKING:
    from buildwatch.infrastructure.database.models.core.stages import StagesORM


class ProjectTypesORM(Base, CreatedAtMixin):
    """Тип строительного проекта"""

    __tablename__ = "project_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(31))

    projects: Mapped[list[ProjectsORM]] = relationship(
        back_populates="type", lazy="selectin"
    )

    work_type_links: Mapped[list[ProjectTypesWorkTypesORM]] = relationship(
        back_populates="project_type",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    work_types: AssociationProxy[list[WorkTypesORM]] = association_proxy(
        "work_type_links", "work_type"
    )


class ProjectsORM(Base, CreatedAtMixin, DeadlinesMixin):
    """Строительный проект"""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(63))

    type_id: Mapped[int] = mapped_column(
        ForeignKey("project_types.id", ondelete="RESTRICT")
    )

    type: Mapped[ProjectTypesORM] = relationship(
        back_populates="projects", lazy="joined"
    )
    stages: Mapped[list[StagesORM]] = relationship(
        back_populates="project", lazy="selectin", cascade="all, delete-orphan"
    )


class WorkTypesORM(Base, CreatedAtMixin):
    """Тип строительных работ с иерархией"""

    __tablename__ = "work_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_types.id", ondelete="SET NULL"),
        default=None,
    )
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str | None] = mapped_column(String(31))

    parent: Mapped[WorkTypesORM | None] = relationship(
        back_populates="children",
        remote_side="WorkTypesORM.id",
        lazy="joined",
    )
    children: Mapped[list[WorkTypesORM]] = relationship(
        back_populates="parent",
        cascade="all",
        lazy="selectin",
    )

    project_type_links: Mapped[list[ProjectTypesWorkTypesORM]] = relationship(
        back_populates="work_type",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    project_types: AssociationProxy[list[ProjectTypesORM]] = association_proxy(
        "project_type_links", "project_type"
    )


class ProjectTypesWorkTypesORM(Base, CreatedAtMixin):
    """Связь типа проекта и типа работ"""

    __tablename__ = "project_types_work_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_type_id: Mapped[int] = mapped_column(
        ForeignKey("project_types.id", ondelete="CASCADE")
    )
    work_type_id: Mapped[int] = mapped_column(
        ForeignKey("work_types.id", ondelete="CASCADE")
    )

    __table_args__ = (
        UniqueConstraint(
            "project_type_id", "work_type_id", name="uq_project_type_work_type"
        ),
    )

    project_type: Mapped[ProjectTypesORM] = relationship(
        back_populates="work_type_links", lazy="joined"
    )
    work_type: Mapped[WorkTypesORM] = relationship(
        back_populates="project_type_links", lazy="joined"
    )
