from fastapi import FastAPI, UploadFile, HTTPException, Form
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import os
from pydub import AudioSegment
from io import BytesIO
import wave
from collections import namedtuple
import random
import shutil
import uuid
from datetime import datetime, timedelta
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
warnings.simplefilter(action="ignore",category=FutureWarning)

clave = subprocess.run(["openssl", "rand", "-hex", "32"], capture_output=True)  #cada vez que se inicia el servidor se crea una clave
LOAD_MODEL = "tiny"
SECRET_KEY = clave.stdout.decode("utf-8").strip() #stdout es la salida del comando en shell, y strip se usa para quitar el \n final
TOKEN_EXP_SECS = 400
RTSESSION_EXP_TOKEN = 3600
WHISPER_VERSION = "v20240930"
CONNECTED_CLIENTS = 0
QUERIES_RECEIVED = 0
FILE_TRANSCRIPTIONS = 0
TIME_SPENT_TRANSCRIPTING = timedelta()

revoked_tokens = set()

server_start_time = datetime.now()

sesiones = {}

db_users = {
    "articuno" : {
        "id": 0,
        "username": "articuno",
        "password": "12345"
    }
}

app = FastAPI()

def get_user(username: str, db: list):
    if username in db:
        return db[username]
    
def autenticate_user(password: str, password_form: str):
    if password_form == password:
        return True
    return False

def create_token(data: list):
    data_token = data.copy()
    expiracion = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_EXP_SECS) #sumarle a la hora actual el timedelta deseado
    data_token["exp"] = expiracion.isoformat()
    print(data_token["exp"])
    token_jwt = jwt.encode(data_token, key=SECRET_KEY, algorithm="HS256")
    return token_jwt

def create_RTtoken(data: list):
    data_token = data.copy()
    expiracion = datetime.now(timezone.utc) + timedelta(seconds=RTSESSION_EXP_TOKEN) #sumarle a la hora actual el timedelta deseado
    data_token["exp"] = expiracion.isoformat()
    print(data_token["exp"])
    token_jwt = jwt.encode(data_token, key=SECRET_KEY, algorithm="HS256")
    return token_jwt

class ExpiredTokenError(Exception):
    pass
class InvalidTokenError(Exception):
    pass

#carpeta donde almacenar el audio
AUDIO_DIR = "./audio_recibido"
os.makedirs(AUDIO_DIR, exist_ok=True)

#carpeta donde almacenar audio temporalmente
TEMP_DIR = "./temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

