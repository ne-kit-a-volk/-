import pytest
import hashlib
import os
from httpx import AsyncClient, ASGITransport
from server import app
from fastapi import FastAPI, Request, HTTPException
@pytest.mark.asyncio
async def test_upload_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        file_path = 'all_photos\sample-green-200x200.jpg'
        with open(file_path, 'rb') as f:
            content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        files = {'file': (os.path.basename(file_path), content)}
        headers = {
            'Client-ID': 'test_client',
            'X-Hash': file_hash
        }
        response = await ac.post("/upload", files=files, headers=headers)
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

@pytest.mark.asyncio
async def test_upload_invalid_hash():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        file_path = 'all_photos\sample-green-200x200.jpg'
        with open(file_path, 'rb') as f:
            content = f.read()
        file_hash = 'invalid_hash'
        files = {'file': (os.path.basename(file_path), content)}
        headers = {
            'Client-ID': 'test_client',
            'X-Hash': file_hash
        }
        response = await ac.post("/upload", files=files, headers=headers)
        assert response.status_code == 400
        assert response.json()['detail'] == "Hash mismatch"

@pytest.mark.asyncio
async def test_upload_invalid_image():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        content = b'not an image'
        file_hash = hashlib.sha256(content).hexdigest()
        files = {'file': ('invalid.txt', content)}
        headers = {
            'Client-ID': 'test_client',
            'X-Hash': file_hash
        }
        response = await ac.post("/upload", files=files, headers=headers)
        assert response.status_code == 400
        assert response.json()['detail'] == "Invalid image file"

@pytest.mark.asyncio
async def test_complete_transfer():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        headers = {'Client-ID': 'test_client'}
        response = await ac.post("/complete", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"status": "transfer completed"}

@pytest.mark.asyncio
async def test_get_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        headers = {'Client-ID': 'test_client'}
        response = await ac.get("/status", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"client_id": "test_client", "status": "completed"}

