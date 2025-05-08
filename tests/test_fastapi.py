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
import os
from jiwer import wer
from app.models import User
from app.database import SessionLocal
from app.security import hash_password


client = TestClient(app)

db = SessionLocal()
existing = db.query(User).filter_by(username = "articuno").first()
if not existing:
    new_user = User(username = "articuno", password = hash_password("12345"))
    db.add(new_user)
    db.commit()
    db.close()
existing = db.query(User).filter_by(username = "gyarados").first()
if not existing:
    new_user = User(username = "gyarados", password = hash_password("12345"))
    db.add(new_user)
    db.commit()
    db.close()

logger = logging.getLogger(__name__)
logging.basicConfig(filename='pruebas.log', encoding='utf-8', level=logging.DEBUG)

def test_get_openapi():
    response = client.get("/openapi.json")

    assert response.status_code == 200

def test_token_revocado():
    login = client.post("/login", params={"username": "articuno", "password": "12345"})
    token_rev = login.json()
    assert login.status_code == 200

    logout = client.post("/logout", params={"access_token": token_rev})

    assert logout.json() == {"message": "logout completado"}

    appstatus = client.get("/appstatus", params={"access_token": token_rev})

    assert appstatus.status_code == 401
    assert appstatus.json() == {"detail": "El token ha sido revocado"}

def test_wrong_user():
    badusertoken = create_token({"username": "vileplume"})

    appstatus = client.get("/appstatus", params={"access_token": badusertoken})

    assert appstatus.status_code == 401
    assert appstatus.json() == {"detail": "El usuario no es valido"}

def test_expired_token():
    data_token = {"username": "articuno"}
    expiracion = datetime.now(timezone.utc) + timedelta(seconds=-2) #sumarle a la hora actual el timedelta deseado
    data_token["exp"] = expiracion.isoformat()
    print(data_token["exp"])
    token_jwt = jwt.encode(data_token, key=SECRET_KEY, algorithm="HS256")

    appstatus = client.get("/appstatus", params={"access_token": token_jwt})

    assert appstatus.status_code == 401
    assert appstatus.json() == {"detail": "El token ha expirado"}

def mock_create_idRT(data):
    # Forzar un valor estático para id_RT
    return "0#articuno"  

def test_duplicated_session():

    # Login para obtener el token de acceso
    response = client.post("/login", params={"username": "articuno", "password": "12345"})
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
    assert response.json() == {"detail": "User not found"}

def test_login_no_username():
    
    response = client.post("/login", params={"username": "", "password": "12345"})
    
    assert response.status_code == 404
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "User not found"}

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
        response = client.put("/broadcast", params={"access_token": token.json(), "RTsession_id": rtId, "iWordDetection": False}, files=files)

    assert response.status_code == 200
    json_data = response.json()
    print(f"esta es la json_data {json_data}")
    assert json_data["transcripcion"][0]["start"] == "0.00"

def test_upload_notWavFile():
    file_path = "/home/mfllamas/Escritorio/pruebaOtroFormat.mp3"  # Ruta del archivo real
    
    # Abrir el archivo en modo binario
    with open(file_path, "rb") as file:
        files = {"uploaded_file": (file_path, file, "audio/x-wav")}
        
        # Hacer la petición PUT con el archivo en formato mp3
        response = client.put("/upload", params={"access_token": "soyadmin", "iWordDetection": False}, files=files)

    # Verificar que la respuesta es correcta
    assert response.status_code == 400
    assert response.json() == {"detail": "Solo se permiten archivos .wav"}

