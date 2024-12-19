from fastapi import FastAPI, UploadFile, HTTPException
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
warnings.simplefilter(action="ignore",category=FutureWarning)

LOAD_MODEL = "medium"
SECRET_KEY = "a72dd5c2bad38471504e1ce24427d30703fdb8c4b8f046058d8d7bb934454270"
TOKEN_EXP_SECS = 40

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
    expiracion = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_EXP_SECS)
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

@app.get("/pruebas")
async def hola_mundo(access_token):
    try:
        user_data = jwt.decode(access_token, key=SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        print(f"Que es esto: {user_data}")
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

    return "Hola mundo desde la API"

@app.put("/upload")
async def upload_archivo(uploaded_file: UploadFile):

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

    input_dir = "audio_recibido"
    output_dir = "output_transcripcion"
    out = await generar_transcripcion(nombre,input_dir,output_dir)

    return {"filename": uploaded_file.filename, "status": "success", "params": params, "transcripcion": out}

async def save_audio(audio_sample,audio_params):
    nombre = str(random.randint(1,100))
    audio = nombre + "audio.wav"
    file_path = os.path.join(AUDIO_DIR, audio)
    with wave.open(file_path,"wb") as w:
        w.setparams(audio_params)
        w.writeframes(audio_sample)
    print(f"Audio guardado en {file_path}")
    return audio


async def generar_transcripcion(nombre,input_dir,output_dir,model=LOAD_MODEL):
    disp = "gpu" if torch.cuda.is_available() else "cpu"
    print(f"Utilizando la {disp}")

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

            content = "\n".join(segment["text"].strip() for segment in result["segments"])
            
            print(f"Terminado de transcribir: {nombre}")
            return content
    print (f"Archivo {nombre} no encontrado")
    return "Archivo no encontrado"

@app.post("/login")
async def login(username: str, password: str):
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
    return token
    
    

        