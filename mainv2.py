from fastapi import FastAPI, File, UploadFile
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

@app.get("/transcripcion")
def probando():
    #fastprueba.generar_transcripcion("audio_recibido","output_transcripcion")
    """try:
        result = subprocess.run(["python", "fastprueba.py"], capture_output=True, text=True)
        output = result.stdout
        if result.returncode != 0:
            return {"error": result.stderr}
        
        return {"message": "Transcripción completada", "output": output}
    
    except Exception as e:
        return {"error": str(e)}"""
    return {"message": "Hola fastapi"}
    
@app.put("/upload")
async def upload_archivo(file: UploadFile = File()):
    #with open(f"./upload_files/{file.filename}","wb") as f:
        #shutil.copyfileobj(file.file, f)
    content = await file.read()
    print(content)
    return {"filename": file.filename, "status": "success", "contents": content}
    

        