async def compruebo_token(access_token):
    try:
        if access_token in revoked_tokens:
            raise InvalidTokenError(
                "El token ha sido revocado"
            )
        user_data = jwt.decode(access_token, key=SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        print(f"JWT: {user_data}")
        expiration_date_str = user_data.get("exp")
        expiration_date = datetime.fromisoformat(expiration_date_str)
        if get_user(user_data["username"],db_users) is None:
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
    
async def compruebo_RTsession(RTsession_token):
    try:
        RT_tokendata = jwt.decode(RTsession_token, key=SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        print(f"JWT_RT: {RT_tokendata}")
        expiration_date_str = RT_tokendata.get("exp")
        expiration_date = datetime.fromisoformat(expiration_date_str)
        
        #comprobar que el token utilizado para hacer el RT token es válido
        await compruebo_token(RT_tokendata["user_token"])

        if datetime.now(timezone.utc) > expiration_date:
            raise ExpiredTokenError(
                "El token ha expirado"
            )
    except Exception as e:
        raise HTTPException(
            status_code=401, detail=str(e)
        )


@app.get("/crearRTsession")
async def crear_RTsession(access_token):

    await compruebo_token(access_token)
    token_RT = create_RTtoken({"user_token": access_token})
    if token_RT not in sesiones:
        sesiones[token_RT] = {
            "user_token": access_token,
            "transcription": []
        }
        print(sesiones)
        return {"session_id": token_RT}
    else:
        raise HTTPException(
            status_code=400, detail="Sesión duplicada"
        )
    

@app.get("/cerrarRTsession")
async def cerrar_RTsession(access_token, RTsession_token):
    
    await compruebo_token(access_token)
    if RTsession_token not in sesiones:
        raise HTTPException(
            status_code=404, detail="No se ha encontrado la sesión"
        )
 
    full_transcription = "".join(sesiones[RTsession_token]["transcription"])
    del sesiones[RTsession_token]
    return{ "session_id": RTsession_token, "full_transcription": full_transcription}


@app.put("/transmission")
async def transcript_chunk(access_token, RTsession_token, uploaded_file: UploadFile):

    await compruebo_token(access_token)

    #comprobar el token de sesión 
    if RTsession_token not in sesiones:
        raise HTTPException(
            status_code=404, detail="No se ha encontrado la sesión"
        )
    
    await compruebo_RTsession(RTsession_token)
    #chunk debe de ser de no más de 2s chunk_size=1024?
    chunk = await uploaded_file.read()
    wav_io = io.BytesIO(chunk)
    with wave.open(wav_io, "rb") as wav_file:
        params = wav_file.getparams()
    audio = await save_temp_audio(chunk,params)
    out = await generar_transcripcion(audio,TEMP_DIR)
    print(audio)

    sesiones[RTsession_token]["transcription"].append(out)

    path_archivo = os.path.join(TEMP_DIR,audio)

    os.remove(path_archivo)

    return {"session_id": session_id, "transcripcion": out}


async def save_temp_audio(audio_sample,audio_params):
    nombre = str(random.randint(1,100))
    audio = nombre + "temp.wav"
    file_path = os.path.join(TEMP_DIR, audio)
    with wave.open(file_path,"wb") as w:
        w.setparams(audio_params)
        w.writeframes(audio_sample)
    print(f"Audio guardado en {file_path}")
    return audio


@app.put("/upload")
async def upload_archivo(uploaded_file: UploadFile, access_token):

    await compruebo_token(access_token)
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
    nombre = await save_audio(audioFile,params)

    output_dir = "output_transcripcion"
    out = await generar_transcripcion(nombre,AUDIO_DIR) #se puede añadir un output_dir

    endTranscription = datetime.now()
    spentTranscripting = endTranscription - startTranscription

    global TIME_SPENT_TRANSCRIPTING
    TIME_SPENT_TRANSCRIPTING = TIME_SPENT_TRANSCRIPTING + spentTranscripting

    return {"filename": uploaded_file.filename, "status": "success", "params": params, "duracion": str(timedelta(seconds=int(spentTranscripting.total_seconds()))), "transcripcion": out}

async def save_audio(audio_sample,audio_params):
    nombre = str(random.randint(1,100))
    audio = nombre + "audio.wav"
    file_path = os.path.join(AUDIO_DIR, audio)
    with wave.open(file_path,"wb") as w:
        w.setparams(audio_params)
        w.writeframes(audio_sample)
    print(f"Audio guardado en {file_path}")
    return audio


async def generar_transcripcion(nombre,input_dir):
    disp = "gpu" if torch.cuda.is_available() else "cpu"
    print(f"Utilizando la {disp}")

    def transcript():
        print(f"usando model: {LOAD_MODEL}")
        model = whisper.load_model(LOAD_MODEL, device=disp)
        path_archivo = os.path.join(input_dir,nombre)
        result = model.transcribe(path_archivo,verbose=False)
        #content = "\n".join(segment["text"].strip() for segment in result["segments"])
        content_w_timestamps = []
        for segment in result["segments"]:
            content_w_timestamps.append({
                "start": f"{segment["start"]:.2f}",
                "end": f"{segment["end"]:.2f}",
                "text": segment["text"].strip()
            })
        return content_w_timestamps
        print(content_w_timestamps)
    content = await asyncio.to_thread(transcript)
    return content
    """
    model = whisper.load_model(model, device=disp)
    os.makedirs(output_dir,exist_ok=True)
    archivos_audio = ('.mp3', '.wav', '.mov', '.aac', '.mp4', '.m4a', '.mkv', '.avi', '.flac')

    for file_name in os.listdir(input_dir):
        if not nombre.lower().endswith(archivos_audio):
            continue
        if file_name == nombre:
            path_archivo = os.path.join(input_dir,nombre)

            print(f"Comienzo de transcripcion del archivo: {nombre}")
            result = model.transcribe(path_archivo, verbose=False)

            print(f"Whisper devuelve: {result}")

            content = "\n".join(segment["text"].strip() for segment in result["segments"])
            
            print(f"Terminado de transcribir: {nombre}")
            return content
    print (f"Archivo {nombre} no encontrado")
    return "Archivo no encontrado"
    """

@app.post("/login")
async def login(username: str, password: str):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    user_data = get_user(username,db_users)
    if user_data is None:
        raise HTTPException(
            status_code=404,
            detail="No User found"
        )
    if not autenticate_user(user_data["password"],password):
        raise HTTPException(
            status_code=401,
            detail="Password error"
        )
    token = create_token({"username": user_data["username"]})
    global CONNECTED_CLIENTS
    CONNECTED_CLIENTS += 1
    return token

@app.post("/logout")
async def logout(access_token):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    revoked_tokens.add(access_token)
    return {"message": "logout completado"}

@app.get("/appstatus")
async def requestAppStatus(access_token):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    await compruebo_token(access_token)
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
async def requestHostStatus(access_token):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    await compruebo_token(access_token)
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return {"Porcentage de uso de la cpu": cpu,
    "Porcentage de uso de la ram": ram}

@app.get("/appstatistics")
async def requestAppStatistics(access_token):

    global QUERIES_RECEIVED
    QUERIES_RECEIVED += 1

    await compruebo_token(access_token)

    return {
        "Total queries recibidas": QUERIES_RECEIVED,
        "Total transcripcion de archivos completos": FILE_TRANSCRIPTIONS,
        "Tiempo total transcribiendo": str(timedelta(seconds=int(TIME_SPENT_TRANSCRIPTING.total_seconds())))
    }



    

    
    

        