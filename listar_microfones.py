import sounddevice as sd

devices = sd.query_devices()

print("Microfones encontrados:\n")

for i, device in enumerate(devices):
    if device["max_input_channels"] > 0:
        print(f"ID {i} - {device['name']}")
        print(f"  Canais de entrada: {device['max_input_channels']}")
        print(f"  Taxa padrão: {device['default_samplerate']}")
        print()