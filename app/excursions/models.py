from datetime import datetime
from typing import Any

from database import Base, engine
from sqlalchemy import JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Excursion(Base):
    __tablename__ = "excursions"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False)
    people_amount: Mapped[int] = mapped_column(nullable=False)
    people_left: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False)
    image_url: Mapped[str] = mapped_column(nullable=False)

    # Добавляем связь с детальной информацией
    details: Mapped["ExcursionDetails"] = relationship(
        "ExcursionDetails",
        back_populates="excursion",
        uselist=False,  # Одна запись деталей на экскурсию
        cascade="all, delete-orphan",
    )


class ExcursionDetails(Base):
    __tablename__ = "excursion_details"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    excursion_id: Mapped[int] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Одна запись на экскурсию
    )

    # Блок 2: Описание маршрута (полное описание)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Блок 3: Что входит (список включений)
    inclusions: Mapped[list[str]] = mapped_column(
        JSON, nullable=True
    )  # ["Трансфер", "Гид", "Питание", ...]

    # Блок 4: Пошаговая программа тура
    itinerary: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )  # [{"time": "09:00", "title": "Сбор группы", "description": "Описание..."}, ...]

    # Дополнительные поля для расширения
    meeting_point: Mapped[str] = mapped_column(nullable=True)  # Место сбора
    requirements: Mapped[list[str]] = mapped_column(
        JSON, nullable=True
    )  # ["Удобная обувь", "Вода", ...]
    recommendations: Mapped[list[str]] = mapped_column(
        JSON, nullable=True
    )  # ["Взять фотоаппарат", "Одеваться по погоде", ...]

    # Связь с основной таблицей
    excursion: Mapped["Excursion"] = relationship("Excursion", back_populates="details")


# Создаем таблицы
Base.metadata.create_all(bind=engine)
