import requests
#import librosa
#import soundfile as sf

file_path = "prueba.txt"
upload_url = "http://localhost:8000/upload"

with open(file_path,"rb") as f:
    files = {"file": (file_path,f)}
    upload_response = requests.put(upload_url, files=files)
    print(file_path)
    print(f)
    print(files)
if upload_response.status_code == 200:
    print("Archivo subido correctamente: ", upload_response.json())
else:
    print("Error al subir el archivo")