def test_broadcastnotWavFile():
    file_path = "/home/mfllamas/Escritorio/pruebaOtroFormat.mp3"  # Ruta del archivo real
    
    token = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert token.status_code == 200
    sesion = client.get("/crearRTsession", params={"access_token": token.json()})
    rtId = sesion.json()["session_id"]
    assert sesion.status_code == 200

    with open(file_path, "rb") as file:
        files = {"uploaded_file": (file_path, file, "audio/x-wav")}
        
        # Hacer la petición PUT con el archivo real
        response = client.put("/broadcast", params={"access_token": token.json(), "RTsession_id": rtId, "iWordDetection": False}, files=files)

    assert response.status_code == 400
    assert response.json() == {"detail": "Solo se permiten archivos .wav"}

@pytest.mark.asyncio
async def test_transmision_w_session_closed():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as ac:
        #Crear una sesión con caducidad inmediata para probar el caso que se haya cerrado por inactividad
        token = await ac.post("/login", params={"username": "gyarados", "password": "12345"})
        assert token.status_code == 200

        user_data = jwt.decode(token.json(), key=SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        id_RT = await create_idRT({"user": user_data["username"]})
        expiracion = datetime.now(timezone.utc) + timedelta(seconds=-2) #timedelta negativo para asegurar la caducidad inmediata
        exp_iso = expiracion.isoformat()
        if id_RT not in sesiones:
            sesiones[id_RT] = {
                "user_token": token.json(),
                "cierre_inactividad": exp_iso,
                "transcription": [""]
            }
        
        file_path = "/home/mfllamas/Escritorio/pruebaN1.wav"  # Ruta del archivo real

        print(sesiones)

        # Abrir el archivo en modo binario
        with open(file_path, "rb") as file:
            files = {"uploaded_file": (file_path, file, "audio/x-wav")}
            
            # Hacer la petición PUT con el archivo real
            response = await ac.put("/broadcast", params={"access_token": token.json(), "RTsession_id": id_RT, "iWordDetection": False}, files=files)

        print(response.json())
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
        response = client.put("/upload", params={"access_token": "soyadmin", "iWordDetection":False}, files=files)

    # Verificar que la respuesta es correcta
    assert response.status_code == 200
    json_data = response.json()
  
    assert json_data["filename"] == "/home/mfllamas/Escritorio/pruebaN1.wav"
    assert json_data["status"] == "success"

#@pytest.mark.skip(reason="ahorrar tiempo")
def test_subir_archivos_RT():
    rutaArchivos = "/home/mfllamas/Escritorio/whisperAPI/Transcript_whisper/audio_chopeado/"
    token = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert token.status_code == 200
    sesion = client.get("/crearRTsession", params={"access_token": token.json()})
    rtId = sesion.json()["session_id"]
    assert sesion.status_code == 200

    archivos = os.listdir(rutaArchivos)

    print(f"archivos test subir RT: {archivos}")
    for audio in archivos:
        file_path = rutaArchivos + audio
        with open(file_path, "rb") as file:
            files = {"uploaded_file": (file_path, file, "audio/x-wav")}
            
            # Hacer la petición PUT con el archivo real
            response = client.put("/broadcast", params={"access_token": token.json(), "RTsession_id": rtId, "iWordDetection": False}, files=files)

        assert response.status_code == 200
        json_data = response.json()
        print(f"esta es la json_data {json_data}")
        assert json_data["session"] == rtId
#@pytest.mark.skip(reason="ahorrar tiempo")
def test_appstatus():
    response = client.get("/appstatus", params = {"access_token": "soyadmin"})

    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data["uptime"], str) 
    assert isinstance(json_data["whisper_version"], str) 
    assert isinstance(json_data["connected_clients"], int) 
#@pytest.mark.skip(reason="ahorrar tiempo")
def test_hoststatus():
    response = client.get("/hoststatus", params = {"access_token": "soyadmin"})

    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data["Memoria Reservada (GB)"], float) 

#@pytest.mark.skip(reason="ahorrar tiempo")
def test_appstatistics():
    response = client.get("/appstatistics", params = {"access_token": "soyadmin"})

    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data["Total queries recibidas"], int) 
    assert isinstance(json_data["Total transcripcion de archivos completos"], int) 
    assert isinstance(json_data["Tiempo total transcribiendo"], str) 


