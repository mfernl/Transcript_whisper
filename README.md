# Transcriptor en tiempo real y diferido
En este proyecto he utilizado [![WhisperAI](https://github.com/openai/whisper)] para crear una API Rest en un equipo con sistema operativo **Linux**, con tarjeta gráfica (GPU) de **NVIDIA**, que reciba peticiones de transcripción de audios en formato .wav y devuelva sus transcripciones.

## Setup
La estructura de este repositorio es la siguiente:
```
.
├── app/                         #Directorio principal de la aplicación.
│   ├── __init__.py             
│   ├── database.py              #Archivo de inicialización de base de datos sqlite.
│   ├── main.py                  #Archivo principal de la API, declaración de endpoints.
│   ├── models.py                #Archivo de declaración de las tablas en la base de datos.
│   └── security.py              #Archivo para el hasheo de contraseñas.
│
├── assets/                      #Directorio para archivos adicionales como csv para los test.
├── audio_chopeado/              #Directorio con archivos de audio creados al separar un archivo de audio original en distintas partes.          
├── swagger-ui/                  #Directorio para la representación interactiva de la API.
├── test_audio/                  #Directorio con archivos de audio para los test.
├── testing_research/            #Directorio con pruebas anteriores a la implementación de la API y otras pruebas.
├── tests/               
│   └── test_fastapi.py          #Tests de la aplicación.
│
├── README.md
├── setup_environment.sh         #Script para instalar las dependencias.
└── start.sh                     #Script para iniciar la API.
```
## Poniendo en marcha la API
Para ejecutar la aplicación se debe primero ejecutar el archivo:
```
./setup_environment.sh
```
Una vez instaladas las dependencias, iniciar la aplicación con:
```
./start.sh
```

## Cómo usar la API
Una vez encendido el servidor en el equipo local, acceda a la url definida para la interfaz interactiva swagger [http://127.0.0.1:8000/docs/#/]. Dentro de esta url se debería mostrar la siguiente interfaz:
![Intefaz Interactiva](https://github.com/user-attachments/assets/c9f37544-d27a-48fd-90b8-f28ae69c4e90)

En la interfaz podemos ver cada uno de los endpoints de la API, para mandar una petición a cada endpoint simplemente debemos hacer click en el endpoint deseado y rellenar los campos necesarios para lanzar una petición a la API:
![Endpoint](https://github.com/user-attachments/assets/675d67fd-8573-4631-9519-f72d4c5d9ee2)

Al darle a **Execute** si se ha hecho de manera exitosa la petición, se mostrará en el apartado de **Respuesta** el código de respuesta y la respuesta del servidor.

Para ejecutar los tests, se debe iniciar el entorno virtual de python mediante
```
source myenv/bin/activate
```
Una vez activado el entorno, dentro de la carpeta tests/ ejecutar los test de la siguiente manera
```
pytest -s test_fastapi.py
```

## Enpoints de la API
Se listan todos los endpoints de la API, su dirección y su funcionamiento.

| Método HTTP | Endpoint | Descripción | Request Parameters | Response body |
|-------------|----------|-------------|--------------------|---------------|
| GET | `/openapi.json` | Devuelve metadatos de la API para el swagger-ui | - | - |
| GET | `/crearRTsession` | Crea una nueva instancia de sesión RT | access_token | String "RT_Session" |
| GET | `/cerrarRTsession` | Cierra un canal de sesión RT | access_token, RTSessionID | Objeto JSON |
| PUT | `/broadcast` | Sube un archivo de audio en formato .wav para transcribir a través de un canal de sesión RT | access_token, RTSessionID, Word Detection (True/False), UploadFile | Objeto JSON |
| PUT | `/upload` | Sube un archivo de audio en formato .wav para transcribir | access_token, Word Detection (True/False), UploadFile | Objeto JSON |
| POST | `/register` | Registra un nuevo usuario en la base de datos | AdminUsername, AdminPasswords, Username, Password | Objeto JSON |
| POST | `/login` | Inicio de sesión para un usuario | Username, Password | String "access_token" |
| POST | `/logout` | Cierra sesión para un usuario | access_token | String "logout completado |
| GET | `/appstatus` | Devuelve datos como el Uptime, versión de Whisper y el número de clientes conectados | access_token | Objeto JSON |
| GET | `/hoststatus` | Devuelve datos del dispositivo servidor como el uso de la CPU, GPU o RAM | access_token | Objeto JSON |
| GET | `/appstatistics` | Devuelve datos sobre el uso de la aplicación como número de querys recibidas o tiempo total transcribiendo | access_token | Objeto JSON |
| POST | `/addIWordsCsv` | Añade nuevos términos importantes a la base de datos para la detección de términos importantes en las transcripciones | AdminUsername, AdminPasswords | Objeto JSON |
| POST | `/deleteIWordsCsv` | Elimina términos importantes de la base de datos o elimina todos los términos de la base de datos | AdminUsername, AdminPasswords, DeleteAll ( 1 o 0 ) | Objeto JSON |


