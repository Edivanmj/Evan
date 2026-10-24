# EVAN OS

EVAN OS é um assistente pessoal offline em Python, criado para funcionar no terminal e aprender com o usuário.

## O que é o EVAN?
EVAN significa Edivan Virtual Assistente Nativo.

## Funcionalidades
- Conversa simples no terminal
- Aprendizado explícito com frases como "aprenda que meu nome é Edivan"
- Memória persistente em SQLite
- Correção e remoção de fatos aprendidos
- Consulta a trechos de PDFs com indicação de arquivo e página
- Voz offline e reconhecimento de fala quando as dependências e o modelo Vosk estão disponíveis
- Logs locais para rastreio

## Como instalar
É necessário Python 3.10 ou superior. Para instalar os pacotes de voz e PDF:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# No Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

O modo de texto não precisa dos pacotes de voz e PDF. A fala é carregada sob demanda,
então a ausência de `pyttsx3` não impede a conversa no terminal. Os modos de voz
precisam de `sounddevice`, `vosk` e do modelo Vosk em `models/vosk-model-small-pt-0.3`.
Para configurar os microfones, execute `python mic_config.py`.

Os PDFs precisam conter texto selecionável. Páginas digitalizadas como imagem são
ignoradas; OCR ainda não está implementado.

## Como rodar
```bash
python main.py
```

## Testes
```bash
python -m unittest discover -s tests -v
```

## Exemplos de uso
```text
aprenda que EVAN significa Edivan Virtual Assistente Nativo

o que você sabe sobre EVAN?

qual é meu nome?

corrija: meu nome é Edivan Mendonça
```

## Próximas versões
- robô físico
- visão computacional

## Menu do EVAN

```bash
python evan.py
```