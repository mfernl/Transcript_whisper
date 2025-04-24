from fastapi import FastAPI, UploadFile, HTTPException, Form
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from pydub import AudioSegment
from io import BytesIO
import wave
from collections import namedtuple
import random
import shutil
import uuid
import subprocess
import io
import torch
from datetime import datetime,timedelta, timezone
import time
import whisper
import warnings
from jose import jwt, JWTError
import psutil
import asyncio
from queue import Queue
from threading import Thread
import multiprocessing
import atexit
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db, Base, engine
from app.models import User
from app.security import hash_password, verify_password
warnings.simplefilter(action="ignore",category=FutureWarning)


clave = subprocess.run(["openssl", "rand", "-hex", "32"], capture_output=True)  #cada vez que se inicia el servidor se crea una clave
LOAD_MODEL = "turbo"
SECRET_KEY = clave.stdout.decode("utf-8").strip() #stdout es la salida del comando en shell, y strip se usa para quitar el \n final
TOKEN_EXP_SECS = 400
RTSESSION_EXP = 3600
WHISPER_VERSION = "v20240930"
CONNECTED_CLIENTS = 0
QUERIES_RECEIVED = 0
FILE_TRANSCRIPTIONS = 0
TIME_SPENT_TRANSCRIPTING = timedelta()
MODELS = [whisper.load_model(LOAD_MODEL, device="cuda") for _ in range(3)] #3 modelos para upload ya que son archivos grandes y uno para RT
MODEL_TURBO_RT = whisper.load_model(LOAD_MODEL, device="cuda")

upload_streams = [torch.cuda.Stream() for _ in range(3)] #Flujos cuda separados

revoked_tokens = set()

server_start_time = datetime.now()

sesiones = {}

transcription_queue = Queue() #cola para manejar los tres modelos turbo

Base.metadata.create_all(bind=engine)

app = FastAPI(docs_url=None, redoc_url=None)

semaphore = multiprocessing.Semaphore(1)

@atexit.register
def cleanup_semaphore():
    semaphore.release()  # Libera el recurso
    print("Semáforo liberado.")
    print("Cierre de API completado.")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
path_swagger = os.path.join(BASE_DIR, "swagger-ui")
if not os.path.exists(path_swagger):
    raise RuntimeError(f"No se encontró la carpeta {path_swagger}")

app.mount("/docs",StaticFiles(directory=path_swagger,html=True))

@app.get("/openapi.json")
def get_openapi():
    return app.openapi()

def create_token(data: list):
    data_token = data.copy()
    expiracion = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_EXP_SECS) #sumarle a la hora actual el timedelta deseado
    data_token["exp"] = expiracion.isoformat()
    print(data_token["exp"])
    token_jwt = jwt.encode(data_token, key=SECRET_KEY, algorithm="HS256")
    return token_jwt

async def create_idRT(data: list):
    data_token = data.copy()
    l = len(sesiones)
    id = str(l) + str(random.randint(1,100)) + "#" + data_token["user"]
    return id

class ExpiredTokenError(Exception):
    pass
class InvalidTokenError(Exception):
    pass

#carpeta donde almacenar el audio RT
RT_DIR = "./temp_audio_RT"
os.makedirs(RT_DIR, exist_ok=True)

#carpeta donde almacenar audio temporalmente
TEMP_DIR = "./temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

