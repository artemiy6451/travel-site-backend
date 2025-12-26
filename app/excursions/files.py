import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from loguru import logger
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
    logger.debug("Compress image with file extension: {}", file_extension)

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

        logger.debug(
            "File compressed form {original_size} to {compressed_size}",
            original_size=original_size,
            compressed_size=compressed_size,
        )
        return compressed_data

    except Exception as e:
        logger.exception("Can not compress file: {}", e)
        return image_content


def should_compress_file(file_extension: str, file_size: int) -> bool:
    logger.debug("Check should compress file.")

    # Не сжимаем очень маленькие файлы
    if file_size < 50 * 1024:  # 50KB
        return False

    # Проверяем поддержку формата
    supported_formats = {".jpg", ".jpeg", ".png", ".webp"}
    return file_extension.lower() in supported_formats


def save_uploaded_file(file: UploadFile) -> str:
    logger.debug("Save uploaded file: {}", file)

    try:
        # Проверка расширения файла
        if file.filename is None:
            raise HTTPException(
                status_code=400, detail="Can not upload file. No filename"
            )
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            logger.warning("File format {} not allowed", file_extension)
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
            logger.warning("File size too large: {}", file_size)
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
        url = f"{settings.api_base_url}/{settings.upload_dir}/{unique_filename}"
        logger.debug("Return image url: {}", url)
        return url

    except Exception as e:
        logger.exception("Can not save file: {}", e)
        raise HTTPException(
            status_code=409, detail=f"Ошибка при сохранении файла: {str(e)}"
        ) from Exception


def delete_uploaded_file_by_url(file_url: str) -> bool:
    logger.debug("Delete image by url: {}", file_url)

    try:
        # Извлекаем имя файла из URL
        filename = extract_filename_from_url(file_url)
        if not filename:
            logger.warning("Filename does not exist!")
            return False

        # Полный путь к файлу
        file_path = settings.upload_dir / filename

        # Проверяем существует ли файл
        if not file_path.exists():
            logger.warning("File does not exist!")
            return False

        # Удаляем файл
        file_path.unlink()

        logger.debug("File deleted")

        return True

    except Exception as e:
        logger.exception("Can not delete file: {}", e)
        raise HTTPException(
            status_code=409, detail=f"Ошибка при удалении файла: {str(e)}"
        ) from Exception


def extract_filename_from_url(file_url: str) -> str | None:
    logger.debug("Extract filename form url: {}", file_url)

    try:
        # Убираем базовый URL и путь к директории
        base_url_with_path = f"{settings.api_base_url}/{settings.upload_dir}/"

        if file_url.startswith(base_url_with_path):
            return file_url.replace(base_url_with_path, "")

        # Альтернативный вариант: извлекаем последнюю часть URL
        filename = file_url.split("/")[-1]

        logger.debug("Return filename: {}", filename)

        return filename

    except Exception as e:
        logger.exception("Can not extract filename: {}", e)
        return None
