from datetime import datetime

from pydantic import BaseModel


class BookingRow(BaseModel):
    """Модель строки для записи в Google Sheets"""

    id: int
    last_name: str
    first_name: str
    phone_number: str
    total_people: int
    price_per_person: float
    total_price: float
    status: str

    def to_row(self) -> list[str]:
        """Конвертирует в список значений для строки таблицы"""
        return [
            str(self.id),
            self.last_name,
            self.first_name,
            self.phone_number.replace("+", ""),
            str(self.total_people),
            str(self.price_per_person),
            str(self.total_price),
            self.status,
        ]


class SheetConfig(BaseModel):
    """Конфигурация листа для экскурсии"""

    # Базовые заголовки (без информации об экскурсии)
    base_headers: list[str] = [
        "ID",
        "Фамилия",
        "Имя",
        "Телефон",
        "Кол-во человек",
        "Цена за человека",
        "Общая сумма",
        "Статус",
    ]

    @staticmethod
    def generate_sheet_name(excursion_title: str, excursion_date: datetime) -> str:
        """
        Генерирует имя листа на основе названия и даты экскурсии
        Формат: "Название (DD.MM.YYYY)"
        """
        date_str = excursion_date.strftime("%d.%m.%Y")
        return f"{excursion_title} ({date_str})"

    @staticmethod
    def generate_sheet_info_header(
        excursion_title: str, excursion_date: datetime, price: float
    ) -> list[str]:
        """
        Генерирует информационную строку об экскурсии
        """
        date_str = excursion_date.strftime("%d.%m.%Y")
        return [
            f"Экскурсия: {excursion_title}",
            f"Дата: {date_str}",
            f"Цена: {price} руб. за человека",
            "",
            "Список бронирований:",
        ]
