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

CHUNK = 131072
FILE = "/home/mfllamas/Escritorio/pruebaN1.wav"
OUTPUT_DIR = "../audio_chopeado"
os.makedirs(OUTPUT_DIR,exist_ok = True)
print("limpiando anterior chop")
subprocess.run(["rm","audio_chopeado/*.wav"])

def chopping(chunk_size,file_path):
    with wave.open(file_path, "rb") as wav_file:
        params = wav_file.getparams()
        while True:
            chunk = wav_file.readframes(chunk_size)
            if not chunk:
                break
            #print(chunk)
            nombre = str(random.randint(1,10000))
            audio = nombre + "chop.wav"
            file_path = os.path.join(OUTPUT_DIR, audio)
            with wave.open(file_path,"wb") as w:
                w.setparams(params)
                w.writeframes(chunk)
            print(f"Audio guardado en {file_path}")
    
def main():
    chopping(CHUNK,FILE)


if __name__ == "__main__":
    main()