import requests
import time
import subprocess

API_URL = "http://localhost:8000/health" 
CHECK_INTERVAL = 120  
MAX_FAILURES = 3
TIMEOUT = 5  

failures = 0

while True:
    try:
        response = requests.get(API_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            print("API OK")
            failures = 0
        else:
            print(f"Código inesperado: {response.status_code}")
            failures += 1
    except Exception as e:
        print(f"Error: {e}")
        failures += 1

    if failures >= MAX_FAILURES:
        print("Reiniciando servidor...")
        subprocess.run("reiniciar la API")
        failures = 0

    time.sleep(CHECK_INTERVAL)
