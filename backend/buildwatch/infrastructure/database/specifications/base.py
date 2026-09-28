from sqlalchemy import Select, asc, desc as sa_desc, false


class Specification:
    """Базовый класс спецификации"""

    def apply(self, query: Select) -> Select:
        """Применение спецификации к SQLAlchemy-запросу"""
        ...


class OrderBySpec(Specification):
    """Сортировка по полю"""

    def __init__(self, col, desc: bool = False, nulls_last: bool = False):
        self.col = col
        self.desc = desc
        self.nulls_last = nulls_last

    def apply(self, query: Select) -> Select:
        """Сортировка запроса по указанному полю"""
        direction = sa_desc(self.col) if self.desc else asc(self.col)
        if self.nulls_last:
            direction = direction.nulls_last()
        return query.order_by(direction)


class EqualsSpec(Specification):
    """Точное совпадение значения столбца."""

    def __init__(self, col, value):
        self.col = col
        self.value = value

    def apply(self, query: Select) -> Select:
        return query.where(self.col == self.value)


class LikeSpec(Specification):
    """Поиск LIKE по конкретному столбцу"""

    def __init__(self, col, value: str | None, case_insensitive: bool = True):
        self.col = col
        self.value = value
        self.case_insensitive = case_insensitive

    def apply(self, query: Select) -> Select:
        """Применение фильтра LIKE к запросу"""
        search_value = f"%{self.value}%" if self.value else "%"
        column = self.col
        if self.case_insensitive:
            return query.filter(column.ilike(search_value))
        return query.filter(column.like(search_value))


class LimitOffsetSpec(Specification):
    """Спецификация пагинации"""

    def __init__(self, limit: int, offset: int):
        self.limit = limit
        self.offset = offset

    def apply(self, query: Select) -> Select:
        """Применение limit и offset к запросу"""
        return query.limit(self.limit).offset(self.offset)


class InSpec(Specification):
    """Спецификация фильтрации по списку значений (WHERE col IN ...)"""

    def __init__(self, col, values: list):
        self.col = col
        self.values = values

    def apply(self, query: Select) -> Select:
        """Применение фильтра IN к запросу"""
        if not self.values:
            return query.filter(false())
        return query.filter(self.col.in_(self.values))


class DateRangeSpec(Specification):
    """Фильтрация по диапазону дат (start_dt >= start, end_dt <= end)"""

    def __init__(self, start_col, end_col, start_date=None, end_date=None):
        self.start_col = start_col
        self.end_col = end_col
        self.start_date = start_date
        self.end_date = end_date

    def apply(self, query: Select) -> Select:
        """Применение фильтра диапазона дат к запросу"""
        if self.start_date:
            query = query.filter(self.start_col >= self.start_date)
        if self.end_date:
            query = query.filter(self.end_col <= self.end_date)
        return query


class IntervalOverlapSpec(Specification):
    """Этапы, касающиеся интервала [from, to]: start <= to AND end >= from"""

    def __init__(self, start_col, end_col, from_date=None, to_date=None):
        self.start_col = start_col
        self.end_col = end_col
        self.from_date = from_date
        self.to_date = to_date

    def apply(self, query: Select) -> Select:
        """Пересечение интервалов — включает частичное попадание"""
        from datetime import datetime, time, timezone

        if self.from_date is not None:
            # date -> datetime 00:00 UTC для сравнения с DateTime(timezone=True)
            from_val = self.from_date
            if not isinstance(from_val, datetime):
                from_val = datetime.combine(from_val, time.min, tzinfo=timezone.utc)
            query = query.filter(self.end_col >= from_val)
        if self.to_date is not None:
            to_val = self.to_date
            if not isinstance(to_val, datetime):
                to_val = datetime.combine(to_val, time.max, tzinfo=timezone.utc)
            query = query.filter(self.start_col <= to_val)
        return query
