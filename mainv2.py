from fastapi import FastAPI, UploadFile
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
#import fastprueba
import subprocess
import io
import torch
import datetime
import whisper
import warnings
warnings.simplefilter(action="ignore",category=FutureWarning)
LOAD_MODEL = "medium"

app = FastAPI()

#carpeta donde almacenar el audio
AUDIO_DIR = "./audio_recibido"
os.makedirs(AUDIO_DIR, exist_ok=True)

audio_data = bytearray()

class ConnectionWS:
    def __init__(self):
        self.active_connections = [] #constructor de la clase, inicializo una lista vacía
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket) #nueva conexión entre cliente y servidor
    async def send_msg(self, msg: str, websocket: WebSocket):
        await websocket.send_text(msg)
    async def disconnect(self, websocket: WebSocket):
        await websocket.close()
        self.active_connections.remove(websocket)

cnx = ConnectionWS()
@app.websocket("/conexion")
async def websocket_endpoint(websocket: WebSocket):
    await cnx.connect(websocket)
    print(f"Cliente {cnx.active_connections} conectado")

    audio_data = bytearray()
    Audio_params = namedtuple("_wave_params",["nchannels","sampwidth","framerate","nframes","comptype","compname"])
    params_salida = ()
    try:
        params = await websocket.receive_text()
        print(f"Recibido: {params}",websocket)
        await cnx.send_msg(f"Recibido {params}",websocket)
        cadena = tuple(params.split(","))
        audio_params = Audio_params(
            nchannels=int(cadena[0]),
            sampwidth=int(cadena[1]),
            framerate=int(cadena[2]),
            nframes=int(cadena[3]),
            comptype=cadena[4],
            compname=cadena[5]
        )
        params_salida = audio_params
        print(f"Parametros en tupla: {params_salida}")
        #primer intercambio de mensajes, recibo los params y le mando el mensaje al cliente
        while True:
            data = await websocket.receive_bytes()
            #print(f"Recibido: {data}",websocket)
            audio_data.extend(data) #append el nuevo bloque de audio al resto
            await cnx.send_msg(f"Recibido bytes",websocket)
            #prueba para ver si se envía todo
            control = await websocket.receive_text()
            #print(f"Recibido : {control}")
    except WebSocketDisconnect:
        print(f"Cliente {cnx.active_connections} desconectado")
        print(f"Parametros en tupla: {params_salida}")
        save_audio(audio_data,params_salida)

def save_audio(audio_sample,audio_params):
    #audio = AudioSegment.from_raw(BytesIO(audio_sample))
    nombre = str(random.randint(1,100))
    audio = nombre + "audio.wav"
    file_path = os.path.join(AUDIO_DIR, audio)
    #audio.export(file_path, format="wav")
    with wave.open(file_path,"wb") as w:
        w.setparams(audio_params)
        w.writeframes(audio_sample)
    print(f"Audio guardado en {file_path}")
 
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

    
    

        