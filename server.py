from fastapi import FastAPI, UploadFile, File, Header, HTTPException
import uvicorn
import hashlib
import aiofiles
import os
import time
from PIL import Image
import io
import argparse

app = FastAPI()

# Глобальные переменные для хранения пути сохранения и статуса клиентов
SAVE_PATH = ""
client_status = {}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    client_id: str = Header(...),
    x_hash: str = Header(...)
):
    start_time = time.time()

    # Проверяем наличие необходимых заголовков
    if not client_id:
        raise HTTPException(status_code=400, detail="Missing Client-ID header")
    if not x_hash:
        raise HTTPException(status_code=400, detail="Missing X-Hash header")

    try:
        # Читаем содержимое файла
        content = await file.read()

        # Вычисляем хеш-сумму
        computed_hash = hashlib.sha256(content).hexdigest()

        # Сравниваем с переданной хеш-суммой
        if computed_hash != x_hash:
            raise HTTPException(status_code=400, detail="Hash mismatch")

        # Проверяем валидность изображения
        if not validate_image(content):
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Создаем директорию для клиента, если не существует
        client_dir = os.path.join(SAVE_PATH, client_id)
        os.makedirs(client_dir, exist_ok=True)

        # Путь для сохранения файла
        file_path = os.path.join(client_dir, file.filename)

        # Проверяем, существует ли файл с таким именем
        file_overwritten = False
        if os.path.exists(file_path):
            # Предупреждаем пользователя, что файл будет перезаписан
            # print(f"Предупреждение: файл '{file.filename}' уже существует и будет перезаписан.")
            file_overwritten = True

        # Асинхронно сохраняем файл
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(content)

        # Обновляем статус клиента
        client_status[client_id] = "in_progress"

        # Замеряем время обработки
        elapsed_time = (time.time() - start_time) * 1000  # в миллисекундах
        print(elapsed_time)
        if elapsed_time > 50:
            print(f"Предупреждение: время сохранения файла превысило 50 мс и составило {elapsed_time:.2f} мс.")

        # Возвращаем ответ с информацией о перезаписи файла
        return {"status": "success", "file_overwritten": file_overwritten}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/complete")
async def complete_transfer(client_id: str = Header(...)):
    if not client_id:
        raise HTTPException(status_code=400, detail="Missing Client-ID header")

    client_status[client_id] = "completed"
    print(f"Клиент {client_id} завершил передачу данных.")
    return {"status": "transfer completed"}

@app.get("/status")
async def get_status(client_id: str = Header(...)):
    if not client_id:
        raise HTTPException(status_code=400, detail="Missing Client-ID header")

    status = client_status.get(client_id, "unknown")
    return {"client_id": client_id, "status": status}

def validate_image(data: bytes) -> bool:
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
        return True
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="Сервер приема фотографий от дронов")
    parser.add_argument('--port', type=int, default=8000, help='Порт для прослушивания')
    parser.add_argument('--save-path', type=str, required=True, help='Путь для сохранения фотографий')
    args = parser.parse_args()

    global SAVE_PATH
    SAVE_PATH = args.save_path

    # Проверяем существование директории сохранения
    if not os.path.exists(SAVE_PATH):
        print(f"Ошибка: директория '{SAVE_PATH}' не существует.")
        return
    else:
        print(f"Сервер запущен и будет сохранять файлы в директорию: '{SAVE_PATH}'")

    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