@pytest.mark.asyncio
#@pytest.mark.skip(reason="ahorrar tiempo")
async def test_subir_archivo_async():
    usuarios = 10
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
                return await ac.put("/upload", params={"access_token": "soyadmin", "iWordDetection": False}, files=files)
        
        gpu_usages = []

        async def medir_gpu():
            #Medir el uso de la memoria 
            while not test_done:
                uso_gpu = torch.cuda.memory_allocated(0) / 1e9  # Convertir a GB
                gpu_usages.append(uso_gpu)
                await asyncio.sleep(0.5) 

        test_done = False
        task_monitor = asyncio.create_task(medir_gpu())
        startTime = datetime.now()
        response = await asyncio.gather(*[subir_archivo() for _ in range(usuarios)])
        endtime = datetime.now()
        test_done = True
        await task_monitor 
        #response = await subir_archivo()#un audio solo
        print("Estoy testando upload")
        tiempo = endtime - startTime
        out = (str(timedelta(seconds=int(tiempo.total_seconds()))))

        avg_gpu_usage = statistics.mean(gpu_usages) if gpu_usages else 0
        peak_gpu_usage = max(gpu_usages) if gpu_usages else 0

        print(f"Tiempo transcribiendo con {usuarios} usuarios: {out}")
        print(f"Uso medio de GPU: {avg_gpu_usage:.2f} GB")
        print(f"Pico de memoria GPU: {peak_gpu_usage:.2f} GB")
        
        for resp in response:
            json_data = resp.json()
            assert json_data["filename"] == "/home/mfllamas/Escritorio/pruebaN1.wav"
            assert json_data["status"] == "success"


#@pytest.mark.skip(reason = "ahorrar tiempo")
@pytest.mark.asyncio
async def test_subir_archivos_varias_sesiones_RT():
    rutaArchivos = "/home/mfllamas/Escritorio/whisperAPI/Transcript_whisper/audio_chopeado/"
    token = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert token.status_code == 200
    num_sesiones = 10
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as ac:
        
        archivos = os.listdir(rutaArchivos)

        async def real_time():
            sesion = await ac.get("/crearRTsession", params={"access_token": token.json()})
            rtId = sesion.json()["session_id"]
            print(f"sesión creada: {rtId}")
            assert sesion.status_code == 200

            responses = []

            for audio in archivos:
                file_path = os.path.join(rutaArchivos,audio)
                with open(file_path, "rb") as file:
                    files = {"uploaded_file": (file_path, file, "audio/x-wav")}
                    
                    # Hacer la petición PUT con el archivo real
                    res = await ac.put("/broadcast", params={"access_token": token.json(), "RTsession_id": rtId, "iWordDetection": False}, files=files)
                    responses.append(res)
            return responses
            

        startTime = datetime.now()
        all_sessions = await asyncio.gather(*[real_time() for _ in range(num_sesiones)])
        endTime = datetime.now()

        for sesion in all_sessions:
            for response in sesion:
                assert response.status_code == 200
        print(sesiones)

        tiempo = endTime - startTime
        out = (str(timedelta(seconds=int(tiempo.total_seconds()))))
        print(f"Tiempo en crear {num_sesiones} sesiones y transcribir: {out}")

