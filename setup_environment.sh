#!/bin/bash

set -e  # Terminar el script si hay un error
LOG_FILE="setup.log"

log() {
    local level="$1"
    local message="$2"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a "$LOG_FILE"
}

cd "$(dirname "$0")"
log "INFO" "Iniciando setup..."

log "INFO" "Instalando python3-venv..."
sudo apt update && sudo apt install -y python3-venv || {
    log "ERROR" "Error instalando python3-venv"
    exit 1
}

log "INFO" "Creando entorno virtual..."
if ! python3 -m venv myenv; then
    log "ERROR" "Error creando el entorno virtual"
    exit 1
fi

log "INFO" "Activando el entorno virtual..."
if ! source myenv/bin/activate; then
    log "ERROR" "Error activando el entorno virtual"
    exit 1
fi

log "INFO" "Actualizando pip..."
if ! pip install --upgrade pip; then
    log "ERROR" "Error actualizando pip"
    exit 1
fi

log "INFO" "Instalando ffmpeg..."
sudo apt update && sudo apt install -y ffmpeg || {
    log "ERROR" "Error instalando ffmpeg"
    exit 1
}

log "INFO" "Instalando Uvicorn..."
if ! pip install -U uvicorn; then
    log "ERROR" "Error instalando Uvicorn"
    exit 1
fi

log "INFO" "Instalando Multipart..."
if ! pip install python-multipart; then
    log "ERROR" "Error instalando python-multipart"
    exit 1
fi

log "INFO" "Instalando torch, torchvision y torchaudio..."
if ! pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126; then
    log "ERROR" "Error instalando PyTorch"
    exit 1
fi

log "INFO" "Instalando Whisper AI..."
if ! pip install -U openai-whisper; then
    log "ERROR" "Error instalando Whisper AI"
    exit 1
fi

log "INFO" "Instalando dependencias de los tests..."
if ! pip install pytest httpx pytest-asyncio; then
    log "ERROR" "Error instalando dependencias de los tests"
    exit 1
fi

if [[ -f requirements.txt ]]; then
    log "INFO" "Instalando dependencias desde requirements.txt..."
    if ! pip install -r requirements.txt; then
        log "ERROR" "Error instalando dependencias desde requirements.txt"
        exit 1
    fi
else
    log "WARNING" "El archivo requirements.txt no existe."
fi

log "INFO" "Entorno listo."

echo "Presiona cualquier tecla para cerrar..."
read -n 1 -s
