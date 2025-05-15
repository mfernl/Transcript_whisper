#!/bin/bash

# Activa el entorno virtual
source myenv/bin/activate

# Ejecuta la API con Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