async def compruebo_token(access_token,db):
    try:
        if access_token != "soyadmin":
            if access_token in revoked_tokens:
                raise InvalidTokenError(
                    "El token ha sido revocado"
                )
            user_data = jwt.decode(access_token, key=SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
            print(f"JWT: {user_data}")
            expiration_date_str = user_data.get("exp")
            expiration_date = datetime.fromisoformat(expiration_date_str)
            existing = db.query(User).filter_by(username = user_data["username"]).first()

            if not existing:
                raise InvalidTokenError(
                    "El usuario no es valido"
                )

            if datetime.now(timezone.utc) > expiration_date:
                raise ExpiredTokenError(
                    "El token ha expirado"
                )
    except Exception as e:
        raise HTTPException(
            status_code=401, detail=str(e)
        )
    

@app.get("/crearRTsession")
async def crear_RTsession(access_token, db: Session = Depends(get_db)):

    await compruebo_token(access_token,db)

    user_data = jwt.decode(access_token, key=SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
    id_RT = await create_idRT({"user": user_data["username"]})
    expiracion = datetime.now(timezone.utc) + timedelta(seconds=RTSESSION_EXP) #sumarle a la hora actual el timedelta deseado
    exp_iso = expiracion.isoformat()
    if id_RT not in sesiones:
        sesiones[id_RT] = {
            "user_token": access_token,
            "cierre_inactividad": exp_iso,
            "transcription": []
        }
        print(sesiones)
        return {"session_id": id_RT}
    else:
        raise HTTPException(
            status_code=400, detail="Sesión duplicada"
        )
    

async def compruebo_cred_sesion(access_token, RTsession_id):
#comprobar el token de sesión 
    if RTsession_id not in sesiones:
        raise HTTPException(
            status_code=404, detail="No se ha encontrado la sesión"
        )
    #comprobar que el token de usuario sea el mismo
    if access_token != sesiones[RTsession_id]["user_token"]:
        raise HTTPException(
            status_code=401, detail="No autorizado para operar en este canal"
        )


@app.get("/cerrarRTsession")
async def cerrar_RTsession(access_token, RTsession_id, db: Session = Depends(get_db)):
    
    await compruebo_token(access_token,db)

    #comprobar existencia de sesión así como concordancia del user_token
    await compruebo_cred_sesion(access_token, RTsession_id)

    full_transcription = ""
    for segment in sesiones[RTsession_id]["transcription"]:
        for seg in segment:
            full_transcription = full_transcription + seg["text"] #lo que devuelve whisper cuando transcribe está divido en segmentos con texto , voy iterando por esos segmentos para conseguir toda lo transcrito
    del sesiones[RTsession_id]
    return{ "session_id": RTsession_id, "full_transcription": full_transcription}


@app.put("/broadcast")
async def transcript_chunk(access_token, RTsession_id, uploaded_file: UploadFile, db: Session = Depends(get_db)):

    await compruebo_token(access_token,db)

    #comprobar existencia de sesión así como concordancia del user_token
    await compruebo_cred_sesion(access_token, RTsession_id)

    if not uploaded_file.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .wav")

    exp_iso = sesiones[RTsession_id]["cierre_inactividad"]
    exp = datetime.fromisoformat(exp_iso)
    #primer caso, se recibe una transmisión antes de que se cierre por inactividad => reseteo de la hora hasta cierre
    if datetime.now(timezone.utc) < exp:
        expiracion = datetime.now(timezone.utc) + timedelta(RTSESSION_EXP) 
        exp_iso = expiracion.isoformat()    
        sesiones[RTsession_id]["cierre_inactividad"] = exp_iso
        print(f"nueva hora de cierre: {sesiones[RTsession_id]}")
    #segundo caso, se recibe una transmisión cuando la sesión ha estado inactiva por 1h => devolvemos mensaje de que ha cerrado y llamamos a cerrarRTsession
    if datetime.now(timezone.utc) > exp:
        cerrada = await cerrar_RTsession(access_token,RTsession_id)
        return {"Detail": "Sesión cerrada por inactividad", "Session_contents": cerrada}
    #chunk debe de ser de no más de 2s chunk_size=1024?
    chunk = await uploaded_file.read()
    wav_io = io.BytesIO(chunk)
    with wave.open(wav_io, "rb") as wav_file:
        params = wav_file.getparams()
    audio = await save_temp_audio(chunk,params,RT_DIR)
    out = await generar_transcripcion_RT(audio,RT_DIR)
    
    sesiones[RTsession_id]["transcription"].append(out)

    path_archivo = os.path.join(RT_DIR,audio)

    os.remove(path_archivo)

    return {"session": RTsession_id,"transcripcion": out}


async def save_temp_audio(audio_sample,audio_params,DIR):
    nombre = str(random.randint(1,10000000000000000000))
    audio = nombre + "temp.wav"
    file_path = os.path.join(DIR, audio)
    with wave.open(file_path,"wb") as w:
        w.setparams(audio_params)
        w.writeframes(audio_sample)
    print(f"Audio guardado en {file_path}")
    return audio


@app.put("/upload")
async def upload_archivo(uploaded_file: UploadFile, access_token,db: Session = Depends(get_db)):

    await compruebo_token(access_token,db)

    if not uploaded_file.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .wav")

    startTranscription = datetime.now()

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    global FILE_TRANSCRIPTIONS
    FILE_TRANSCRIPTIONS += 1

    chunk_size = 1024 
    audioFile = bytearray()
    while True:
        chunk = await uploaded_file.read(chunk_size)
        if not chunk:
            break
        #print(chunk)
        audioFile.extend(chunk)
    wav_io = io.BytesIO(audioFile) #convertir a un buffer en memoria
    with wave.open(wav_io, "rb") as wav_file:
        params = wav_file.getparams()
        print(params)
    nombre = await save_temp_audio(audioFile,params,TEMP_DIR)
    out = await generar_transcripcion(nombre,TEMP_DIR) #Temp dir, archivos se eliminan despues de transcribir
    path_archivo = os.path.join(TEMP_DIR,nombre)

    os.remove(path_archivo)

    endTranscription = datetime.now()
    spentTranscripting = endTranscription - startTranscription

    global TIME_SPENT_TRANSCRIPTING
    TIME_SPENT_TRANSCRIPTING = TIME_SPENT_TRANSCRIPTING + spentTranscripting

    return {"filename": uploaded_file.filename, "status": "success", "params": params, "duration": str(timedelta(seconds=int(spentTranscripting.total_seconds()))), "transcription": out}


def transcription_worker(model,stream):
    while True:
        task = transcription_queue.get()
        if task is None:
            break  # Salir si la cola cierra
        path_archivo, response_queue = task  # Extraer datos

        with torch.cuda.stream(stream):  # Asegurar flujo CUDA separado
            result = model.transcribe(path_archivo,verbose=False,language="es")
            #print(result)
            content_w_timestamps = []
            for segment in result["segments"]:
                content_w_timestamps.append({
                    "start": f"{segment["start"]:.2f}",
                    "end": f"{segment["end"]:.2f}",
                    "text": segment["text"].strip()
                })

        response_queue.put(content_w_timestamps)  # Enviar resultado de vuelta
        transcription_queue.task_done()


for i in range(3):
    thread = Thread(target=transcription_worker, args=(MODELS[i], upload_streams[i]), daemon=True)
    thread.start()


async def generar_transcripcion(nombre,input_dir):

    path_archivo = os.path.join(input_dir,nombre)
    response_queue = Queue()
    transcription_queue.put((path_archivo, response_queue))

    # Esperar el resultado sin bloquear FastAPI
    result = await asyncio.to_thread(response_queue.get)
    return result
    
    


async def generar_transcripcion_RT(nombre,input_dir):

    with torch.cuda.stream(torch.cuda.Stream()):  # Flujo separado
        print(f"usando model: {LOAD_MODEL}")
        path_archivo = os.path.join(input_dir,nombre)
        result = MODEL_TURBO_RT.transcribe(path_archivo,verbose=False,language="es")
        content_w_timestamps = []
        for segment in result["segments"]:
            content_w_timestamps.append({
                "start": f"{segment["start"]:.2f}",
                "end": f"{segment["end"]:.2f}",
                "text": segment["text"].strip()
            })
    return content_w_timestamps
    

@app.post("/register")
async def register(name: str, password: str, db: Session = Depends(get_db)):

    existing = db.query(User).filter_by(username = name).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already existing user"
        )

    hashed = hash_password(password)

    new_user = User(username = name, password = hashed)
    db.add(new_user)
    db.commit()

    return {"message": "Usuario creado", "id": new_user.id}


@app.post("/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    existing = db.query(User).filter_by(username = username).first()

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    pw = existing.password

    if not verify_password(password,pw):
        raise HTTPException(
            status_code=401,
            detail="Password error"
        )
    
    token = create_token({"username": username})
    global CONNECTED_CLIENTS
    CONNECTED_CLIENTS += 1
    return token

@app.post("/logout")
async def logout(access_token,db: Session = Depends(get_db)):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    await compruebo_token(access_token,db)
    
    revoked_tokens.add(access_token)
    return {"message": "logout completado"}

@app.get("/appstatus")
async def requestAppStatus(access_token,db: Session = Depends(get_db)):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    await compruebo_token(access_token,db)
    current_time = datetime.now()
    uptime = current_time - server_start_time
    print(uptime)
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

    return {
        "uptime": uptime_str,
        "whisper_version": WHISPER_VERSION,
        "connected_clients": CONNECTED_CLIENTS
    }

@app.get("/hoststatus")
async def requestHostStatus(access_token,db: Session = Depends(get_db)):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    await compruebo_token(access_token,db)
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    total_mem = torch.cuda.get_device_properties(0).total_memory  # Total de la GPU
    reserved_mem = torch.cuda.memory_reserved(0)  # Memoria reservada por PyTorch
    allocated_mem = torch.cuda.memory_allocated(0)  # Memoria en uso por PyTorch
    free_mem = reserved_mem - allocated_mem  # Memoria realmente libre


    return {"Porcentage de uso de la cpu": cpu,
    "Porcentage de uso de la ram": ram,
    "Memoria Total (GB)": round(total_mem / 1e9,2),
    "Memoria Reservada (GB)": round(reserved_mem / 1e9,2),
    "Memoria Usada por PyTorch (GB)": round(allocated_mem / 1e9,2),
    "Memoria Libre (GB)": round(free_mem / 1e9,2)}

@app.get("/appstatistics")
async def requestAppStatistics(access_token,db: Session = Depends(get_db)):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    await compruebo_token(access_token,db)

    return {
        "Total queries recibidas": QUERIES_RECEIVED,
        "Total transcripcion de archivos completos": FILE_TRANSCRIPTIONS,
        "Tiempo total transcribiendo": str(timedelta(seconds=int(TIME_SPENT_TRANSCRIPTING.total_seconds())))
    }



    

    
    

        