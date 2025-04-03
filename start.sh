#!/bin/bash

# Activa el entorno virtual
source myenv/bin/activate

# Ejecuta la API con Uvicorn
uvicorn app.main:app --reload
