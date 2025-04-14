from locust import HttpUser, TaskSet, task, between
import hashlib
import os
import random
import string

# Путь к изображению для отправки
IMAGE_PATH = 'all_photos\sample-birch-400x300.jpg'

def generate_client_id():
    return 'client_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

class UserBehavior(TaskSet):
    @task
    def upload_file(self):
        client_id = generate_client_id()
        with open(IMAGE_PATH, 'rb') as f:
            content = f.read()

        file_hash = hashlib.sha256(content).hexdigest()

        files = {'file': (os.path.basename(IMAGE_PATH), content)}
        headers = {
            'Client-ID': client_id,
            'X-Hash': file_hash
        }

        self.client.post("/upload", files=files, headers=headers)

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 1)
