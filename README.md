# Transcriptor en tiempo real y diferido
En este proyecto he utilizado [![WhisperAI](https://github.com/openai/whisper)] para crear una API Rest que reciba peticiones de transcripción de audios en formato .wav y devuelva sus transcripciones.

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
## Poniendo en marcha la API
Para ejecutar la aplicación se debe primero ejecutar el archivo:
```
./setupt_environment.sh
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

Al darle a **Execute** si se ha hecho de manera exitosa la petición, se mostrará en el apartado de **Respuesta** el código de respuesta y el body de esta.

## Enpoints de la API
Se listan todos los endpoints de la API, su dirección y su funcionamiento.

| Método HTTP | Endpoint | Descripción | Request Parameters | Response body |
|-------------|----------|-----------|-------------|--------------|---------------|
| GET | `/openapi.json` | Devuelve metadatos de la API para el swagger-ui | - | - |
| GET | `/crearRTsession` | Crea una nueva instancia de sesión RT | access_token | String "RT_Session" |
| GET | `/api/pokemon/:id` | READ | Devuelve un Pokémon específico | - | Objeto JSON |
| PUT | `/api/pokemon/:id` | UPDATE | Modifica un Pokémon existente | Objeto JSON | Objeto JSON |
| DELETE | `/api/pokemon/:id` | DELETE | Elimina un Pokémon específico | - | Objeto JSON |


