import hashlib
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from config import settings
from fastapi import HTTPException, UploadFile

# Настройки для загрузки файлов
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Добавляем кеш для хранения хешей уже загруженных файлов
_uploaded_files_cache = set()


def calculate_file_hash(file_content: bytes) -> str:
    """Вычисляет MD5 хеш содержимого файла"""
    return hashlib.md5(file_content).hexdigest()


def save_uploaded_file(file: UploadFile) -> str:
    """
    Сохраняет загруженный файл на сервере и возвращает абсолютный URL для доступа к нему
    """
    try:
        # Проверка расширения файла
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Проверка размера файла
        file.file.seek(0, 2)  # Перемещаемся в конец файла
        file_size = file.file.tell()
        file.file.seek(0)  # Возвращаемся в начало

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024}MB",
            )

        # Читаем содержимое файла для проверки хеша
        file_content = file.file.read()
        file_hash = calculate_file_hash(file_content)

        # Проверяем, не загружался ли уже такой файл
        if file_hash in _uploaded_files_cache:
            # Ищем существующий файл с таким хешем
            existing_file = find_existing_file_by_hash(file_hash)
            if existing_file:
                return f"{settings.api_base_url}/static/uploads/{existing_file}"

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{uuid.uuid4().hex}{file_extension}"
        file_path = settings.upload_dir / unique_filename

        # Сохраняем файл (перемещаем указатель обратно)
        file.file.seek(0)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Добавляем хеш в кеш
        _uploaded_files_cache.add(file_hash)

        # Сохраняем связь хеш-имя файла в файловой системе (опционально)
        save_file_hash_mapping(file_hash, unique_filename)

        # Возвращаем абсолютный URL для доступа к файлу
        return f"{BASE_URL}/static/uploads/{unique_filename}"

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при сохранении файла: {str(e)}"
        ) from Exception


def find_existing_file_by_hash(file_hash: str) -> str | None:
    """
    Ищет существующий файл по хешу в директории загрузок
    """
    try:
        # Проверяем файл с маппингом хешей
        hash_mapping_file = UPLOAD_DIR / "file_hashes.json"
        if hash_mapping_file.exists():

            with open(hash_mapping_file, "r", encoding="utf-8") as f:
                hash_mapping = json.load(f)
                return hash_mapping.get(file_hash)

        # Альтернативный способ: сканируем все файлы и проверяем хеш
        # (менее эффективно, но работает если файл маппинга удален)
        for file_path in UPLOAD_DIR.glob("*.*"):
            if file_path.name in ["file_hashes.json", ".gitkeep"]:
                continue
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                    if calculate_file_hash(content) == file_hash:
                        return file_path.name
            except Exception:
                continue

        return None
    except Exception:
        return None


def save_file_hash_mapping(file_hash: str, filename: str):
    """
    Сохраняет связь между хешем файла и именем файла
    """
    try:
        hash_mapping_file = UPLOAD_DIR / "file_hashes.json"
        hash_mapping = {}

        if hash_mapping_file.exists():
            with open(hash_mapping_file, "r", encoding="utf-8") as f:
                hash_mapping = json.load(f)

        hash_mapping[file_hash] = filename

        with open(hash_mapping_file, "w", encoding="utf-8") as f:
            json.dump(hash_mapping, f, ensure_ascii=False, indent=2)

    except Exception:
        # Если не удалось сохранить маппинг, продолжаем без него
        pass


def load_existing_file_hashes():
    """
    Загружает хеши уже существующих файлов при старте приложения
    """
    try:
        # Сканируем существующие файлы и вычисляем их хеши
        for file_path in UPLOAD_DIR.glob("*.*"):
            if file_path.name in ["file_hashes.json", ".gitkeep"]:
                continue
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                    file_hash = calculate_file_hash(content)
                    _uploaded_files_cache.add(file_hash)
            except Exception:
                continue

        # Также загружаем хеши из файла маппинга
        hash_mapping_file = UPLOAD_DIR / "file_hashes.json"
        if hash_mapping_file.exists():
            with open(hash_mapping_file, "r", encoding="utf-8") as f:
                hash_mapping = json.load(f)
                for file_hash in hash_mapping.keys():
                    _uploaded_files_cache.add(file_hash)

    except Exception:
        # Если не удалось загрузить, начинаем с пустого кеша
        pass


# Загружаем хеши существующих файлов при импорте модуля
load_existing_file_hashes()
