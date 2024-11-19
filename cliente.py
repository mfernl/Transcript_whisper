import asyncio
import websockets
import wave
from pydub import AudioSegment
#import librosa
#import soundfile as sf



async def send_msg():
    uri = "ws://localhost:8000/conexion"
    async with websockets.connect(uri) as websocket: 
        #x = librosa.load("prueba1.wav",sr=16000)
        #sf.write("towav.wav", x, 16000)
        comprueboMp3()
        #necesito leer los parámetros del audio para enviarlos al servidor
        with wave.open("prueba1.wav","rb") as w:
            chunk_size = 1024
            params = w.getparams()
            #getparams devuelve una named tuple, pasarlo a string para pasarlo al servidor
            sparams = ",".join(map(str,params))
            print(f"Leyendo parametros: {params}")
            #enviar al servidor los parametros:
            await websocket.send(sparams)
            print(f"Parametros enviados: {sparams}")
            msg = await websocket.recv()
            print(f"Mensaje del servidor: {msg}")
            data = w.readframes(chunk_size)
            print(f"Bytes: {data}")
            print(f"Estoy en= {w.tell()}")
            while data:
                await websocket.send(data)
                data = w.readframes(chunk_size)
                mensaje = await websocket.recv()
                print(f"Mensaje del servidor: {mensaje}")
                print(f"Estoy en= {w.tell()}")
                control = w.tell()
                await websocket.send(f"Estoy en {control}")
                print(f"bytes: {data}")
        print("audio enviado al servidor")
        w.close()
        await websocket.close()
        #msg = await websocket.recv()
        #print(f"Mensaje del servidor: {msg}")

def comprueboMp3():
    audio = AudioSegment.from_file("prueba2.mp3")
    audio.export("prueba1.wav",format="wav")

asyncio.run(send_msg())