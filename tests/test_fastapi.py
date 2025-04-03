from fastapi.testclient import TestClient
from app.main import app
import asyncio
from io import BytesIO
from fastapi import UploadFile
import pytest
from httpx import ASGITransport, AsyncClient
import torch
import pytest_asyncio
from app.main import create_token, create_idRT, sesiones, transcription_queue
from datetime import datetime, timedelta, timezone
from app.main import SECRET_KEY
from jose import jwt, JWTError
from unittest.mock import patch
import logging
import statistics

client = TestClient(app)

logger = logging.getLogger(__name__)
logging.basicConfig(filename='pruebas.log', encoding='utf-8', level=logging.DEBUG)

def test_get_openapi():
    response = client.get("/openapi.json")

    assert response.status_code == 200

def test_token_revocado():
    login = client.post("/login", params={"username": "articuno", "password": "12345"})
    token_rev = login.json()

    logout = client.post("/logout", params={"access_token": token_rev})

    assert logout.json() == {"message": "logout completado"}

    login2 = client.post("/login", params={"username": "articuno", "password": "12345"})

    appstatus = client.get("/appstatus", params={"access_token": token_rev})

    assert appstatus.status_code == 401
    assert appstatus.json() == {"detail": "El token ha sido revocado"}

def test_wrong_user():
    badusertoken = create_token({"username": "gyarados"})

    appstatus = client.get("/appstatus", params={"access_token": badusertoken})

    assert appstatus.status_code == 401
    assert appstatus.json() == {"detail": "El usuario no es valido"}

def test_expired_token():
    data_token = {"username": "deoxys"}
    expiracion = datetime.now(timezone.utc) + timedelta(seconds=-2) #sumarle a la hora actual el timedelta deseado
    data_token["exp"] = expiracion.isoformat()
    print(data_token["exp"])
    token_jwt = jwt.encode(data_token, key=SECRET_KEY, algorithm="HS256")

    appstatus = client.get("/appstatus", params={"access_token": token_jwt})

    assert appstatus.status_code == 401
    assert appstatus.json() == {"detail": "El token ha expirado"}

def mock_create_idRT(data):
    # Forzar un valor estático para id_RT
    return "0#deoxys"  

def test_duplicated_session():

    # Login para obtener el token de acceso
    response = client.post("/login", params={"username": "deoxys", "password": "54321"})
    assert response.status_code == 200  
    access_token = response.json()
    
    #Mock fuerza que el idRT se comporte siempre igual
    with patch('app.main.create_idRT', side_effect=mock_create_idRT):

        response1 = client.get("/crearRTsession", params={"access_token": access_token})
        assert response1.status_code == 200
        assert "session_id" in response1.json()

        response2 = client.get("/crearRTsession", params={"access_token": access_token})
        
        assert response2.status_code == 400
        assert response2.json() == {"detail": "Sesión duplicada"}

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

def test_close_session():
    log = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert log.status_code == 200
    print(f"Este es el token del login: {log.json()}")
    access_token = log.json()
    response = client.get("/crearRTsession", params={"access_token": access_token})
    print(f"Esta es la respuesta de crear sesion: {response}")
    assert response.status_code == 200
    session = response.json()["session_id"]
    print(f"Esta es la sesión: {session}")
    close = client.get("/cerrarRTsession", params={"access_token": access_token, "RTsession_id": session})
    assert close.status_code == 200
    close_data = close.json()
    assert close_data["session_id"] == session
    assert close_data["full_transcription"] == ""

def test_close_session_wrongtoken():
    log = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert log.status_code == 200
    print(f"Este es el token del login: {log.json()}")
    access_token = log.json()
    response = client.get("/crearRTsession", params={"access_token": access_token})
    print(f"Esta es la respuesta de crear sesion: {response}")
    assert response.status_code == 200
    session = response.json()["session_id"]
    print(f"Esta es la sesión: {session}")
    close = client.get("/cerrarRTsession", params={"access_token": "soyadmin", "RTsession_id": session})
    assert close.status_code == 401
    assert close.json() == {"detail": "No autorizado para operar en este canal"}

def test_close_session_sessionNotFound():
    log = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert log.status_code == 200
    print(f"Este es el token del login: {log.json()}")
    access_token = log.json()
    response = client.get("/crearRTsession", params={"access_token": access_token})
    print(f"Esta es la respuesta de crear sesion: {response}")
    assert response.status_code == 200

    close = client.get("/cerrarRTsession", params={"access_token": access_token, "RTsession_id": "soyerror"})
    assert close.status_code == 404
    assert close.json() == {"detail": "No se ha encontrado la sesión"}

