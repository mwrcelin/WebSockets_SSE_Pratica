import json
import time
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

SERVIDOR = "http://servidor:3000"


def servidor_disponivel():
    while True:
        try:
            with urlopen(f"{SERVIDOR}/health", timeout=3) as resposta:
                if resposta.status == 200:
                    print("Servidor disponível.", flush=True)
                    return
        except (URLError, TimeoutError):
            print("Aguardando o servidor...", flush=True)
        time.sleep(2)


def enviar_evento():
    hora = datetime.now().astimezone().strftime("%H:%M:%S")
    evento = {
        "origem": "Serviço emissor Python",
        "mensagem": f"Atualização automática gerada às {hora}",
    }
    corpo = json.dumps(evento, ensure_ascii=False).encode("utf-8")
    requisicao = Request(
        f"{SERVIDOR}/webhook",
        data=corpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(requisicao, timeout=5) as resposta:
        print(f"Evento enviado às {hora}: {resposta.read().decode('utf-8')}", flush=True)


if __name__ == "__main__":
    print("Serviço emissor Python iniciado.", flush=True)
    servidor_disponivel()
    while True:
        try:
            enviar_evento()
        except (URLError, TimeoutError) as erro:
            print(f"Falha ao enviar evento: {erro}", flush=True)
        time.sleep(10)
