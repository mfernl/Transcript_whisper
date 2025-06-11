from pydub import AudioSegment
from pydub.generators import WhiteNoise


original = AudioSegment.from_file("vanilla.wav", format="wav")

# Crear una copia con "retardo"
delay_ms = 250
attenuation = -6  # reducir volumen del eco

# Añadir silencio antes de la copia (delay)
echo = AudioSegment.silent(duration=delay_ms) + original + AudioSegment.silent(duration=0)
echo = echo + attenuation  # bajar volumen del eco

# Mezclar original con el eco (superposición)
with_echo = original.overlay(echo)

delay_ms = 500
attenuation = -10 

echo = AudioSegment.silent(duration=delay_ms) + with_echo + AudioSegment.silent(duration=0)
echo = echo + attenuation  

with_echo2 = original.overlay(echo)


with_echo2.export("test_with_echo.wav", format="wav")

# Generar ruido blanco con la misma duración que el audio
noise = WhiteNoise().to_audio_segment(duration=len(original))

# Atenuar el ruido para que no sea molesto (volumen en dB)
noise = noise - 40  # más bajo es menos ruidoso

# Mezclar ruido con el audio original
with_noise = original.overlay(noise)

with_noise.export("test_with_noise.wav", format="wav")