def test_transmision():
    token = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert token.status_code == 200
    sesion = client.get("/crearRTsession", params={"access_token": token.json()})
    rtId = sesion.json()["session_id"]
    assert sesion.status_code == 200

    file_path = "/home/mfllamas/Escritorio/pruebaN1.wav"  # Ruta del archivo real
    
    # Abrir el archivo en modo binario
    with open(file_path, "rb") as file:
        files = {"uploaded_file": (file_path, file, "audio/x-wav")}
        
        # Hacer la petición PUT con el archivo real
        response = client.put("/transmission", params={"access_token": token.json(), "RTsession_id": rtId}, files=files)

    assert response.status_code == 200
    json_data = response.json()
    print(f"esta es la json_data {json_data}")
    assert json_data["transcripcion"][0]["start"] == "0.00"

def test_transmision_w_session_closed():
    #Crear una sesión con caducidad inmediata para probar el caso que se haya cerrado por inactividad
    token = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert token.status_code == 200

    user_data = jwt.decode(token.json(), key=SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
    id_RT = create_idRT({"user": user_data["username"]})
    expiracion = datetime.now(timezone.utc) + timedelta(seconds=-2) #timedelta negativo para asegurar la caducidad inmediata
    exp_iso = expiracion.isoformat()
    if id_RT not in sesiones:
        sesiones[id_RT] = {
            "user_token": token.json(),
            "cierre_inactividad": exp_iso,
            "transcription": []
        }
    
    file_path = "/home/mfllamas/Escritorio/pruebaN1.wav"  # Ruta del archivo real

    # Abrir el archivo en modo binario
    with open(file_path, "rb") as file:
        files = {"uploaded_file": (file_path, file, "audio/x-wav")}
        
        # Hacer la petición PUT con el archivo real
        response = client.put("/transmission", params={"access_token": token.json(), "RTsession_id": id_RT}, files=files)

    assert response.status_code == 200
    json_data = response.json()
    print(f"esta es la json_data {json_data}")
    assert json_data["Detail"] == "Sesión cerrada por inactividad"
    assert json_data["Session_contents"]["full_transcription"] == ""
    assert json_data["Session_contents"]["session_id"]== id_RT


#@pytest.mark.skip(reason="ahorrar tiempo")
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
    print(json_data)
    print(json_data["filename"])
    print(json_data["status"])
    assert json_data["filename"] == "/home/mfllamas/Escritorio/pruebaN1.wav"
    assert json_data["status"] == "success"

@pytest.mark.asyncio
#@pytest.mark.skip(reason="ahorrar tiempo")
async def test_subir_archivo_async():
    usuarios = 100
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as ac:
        file_path = "/home/mfllamas/Escritorio/pruebaN1.wav"  # Ruta del archivo real

        async def subir_archivo():
        # Abrir el archivo en modo binario
            with open(file_path, "rb") as file:
                files = {"uploaded_file": (file_path, file, "audio/x-wav")}
                return await ac.put("/upload", params={"access_token": "soyadmin"}, files=files)
        
        gpu_usages = []

        async def medir_gpu():
            #Medir el uso de la memoria 
            while not test_done:
                uso_gpu = torch.cuda.memory_allocated(0) / 1e9  # Convertir a GB
                gpu_usages.append(uso_gpu)
                await asyncio.sleep(0.5) 

        startTime = datetime.now()
        test_done = False
        task_monitor = asyncio.create_task(medir_gpu())
        response = await asyncio.gather(*[subir_archivo() for _ in range(usuarios)])
        test_done = True
        await task_monitor 
        #response = await subir_archivo()#un audio solo
        print("Estoy testando upload")
        json_data = response[49].json()
        endtime = datetime.now()
        tiempo = endtime - startTime
        out = (str(timedelta(seconds=int(tiempo.total_seconds()))))

        avg_gpu_usage = statistics.mean(gpu_usages) if gpu_usages else 0
        peak_gpu_usage = max(gpu_usages) if gpu_usages else 0

        print(f"Tiempo transcribiendo con {usuarios} usuarios: {out}")
        print(f"Uso medio de GPU: {avg_gpu_usage:.2f} GB")
        print(f"Pico de memoria GPU: {peak_gpu_usage:.2f} GB")
        
        assert json_data["filename"] == "/home/mfllamas/Escritorio/pruebaN1.wav"
        assert json_data["status"] == "success"

def test_appstatus():
    response = client.get("/appstatus", params = {"access_token": "soyadmin"})

    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data["uptime"], str) 
    assert isinstance(json_data["whisper_version"], str) 
    assert isinstance(json_data["connected_clients"], int) 

def test_hoststatus():
    response = client.get("/hoststatus", params = {"access_token": "soyadmin"})

    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data["Memoria Reservada (GB)"], float) 


def test_appstatistics():
    response = client.get("/appstatistics", params = {"access_token": "soyadmin"})

    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data["Total queries recibidas"], int) 
    assert isinstance(json_data["Total transcripcion de archivos completos"], int) 
    assert isinstance(json_data["Tiempo total transcribiendo"], str) 

#tests simplemente para tener un 100 de coverage


