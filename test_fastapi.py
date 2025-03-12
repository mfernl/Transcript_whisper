from fastapi.testclient import TestClient
from app.main import app
import asyncio
from io import BytesIO
from fastapi import UploadFile
import pytest

client = TestClient(app)


def test_login():

    response = client.post("/login", params={"username": "articuno", "password": "12345"})
    
    # Verificar que el código de estado sea 200 
    assert response.status_code == 200
    
    # Verificar que la respuesta contiene el token
    token = response.json()
    assert isinstance(token, str)  # Verifica que el token sea un string

def test_login_wrong_username():
    
    response = client.post("/login", params={"username": "moltres", "password": "12345"})
    
    assert response.status_code == 404
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "No User found"}

def test_login_no_username():
    
    response = client.post("/login", params={"username": "", "password": "12345"})
    
    assert response.status_code == 404
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "No User found"}

def test_login_wrong_password():
    
    response = client.post("/login", params={"username": "articuno", "password": "125"})
 
    assert response.status_code == 401
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "Password error"}

def test_login_no_password():
    
    response = client.post("/login", params={"username": "articuno", "password": ""})
 
    assert response.status_code == 401
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "Password error"}

def test_subir_archivo_real():
    file_path = "/home/mfllamas/Escritorio/pruebaN1.wav"  # Ruta del archivo real
    
    # Abrir el archivo en modo binario
    with open(file_path, "rb") as file:
        files = {"uploaded_file": (file_path, file, "audio/x-wav")}
        
        # Hacer la petición PUT con el archivo real
        response = client.put("/upload", params={"access_token": "soyadmin"}, files=files)

    # Verificar que la respuesta es correcta
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["filename"] == "pruebaN1.wav"
    assert json_data["message"] == "Archivo subido exitosamente"


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def pruebaLoop():
    print("Hola desde el loop")


try:
    loop.run_until_complete(pruebaLoop())
except KeyboardInterrupt:
    pass
finally:
    loop.close()
# Test para simular 5 solicitudes de carga de archivos simultáneas
"""@pytest.mark.asyncio
async def test_multiple_uploads():
    file_path = "/home/mfllamas/Escritorio/pruebaN1.wav"  # Ruta del archivo WAV

    with open(file_path, "rb") as f:
        file_data = f.read()

    file_names = [f"file_{i}.wav" for i in range(1)]
    access_token = "soyadmin"  # Token que vas a pasar en la solicitud

    tasks = [upload_file(file_data, file_name, access_token) for file_name in file_names]
    responses = await asyncio.gather(*tasks)

    for response in responses:
        assert response.status_code == 200
        json_response = response.json()
        assert "filename" in json_response
        assert json_response["filename"] in file_names
        assert "status" in json_response
        assert json_response["status"] == "success"
        assert "params" in json_response
        assert "duracion" in json_response
        assert "transcripcion" in json_response
"""