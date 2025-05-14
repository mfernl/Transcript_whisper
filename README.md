##Transcriptor en tiempo real y diferido
En este proyecto he utilizado [![WhisperAI](https://github.com/openai/whisper)] para crear una API Rest que reciba peticiones de transcripción de audios en formato .wav y devuelva sus transcripciones.

##Setup
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
├── swagger-ui/                  #Directorio para la representación interactiva de la API.
├── testing_research/            #Directorio con pruebas anteriores a la implementación de la API y otras pruebas.
├── tests/               
│   └── test_fastapi.py          #Tests de la aplicación.
│
├── README.md
├── setup.log                    #Log del script de instalación de dependencias.
├── setup_environment.sh         #Script para instalar las dependencias.
└── start.sh                     #Script para iniciar la API.
```
##Start
Para ejecutar la aplicación se debe primero ejecutar el archivo:
```
./setupt_environment.sh
```
Una vez instaladas las dependencias, iniciar la aplicación con:
```
./start.sh
```
