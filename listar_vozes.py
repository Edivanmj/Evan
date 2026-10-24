import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty("voices")

print("Vozes instaladas no Windows:\n")

for index, voice in enumerate(voices):
    print(f"ID {index}")
    print(f"Nome: {voice.name}")
    print(f"Identificador: {voice.id}")
    print()