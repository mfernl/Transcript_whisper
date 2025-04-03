import os
import whisper
import datetime
import torch
#modelo de transcripcion
LOAD_MODEL = "tiny"

def generar_transcripcion(input_dir,output_dir,model=LOAD_MODEL):
    disp = "gpu" if torch.cuda.is_available() else "cpu"
    print(f"Utilizando la {disp}")

    model = whisper.load_model(model, device=disp)
    os.makedirs(output_dir,exist_ok=True)
    archivos_audio = ('.mp3', '.wav', '.mov', '.aac', '.mp4', '.m4a', '.mkv', '.avi', '.flac')

    for file_name in os.listdir(input_dir):
        if not file_name.lower().endswith(archivos_audio):
            continue
        path_archivo = os.path.join(input_dir,file_name)
        nombre_archivo = os.path.splitext(file_name)[0]

        print(f"Comienzo de transcripcion del archivo: {file_name}")
        result = model.transcribe(path_archivo, verbose=False)

        content = "\n".join(segment["text"].strip() for segment in result["segments"])
        file_path = os.path.join(output_dir, f"{nombre_archivo}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Terminado de transcribir: {file_name}")

        

def main():
    input_dir = "input"
    output_dir = "output"
    generar_transcripcion(input_dir,output_dir)
if __name__ == "__main__":
    main()