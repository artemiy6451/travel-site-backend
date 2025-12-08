import logging

import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import ValueInputOption

from app.booking.schemas import BookingSchema
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.sheets.schemas import BookingRow, SheetConfig

logger = logging.getLogger(__name__)


class SheetsService:
    """Сервис для работы с Google Sheets"""

    def __init__(self) -> None:
        self.client: gspread.Client | None = None
        self.spreadsheet: gspread.Spreadsheet | None = None
        self._connect()
        self.excursion_sheets: dict[str, str] = {}

    def _connect(self) -> None:
        """Устанавливает соединение с Google Sheets API"""
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            credentials = Credentials.from_service_account_info(
                settings.credentials_dict, scopes=scopes
            )

            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(settings.spreadsheet_id)

            logger.info(f"✅ Подключено к Google таблице: {self.spreadsheet.title}")

            # Загружаем существующие листы в кэш
            self._load_existing_sheets()

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Google Sheets: {e}")
            raise

    def _load_existing_sheets(self) -> None:
        """Загружает информацию о существующих листах в кэш"""
        try:
            worksheets = self.spreadsheet.worksheets()  # type: ignore
            for ws in worksheets:
                # Можно добавить логику для парсинга информации из листов
                logger.debug(f"Найден лист: {ws.title}")
        except Exception as e:
            logger.warning(f"Ошибка загрузки листов: {e}")

    def get_or_create_excursion_sheet(
        self, excursion: ExcursionScheme
    ) -> gspread.Worksheet:
        """
        Получает или создает лист для конкретной экскурсии

        Args:
            excursion: Данные экскурсии

        Returns:
            Worksheet: Лист для экскурсии
        """
        # Генерируем уникальное имя листа
        sheet_name = SheetConfig.generate_sheet_name(excursion.title, excursion.date)

        # Проверяем кэш
        cache_key = f"{excursion.id}_{excursion.date.strftime('%Y%m%d')}"

        if cache_key in self.excursion_sheets:
            sheet_name = self.excursion_sheets[cache_key]

        try:
            # Пытаемся получить существующий лист
            worksheet = self.spreadsheet.worksheet(sheet_name)  # type: ignore
            logger.info(f"Лист '{sheet_name}' найден")

        except gspread.exceptions.WorksheetNotFound:
            # Создаем новый лист для экскурсии
            worksheet = self.spreadsheet.add_worksheet(  # type: ignore
                title=sheet_name, rows=1000, cols=15
            )

            # Подготавливаем новый лист
            self._prepare_excursion_sheet(worksheet, excursion)

            # Добавляем в кэш
            self.excursion_sheets[cache_key] = sheet_name

            logger.info(f"✅ Создан новый лист для экскурсии: '{sheet_name}'")

        return worksheet

    def _prepare_excursion_sheet(
        self, worksheet: gspread.Worksheet, excursion: ExcursionScheme
    ) -> None:
        """
        Подготавливает новый лист для экскурсии
        """
        try:
            # 1. Очищаем лист
            worksheet.clear()

            # 2. Добавляем информационный заголовок об экскурсии
            info_header = SheetConfig.generate_sheet_info_header(
                excursion.title, excursion.date, excursion.price
            )

            for i, info_line in enumerate(info_header, start=1):
                worksheet.update_cell(i, 1, info_line)

            # 3. Форматируем информационный заголовок
            try:
                from gspread_formatting import CellFormat, TextFormat, format_cell_range

                # Жирный шрифт для заголовка
                header_format = CellFormat(textFormat=TextFormat(bold=True, fontSize=12))
                format_cell_range(worksheet, f"A1:A{len(info_header)}", header_format)
            except ImportError:
                logger.warning(
                    "gspread-formatting не установлен, пропускаем форматирование"
                )

            # 4. Добавляем заголовки таблицы бронирований
            # Пустая строка после информационного заголовка
            data_start_row = len(info_header) + 2

            # Заголовки таблицы
            headers = SheetConfig().base_headers
            worksheet.update(f"A{data_start_row}", [headers])  # type: ignore

            # 5. Форматируем заголовки таблицы
            try:
                from gspread_formatting import CellFormat, TextFormat, format_cell_range

                # Заголовки таблицы - жирные с фоном
                table_header_format = CellFormat(
                    textFormat=TextFormat(bold=True),
                    backgroundColor={"red": 0.9, "green": 0.9, "blue": 0.9},
                )
                format_cell_range(
                    worksheet,
                    f"A{data_start_row}:{chr(64 + len(headers))}{data_start_row}",
                    table_header_format,
                )
            except ImportError:
                pass

            # 6. Замораживаем заголовки таблицы
            worksheet.freeze(rows=data_start_row)

            # 7. Автоматически подгоняем ширину столбцов
            worksheet.columns_auto_resize(0, len(headers) - 1)

            logger.info(f"Лист '{worksheet.title}' подготовлен для экскурсии")

        except Exception as e:
            logger.error(f"Ошибка подготовки листа: {e}")
            raise

    def add_booking(self, booking: BookingSchema, excursion: ExcursionScheme) -> bool:
        """Добавляет бронирование в лист соответствующей экскурсии"""
        try:
            # Получаем или создаем лист для экскурсии
            worksheet = self.get_or_create_excursion_sheet(excursion)

            # Находим строку для добавления данных
            data_start_row = self._get_data_start_row(worksheet)

            # Создаем строку данных
            booking_row = BookingRow(
                id=booking.id,
                last_name=booking.last_name,
                first_name=booking.first_name,
                phone_number=booking.phone_number,
                total_people=booking.total_people,
                price_per_person=excursion.price,
                total_price=excursion.price * booking.total_people,
                status="✅ Активна" if booking.is_active else "⏳ В обработке",
            )

            # Добавляем строку в таблицу
            row_values = booking_row.to_row()
            worksheet.append_row(
                row_values,
                value_input_option=ValueInputOption.user_entered,
                table_range=f"A{data_start_row}",
            )

            # Форматируем новую строку
            self._format_booking_row(
                worksheet, data_start_row + len(worksheet.get_all_values()) - 1
            )

            # Обновляем итоги (опционально)
            self._update_totals(worksheet, excursion)  # type: ignore

            logger.info(
                f"✅ Бронирование #{booking.id} добавлено в лист '{worksheet.title}'"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка добавления в Google Sheets: {e}")
            return False

    def _get_data_start_row(self, worksheet: gspread.Worksheet) -> int:
        """
        Определяет строку, с которой начинаются данные бронирований
        """
        all_values = worksheet.get_all_values()

        # Ищем заголовки таблицы
        headers = SheetConfig().base_headers
        for i, row in enumerate(all_values, start=1):
            if row and row[0] == headers[0]:
                return i + 1  # Данные начинаются со следующей строки

        # Если заголовки не найдены, предполагаем, что это новый лист
        # Информационный заголовок обычно занимает 5-6 строк
        return 7

    def _format_booking_row(self, worksheet: gspread.Worksheet, row_num: int) -> None:
        """Форматирует строку с бронированием"""
        try:
            from gspread_formatting import Border, Borders, CellFormat, format_cell_range

            # Добавляем границы для ячеек
            border_format = CellFormat(
                borders=Borders(
                    top=Border("SOLID"),
                    bottom=Border("SOLID"),
                    left=Border("SOLID"),
                    right=Border("SOLID"),
                )
            )

            headers = SheetConfig().base_headers
            format_cell_range(
                worksheet, f"A{row_num}:{chr(64 + len(headers))}{row_num}", border_format
            )

        except ImportError:
            pass

    def _update_totals(self, worksheet: gspread.Worksheet) -> None:
        """
        Обновляет итоговую информацию в листе
        (количество бронирований, общее количество людей, общая сумма)
        """
        try:
            data_start_row = self._get_data_start_row(worksheet)
            all_values = worksheet.get_all_values()

            if len(all_values) < data_start_row:
                return

            # Получаем данные бронирований
            bookings_data = all_values[data_start_row - 1 :]

            if not bookings_data:
                return

            # Вычисляем итоги
            total_bookings = len(bookings_data)
            total_people = sum(int(row[5]) for row in bookings_data if row[5].isdigit())
            total_amount = sum(
                float(row[7]) for row in bookings_data if self._is_number(row[7])
            )

            # Находим строку для итогов (после информационного заголовка)
            info_row = 1

            # Обновляем или добавляем строку с итогами
            totals_row = (
                f"Итого: {total_bookings} бронирований,"
                f"{total_people} человек, {total_amount} руб."
            )
            worksheet.update_cell(info_row + 4, 1, totals_row)

        except Exception as e:
            logger.warning(f"Не удалось обновить итоги: {e}")

    def _is_number(self, value: str) -> bool:
        """Проверяет, является ли строка числом"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def update_booking_status(
        self, booking: BookingSchema, excursion: ExcursionScheme
    ) -> bool:
        """Обновляет статус брони в таблице"""
        try:
            worksheet = self.get_or_create_excursion_sheet(excursion)
            data_start_row = self._get_data_start_row(worksheet)

            # Ищем строку с нужным ID (первый столбец)
            cell = worksheet.find(str(booking.id))

            if cell and cell.row >= data_start_row:
                # Обновляем статус (8-й столбец в базовых заголовках)
                new_status = "✅ Активна" if booking.is_active else "⏳ В обработке"
                worksheet.update_cell(cell.row, 8, new_status)

                logger.info(f"✅ Статус брони #{booking.id} обновлен в Google Sheets")
                return True
            else:
                logger.warning(f"Бронирование #{booking.id} не найдено в таблице")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка обновления статуса: {e}")
            return False

    def create_summary_sheet(self) -> None:  # noqa
        """
        Создает сводный лист со всеми экскурсиями
        """
        try:
            summary_sheet_name = "📊 Сводка по всем экскурсиям"

            try:
                worksheet = self.spreadsheet.worksheet(summary_sheet_name)  # type: ignore
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(  # type: ignore
                    title=summary_sheet_name, rows=1000, cols=10
                )

            # Заголовки сводного листа
            headers = [
                "Экскурсия",
                "Дата",
                "Цена",
                "Бронирований",
                "Всего человек",
                "Общая сумма",
                "Свободных мест",
                "Заполненность",
            ]

            worksheet.update("A1", [headers])  # type: ignore

            # Получаем все листы (кроме сводного)
            all_sheets = self.spreadsheet.worksheets()  # type: ignore
            summary_data = []

            for sheet in all_sheets:
                if sheet.title != summary_sheet_name:
                    # Парсим информацию из названия листа
                    try:
                        if "(" in sheet.title and ")" in sheet.title:
                            title_part = sheet.title.split("(")[0].strip()
                            date_part = (
                                sheet.title.split("(")[1].replace(")", "").strip()
                            )

                            # Получаем данные из листа
                            all_values = sheet.get_all_values()
                            bookings_count = (
                                len(all_values) - self._get_data_start_row(sheet) + 1
                            )

                            if bookings_count > 0:
                                # Вычисляем статистику
                                total_people = 0
                                total_amount = 0

                                for row in all_values[
                                    self._get_data_start_row(sheet) - 1 :
                                ]:
                                    if len(row) > 7:  # noqa
                                        try:
                                            total_people += (
                                                int(row[5]) if row[5].isdigit() else 0
                                            )
                                            total_amount += (  # type: ignore
                                                float(row[7])
                                                if self._is_number(row[7])
                                                else 0
                                            )
                                        except (ValueError, IndexError):
                                            pass

                                # Получаем цену из информационного заголовка
                                price = 0
                                for row in all_values[:5]:
                                    if "Цена:" in str(row):
                                        try:
                                            price = float(  # type: ignore
                                                str(row)
                                                .split(":")[1]
                                                .split("руб")[0]
                                                .strip()
                                            )
                                        except Exception:
                                            pass

                                summary_data.append(
                                    [
                                        title_part,
                                        date_part,
                                        price,
                                        bookings_count,
                                        total_people,
                                        total_amount,
                                        "N/A",  # Свободные места (нужна вместимость)
                                        (
                                            f"{(bookings_count / 20 * 100):.1f}%"
                                            if bookings_count > 0
                                            else "0%"
                                        ),
                                    ]
                                )
                    except Exception as e:
                        logger.warning(f"Ошибка обработки листа {sheet.title}: {e}")

            if summary_data:
                worksheet.update("A2", summary_data)  # type: ignore

            logger.info("✅ Сводный лист создан/обновлен")

        except Exception as e:
            logger.error(f"❌ Ошибка создания сводного листа: {e}")

    def close(self) -> None:
        """Закрывает соединение"""
        logger.info("Соединение с Google Sheets закрыто")


sheets_service = SheetsService()