#@pytest.mark.skip(reason = "ahorrar tiempo")
@pytest.mark.asyncio
async def test_battlefield():
    rutaRT = "/home/mfllamas/Escritorio/whisperAPI/Transcript_whisper/audio_chopeado/"
    usuarios = 2
    num_sesiones = 10
    #login
    token = client.post("/login", params={"username": "articuno", "password": "12345"})
    assert token.status_code == 200

    file_path = "/home/mfllamas/Escritorio/pruebaN1.wav"
    archivosRT = os.listdir(rutaRT)
    
    gpu_usages = []
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as ac:
        
        async def subir_archivo():
        # Abrir el archivo en modo binario
            with open(file_path, "rb") as file:
                files = {"uploaded_file": (file_path, file, "audio/x-wav")}
                return await ac.put("/upload", params={"access_token": "soyadmin", "iWordDetection": False}, files=files)
        

        async def medir_gpu():
            #Medir el uso de la memoria 
            while not test_done:
                uso_gpu = torch.cuda.memory_allocated(0) / 1e9  # Convertir a GB
                gpu_usages.append(uso_gpu)
                await asyncio.sleep(0.5) 

        async def real_time():
            sesion = await ac.get("/crearRTsession", params={"access_token": token.json()})
            rtId = sesion.json()["session_id"]
            print(f"sesión creada: {rtId}")
            assert sesion.status_code == 200

            responses = []

            for audio in archivosRT:
                file_path = os.path.join(rutaRT, audio)
                with open(file_path, "rb") as file:
                    files = {"uploaded_file": (file_path, file, "audio/x-wav")}
                    
                    # Hacer la petición PUT con el archivo real
                    res = await ac.put("/broadcast", params={"access_token": token.json(), "RTsession_id": rtId, "iWordDetection": False}, files=files)
                    responses.append(res)
                await asyncio.sleep(0.1)
            return responses

        test_done = False
        task_monitor = asyncio.create_task(medir_gpu())
        startTime = datetime.now()
        upload_tasks = [asyncio.create_task(subir_archivo()) for _ in range(usuarios)]

        rt_tasks = [asyncio.create_task(real_time()) for _ in range(num_sesiones)]

        all_tasks = await asyncio.gather(*upload_tasks, *rt_tasks)

        endtime = datetime.now()
        test_done = True
        await task_monitor 

        tiempo = endtime - startTime
        out = (str(timedelta(seconds=int(tiempo.total_seconds()))))

        avg_gpu_usage = statistics.mean(gpu_usages) if gpu_usages else 0
        peak_gpu_usage = max(gpu_usages) if gpu_usages else 0

        print(f"Tiempo transcribiendo con {usuarios} usuarios y {num_sesiones} sesiones: {out}")
        print(f"Uso medio de GPU: {avg_gpu_usage:.2f} GB")
        print(f"Pico de memoria GPU: {peak_gpu_usage:.2f} GB")


        for resp in all_tasks:
            if isinstance(resp, list):  # Respuestas RT
                for r in resp:
                    assert r.status_code == 200
                    data = r.json()
                    print(f"RT transcription: {data["session"]}")
            else:  # Respuesta upload
                assert resp.status_code == 200
                print(f"Upload: {resp.json()["status"]}")
        
#@pytest.mark.skip(reason = "audio de 1 hora")
@pytest.mark.asyncio
async def test_word_error_rate():

    usuarios = 10

    reference = "Hola, hola, hola. Estamos probando nuevo audio en el nuevo PC.We are testing. This is audio number one.Number two, number three, number four.Testing long audio.Edificio, árbol, teclado.Número, número, número, número, número, número, número."

    file_path = "/home/mfllamas/Escritorio/pruebaN1.wav"  # Ruta del archivo real

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as ac:

        async def subir_archivo():
        # Abrir el archivo en modo binario
            with open(file_path, "rb") as file:
                files = {"uploaded_file": (file_path, file, "audio/x-wav")}
                return await ac.put("/upload", params={"access_token": "soyadmin","iWordDetection":False}, files=files)

        response = await asyncio.gather(*[subir_archivo() for _ in range(usuarios)])

        sumWer = 0

        for resp in response:
            hypothesis = ""
            audio = resp.json()["transcription"]
            for text in audio:
                hypothesis = hypothesis + text["text"]
            sumWer += wer(reference, hypothesis)
        
        globWer = sumWer/usuarios

        print(f"El WER de {usuarios} usuarios es del {globWer}")
    return 0


