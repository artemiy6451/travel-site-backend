import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.config import settings

# Настройки для загрузки файлов
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Настройки сжатия
COMPRESSION_SETTINGS: dict[str, dict[str, int | bool]] = {
    "jpg": {"quality": 85, "optimize": True},
    "jpeg": {"quality": 85, "optimize": True},
    "png": {"optimize": True},
    "webp": {"quality": 85, "optimize": True},
}

# Максимальные размеры для сжатия
MAX_WIDTH = 1920
MAX_HEIGHT = 1080


def compress_image(image_content: bytes, file_extension: str) -> bytes:
    try:
        # Открываем изображение из bytes
        image = Image.open(BytesIO(image_content))

        # Конвертируем в RGB если нужно (для JPEG)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")  # type: ignore

        # Получаем оригинальные размеры
        original_width, original_height = image.size

        # Вычисляем новые размеры с сохранением пропорций
        if original_width > MAX_WIDTH or original_height > MAX_HEIGHT:
            image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

        # Сохраняем в буфер с настройками сжатия
        output_buffer = BytesIO()
        format_name = file_extension.lower().lstrip(".")
        if format_name == "jpg":
            format_name = "jpeg"

        # Применяем настройки сжатия для формата
        compression_args = COMPRESSION_SETTINGS.get(
            format_name, {"quality": 85, "optimize": True}
        )

        if format_name in ["jpeg", "jpg"]:
            image.save(output_buffer, format=format_name.upper(), **compression_args)
        elif format_name == "png":
            # Для PNG используем оптимизацию
            image.save(output_buffer, format="PNG", **compression_args)
        elif format_name == "webp":
            image.save(output_buffer, format="WEBP", **compression_args)
        else:
            # Для неизвестных форматов сохраняем как есть
            return image_content

        # Возвращаем сжатые данные
        compressed_data = output_buffer.getvalue()

        # Логируем степень сжатия
        original_size = len(image_content)
        compressed_size = len(compressed_data)

        # Если сжатие увеличило размер (маловероятно), возвращаем оригинал
        if compressed_size > original_size:
            return image_content

        return compressed_data

    except Exception:
        return image_content


def should_compress_file(file_extension: str, file_size: int) -> bool:
    # Не сжимаем очень маленькие файлы
    if file_size < 50 * 1024:  # 50KB
        return False

    # Проверяем поддержку формата
    supported_formats = {".jpg", ".jpeg", ".png", ".webp"}
    return file_extension.lower() in supported_formats


def save_uploaded_file(file: UploadFile) -> str:
    try:
        # Проверка расширения файла
        if file.filename is None:
            raise HTTPException(
                status_code=400, detail="Can not upload file. No filename"
            )
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"""
                Неподдерживаемый формат файла. Разрешены: {", ".join(ALLOWED_EXTENSIONS)}
                """,
            )

        # Проверка размера файла
        file.file.seek(0, 2)  # Перемещаемся в конец файла
        file_size = file.file.tell()
        file.file.seek(0)  # Возвращаемся в начало

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"""
                Файл слишком большой.
                Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024}MB
                """,
            )

        # Читаем содержимое файла для проверки хеша и возможного сжатия
        file_content = file.file.read()

        # Сжимаем изображение если нужно
        if should_compress_file(file_extension, file_size):
            compressed_content = compress_image(file_content, file_extension)

            # Используем сжатое содержимое для дальнейшей обработки
            processed_content = compressed_content
        else:
            processed_content = file_content

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{uuid.uuid4().hex}{file_extension}"
        file_path = settings.upload_dir / unique_filename

        # Сохраняем обработанный файл
        with open(file_path, "wb") as buffer:
            buffer.write(processed_content)

        # Возвращаем абсолютный URL для доступа к файлу
        return f"{settings.api_base_url}/{settings.upload_dir}/{unique_filename}"

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=409, detail=f"Ошибка при сохранении файла: {str(e)}"
        ) from Exception


def delete_uploaded_file_by_url(file_url: str) -> bool:
    try:
        # Извлекаем имя файла из URL
        filename = extract_filename_from_url(file_url)
        if not filename:
            return False

        # Полный путь к файлу
        file_path = settings.upload_dir / filename

        # Проверяем существует ли файл
        if not file_path.exists():
            return False

        # Удаляем файл
        file_path.unlink()

        return True

    except Exception as e:
        raise HTTPException(
            status_code=409, detail=f"Ошибка при удалении файла: {str(e)}"
        ) from Exception


def extract_filename_from_url(file_url: str) -> str | None:
    try:
        # Убираем базовый URL и путь к директории
        base_url_with_path = f"{settings.api_base_url}/{settings.upload_dir}/"

        if file_url.startswith(base_url_with_path):
            return file_url.replace(base_url_with_path, "")

        # Альтернативный вариант: извлекаем последнюю часть URL
        return file_url.split("/")[-1]

    except Exception:
        return None
