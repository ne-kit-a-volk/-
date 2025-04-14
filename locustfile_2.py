from locust import HttpUser, TaskSet, task, between
import hashlib
import os
import glob

# Путь к директории с изображениями для отправки
IMAGE_DIR = 'all_photos'

class UploadImagesTaskSet(TaskSet):
    def on_start(self):
        # Получаем список всех файлов изображений в директории
        self.image_files = glob.glob(os.path.join(IMAGE_DIR, '*'))
        # Индекс текущего файла
        self.current_index = 0

    @task
    def upload_images(self):
        if self.current_index < len(self.image_files):
            image_path = self.image_files[self.current_index]
            self.current_index += 1

            client_id = 'test_client'
            with open(image_path, 'rb') as f:
                content = f.read()

            file_hash = hashlib.sha256(content).hexdigest()

            files = {
                'file': (os.path.basename(image_path), content, 'image/jpeg')
            }
            headers = {
                'Client-ID': client_id,
                'X-Hash': file_hash
            }

            response = self.client.post("/upload", files=files, headers=headers)
            if response.status_code == 200:
                print(f"Файл {os.path.basename(image_path)} успешно отправлен на сервер.")
            else:
                print(f"Ошибка при отправке файла {os.path.basename(image_path)}: {response.status_code} - {response.text}")
        else:
            # Все изображения отправлены, останавливаем задачи пользователя
            self.interrupt()

class UploadImagesUser(HttpUser):
    tasks = [UploadImagesTaskSet]
    wait_time = between(1, 1)

    def on_stop(self):
        # Завершаем тестирование после завершения задач
        if self.environment.runner:
            self.environment.runner.quit()
