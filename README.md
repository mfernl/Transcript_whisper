# Real time and Batch Speech Transcription API
This project consists of a REST API combined with [![WhisperAI](https://github.com/openai/whisper)] for GPU-accelerated (**NVIDIA**) audio transcription. Running on **Linux** OS, this project is capable of receiving .wav format audios and return transcriptions.

## Overview

The API offers two transcription modes:
- **Real-time**, via streaming sessions (`.wav` chunks broadcast over a session)
- **Batch**, via single-file upload

alongside user management, authentication, and system/usage monitoring.

## Repository Structure
```
.
├── app/                         
│   ├── __init__.py             
│   ├── database.py              # Sqlite database.
│   ├── main.py                  # API declaration, endpoints declaration.
│   ├── models.py                # Database tables.
│   └── security.py              # Password Hashing.
│
├── assets/                      
├── audio_chopeado/              # Audio fragments.          
├── swagger-ui/                  # API´s UI.
├── test_audio/                  # Test audio files.
├── testing_research/            # Previous testing before API implementation.
├── tests/               
│   └── test_fastapi.py          # Tests.
│
├── README.md
├── setup_environment.sh         # Dependency installation script.
└── start.sh                     # API init script.
```
## API setup
Before starting the API, execute the dependency script:
```
./setup_environment.sh
```
Once the dependencies are installed, run the application:
```
./start.sh
```

## How to use
Once the application is running, open the interactive UI at [http://127.0.0.1:8000/docs/#/] to try each endpoint directly as it shows the following image:
![Intefaz Interactiva](https://github.com/user-attachments/assets/c9f37544-d27a-48fd-90b8-f28ae69c4e90)

To send a request, fill with the required data:
![Endpoint](https://github.com/user-attachments/assets/675d67fd-8573-4631-9519-f72d4c5d9ee2)

Once sent, the response will be displayed below, in the Responses section.

To execute the app tests, start the Python environment as follows:
```
source myenv/bin/activate
```
Once the environment is running, execute the tests:
```
pytest -s test_fastapi.py
```

## API Endpoints

| Method | Endpoint | Description | Request Parameters | Response body |
|-------------|----------|-------------|--------------------|---------------|
| GET | `/openapi.json` | API metadata for Swagger UI | - | - |
| GET | `/crearRTsession` | Creates new real-time session | access_token | String "RT_Session" |
| GET | `/cerrarRTsession` | Closes existing real-time session | access_token, RTSessionID | JSON Object |
| PUT | `/broadcast` | Uploads .wav chunk to be transcripted inside existing real-time session| access_token, RTSessionID, Word Detection (True/False), UploadFile | JSON Object |
| PUT | `/upload` | Uploads .wav audio file to be transcripted | access_token, Word Detection (True/False), UploadFile | JSON Object |
| POST | `/register` | Register new user | AdminUsername, AdminPasswords, Username, Password | JSON Object |
| POST | `/login` | User login | Username, Password | String "access_token" |
| POST | `/logout` | User logout | access_token | String "logout completado |
| GET | `/appstatus` | Returns app status information: Uptime, Whisper version and the number of connected clients | access_token | JSON Object |
| GET | `/hoststatus` | Returns server status information: CPU/GPU/RAM usage | access_token | JSON Object |
| GET | `/appstatistics` | Returns usage stats: queries received, total transcription time | access_token | JSON Object |
| POST | `/addIWordsCsv` | Adds new key terms to the important-terms dictionary | AdminUsername, AdminPasswords | JSON Object |
| POST | `/deleteIWordsCsv` | Removes key terms (or all of them) from the dictionary | AdminUsername, AdminPasswords, DeleteAll ( 1 o 0 ) | JSON Object |

## Tech Stack

Python · FastAPI · OpenAI Whisper · SQLite · pytest · Swagger/OpenAPI

## Author

Marco Fernández Llamas — [github.com/mfernl](https://github.com/mfernl)
