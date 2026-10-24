

# #EVAN OS — Edivan Virtual Assistente Nativo

EVAN OS é um assistente pessoal offline em Python, criado para funcionar no terminal e aprender com o usuário.

O projeto foi idealizado para se tornar mais do que um assistente virtual: um companheiro artificial capaz de conversar, aprender com as experiências, guardar lembranças e evoluir ao lado de seu criador ao longo dos anos.

## O que é o EVAN?
EVAN significa Edivan Virtual Assistente Nativo.

## Funcionalidades
- Conversa simples no terminal
- Aprendizado explícito com frases como "aprenda que meu nome é Edivan"
- Memória persistente em SQLite
- Correção e remoção de fatos aprendidos
- Consulta a trechos de PDFs com indicação de arquivo e página
- Voz offline e reconhecimento de fala quando as dependências e o modelo Vosk estão disponíveis
- Conversa livre offline com modelo GGUF via `llama-cpp-python`
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

### Modelo de linguagem local

O arquivo usado por este projeto é
[`Qwen2.5-3B-Instruct-Q4_K_M.gguf`](https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/blob/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf),
armazenado em `models/llm`. O EVAN escolhe o primeiro `.gguf` nessa pasta em
ordem alfabética. Para selecionar outro, defina `EVAN_MODEL_PATH` com um caminho
absoluto ou relativo à pasta do projeto. O modelo é carregado quando o EVAN
precisa responder a uma pergunta fora dos comandos e respostas locais.

No PowerShell, para selecionar explicitamente o modelo baixado:

```powershell
$env:EVAN_MODEL_PATH = "F:\evan_os\models\llm\Qwen2.5-3B-Instruct-Q4_K_M.gguf"
python main.py
```

O modelo Qwen2.5-3B-Instruct está sob a Qwen Research License, limitada a uso não
comercial. Leia a licença do modelo antes de usar ou redistribuir os pesos. O
arquivo GGUF é grande e está excluído do Git; cada computador precisa baixá-lo
separadamente.

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
## Estalação futura

pip install -r requirements.txt

Esse ajuste serve para uma instalação nova, por exemplo em outro computador ou no futuro mini PC do robô, sem o pip tentar compilar tudo do zero.
