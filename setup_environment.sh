#!/bin/bash

set -e
cd "$(dirname "$0")"
echo "Creando entorno virtual..."
python3 -m venv myenv
if[ $? -ne 0]; then
	echo "Error creando el entorno virtual"
	exit 1
fi

echo "Activando el entorno virtual..."
source myenv/bin/activate
if[ $? -ne 0]; then
	echo "Error activando el entorno virtual"
	exit 1
fi

echo "Actualizando pip..."
pip install --upgrade pip
if[ $? -ne 0]; then
	echo "Error actualizando pip"
	exit 1
fi

echo "Instalando ffmpeg..."
sudo apt update && sudo apt install ffmpeg

echo "Instalando torch, torchvision y torchaudio..."
#instalando sin cuda
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if[ $? -ne 0]; then
	echo "Error isntalando pytorch"
	exit 1
fi

if [-f requirements.txt ]; then
	echo "Instalando dependencias desde requirements.txt..."
	pip install -r requirements.txt
	if[ $? -ne 0]; then
	echo "Error instalando dependencias desde requierements.txt"
	exit 1
	fi
else
	echo "El archivo requirements.txt no existe."
fi

echo
echo "Entorno listo"

echo "Presiona cualquier tecla para cerrar..."
read -n 1 -s