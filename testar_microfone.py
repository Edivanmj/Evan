from hearing import EvanHearing

hearing = EvanHearing()

texto = hearing.listen_once(seconds=6)

if texto:
    print(f"Você falou: {texto}")
else:
    print("Não consegui entender nada. Tente falar mais perto do microfone.")