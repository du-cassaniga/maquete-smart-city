"""
Servidor da maquete Smart City.

Fluxo:  Arduino --(USB/serial, uma linha JSON a cada 2 s)--> este programa --(HTTP)--> site

Como rodar:
    python servidor.py            -> procura o Arduino sozinho
    python servidor.py COM6       -> usa uma porta específica
    python servidor.py --teste    -> sem Arduino, gera leituras de mentira (o site avisa "SIMULAÇÃO")
Depois abra http://localhost:8000
"""

import json
import random
import sys
import threading
import time
from collections import deque
from pathlib import Path

import serial                      # pyserial: conversa com a porta USB
import serial.tools.list_ports
import uvicorn                     # roda o FastAPI
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

PASTA = Path(__file__).parent
LIMIAR_LDR = 50          # mesmo valor do sketch: abaixo disso o poste liga
OFFLINE_APOS = 10        # segundos sem leitura = maquete fora do ar

# ---------------------------------------------------------------------------
# Estado compartilhado entre a thread que lê o Arduino e o FastAPI
# ---------------------------------------------------------------------------
ultima = None                       # última leitura (dicionário)
ultima_em = 0.0                     # quando ela chegou (time.time())
ultima_bruta = ""                   # a linha exatamente como veio do Arduino
historico = deque(maxlen=600)       # ~20 min de leituras (uma a cada 2 s)
inicio = time.time()
porta_em_uso = None
modo_teste = "--teste" in sys.argv
trava = threading.Lock()


def guardar(linha):
    """Recebe uma linha de texto do Arduino, converte o JSON e guarda."""
    global ultima, ultima_em, ultima_bruta
    try:
        dados = json.loads(linha)
    except json.JSONDecodeError:
        return  # linha cortada ou mensagem que não é JSON: ignora
    if "ldr" not in dados:
        return
    dados["hora"] = time.time()
    with trava:
        ultima, ultima_em, ultima_bruta = dados, dados["hora"], linha
        historico.append(dados)


def achar_arduino():
    """Procura nas portas USB alguma que pareça um Arduino."""
    for p in serial.tools.list_ports.comports():
        texto = f"{p.description} {p.manufacturer}".lower()
        if p.vid in (0x2341, 0x2A03, 0x1A86, 0x0403, 0x10C4) or "arduino" in texto or "ch340" in texto:
            return p.device
    return None


def ler_arduino():
    """Fica lendo a serial para sempre. Se o cabo sair, tenta reconectar."""
    global porta_em_uso
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    while True:
        porta = argumentos[0] if argumentos else achar_arduino()
        if not porta:
            print("Arduino não encontrado. Tentando de novo em 3 s...")
            time.sleep(3)
            continue
        try:
            with serial.Serial(porta, 9600, timeout=5) as ser:
                porta_em_uso = porta
                print(f"Lendo o Arduino em {porta}")
                while True:
                    linha = ser.readline().decode("utf-8", errors="ignore").strip()
                    if linha:
                        guardar(linha)
        except serial.SerialException as erro:
            porta_em_uso = None
            print(f"Problema na porta {porta}: {erro}")
            if "Acesso negado" in str(erro) or "Access is denied" in str(erro) or "PermissionError" in str(erro):
                print("  -> Feche o Monitor Serial da Arduino IDE.")
            time.sleep(3)


def simular():
    """Modo --teste: gera leituras no mesmo formato do Arduino."""
    global porta_em_uso
    porta_em_uso = "simulação"
    ldr, temp, umid = 300, 24.0, 60.0
    while True:
        ldr = max(0, min(1023, ldr + random.randint(-60, 60)))
        temp += random.uniform(-0.2, 0.2)
        umid += random.uniform(-0.8, 0.8)
        guardar(json.dumps({
            "ldr": ldr,
            "poste": "ligado" if ldr < LIMIAR_LDR else "desligado",
            "vaga": random.choice(["livre", "ocupada"]),
            "temperatura": round(temp, 2),
            "umidade": round(umid, 2),
        }))
        time.sleep(2)


# ---------------------------------------------------------------------------
# Análise dos dados (feita em cima do histórico guardado)
# ---------------------------------------------------------------------------
def resumo(valores):
    valores = [v for v in valores if v is not None]
    if not valores:
        return None
    media = sum(valores) / len(valores)
    return {"media": round(media, 2), "min": round(min(valores), 2), "max": round(max(valores), 2)}


def analisar(lista):
    if not lista:
        return None
    total = len(lista)
    ocupada = [d["vaga"] == "ocupada" for d in lista]
    ligado = [d["poste"] == "ligado" for d in lista]
    # quantas vezes um carro chegou (vaga passou de livre para ocupada)
    chegadas = sum(1 for a, b in zip(ocupada, ocupada[1:]) if not a and b)

    temp = resumo([d.get("temperatura") for d in lista])
    umid = resumo([d.get("umidade") for d in lista])

    # classificação simples do clima atual
    atual = lista[-1]
    t, u = atual.get("temperatura"), atual.get("umidade")
    avisos = []
    if t is not None and t >= 30:
        avisos.append("Calor: temperatura acima de 30 °C.")
    if t is not None and t <= 12:
        avisos.append("Frio: temperatura abaixo de 12 °C.")
    if u is not None and u >= 80:
        avisos.append("Ar muito úmido (acima de 80%).")
    if u is not None and u <= 30:
        avisos.append("Ar muito seco (abaixo de 30%).")
    if t is None or u is None:
        avisos.append("Sensor DHT22 sem leitura.")

    return {
        "leituras": total,
        "minutos": round((lista[-1]["hora"] - lista[0]["hora"]) / 60, 1),
        "vaga_ocupada_pct": round(100 * sum(ocupada) / total),
        "chegadas": chegadas,
        "poste_ligado_pct": round(100 * sum(ligado) / total),
        "ldr": resumo([d["ldr"] for d in lista]),
        "temperatura": temp,
        "umidade": umid,
        "avisos": avisos,
    }


# ---------------------------------------------------------------------------
# API (FastAPI)
# ---------------------------------------------------------------------------
app = FastAPI(title="Smart City - Maquete")


@app.middleware("http")
async def sem_cache(request, chamar):
    """Faz o navegador sempre pegar a versão mais nova do site e dos dados."""
    resposta = await chamar(request)
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


def online():
    return ultima is not None and time.time() - ultima_em < OFFLINE_APOS


@app.get("/api/dados")
def dados():
    """Tudo o que o site precisa numa resposta só."""
    with trava:
        lista = list(historico)
        atual, bruta = ultima, ultima_bruta
    return {
        "online": online(),
        "modo": "teste" if modo_teste else "arduino",
        "porta": porta_em_uso,
        "atual": atual,
        "json_bruto": bruta,
        "analise": analisar(lista),
        # últimos ~2 min para os gráficos pequenos
        "serie": [{"t": d["temperatura"], "u": d["umidade"], "ldr": d["ldr"]} for d in lista[-60:]],
    }


# Rotas separadas por recurso (mesmos nomes dos recursos CoAP do trabalho)
@app.get("/iluminacao")
def iluminacao():
    if not online():
        return JSONResponse({}, status_code=503)
    return {"ldr": ultima["ldr"], "poste": ultima["poste"]}


@app.get("/estacionamento")
def estacionamento():
    if not online():
        return JSONResponse({}, status_code=503)
    return {"vaga": ultima["vaga"]}


@app.get("/clima")
def clima():
    if not online():
        return JSONResponse({}, status_code=503)
    return {"temperatura": ultima["temperatura"], "umidade": ultima["umidade"]}


# O site (index.html, estilo.css, painel.js) fica na pasta "site"
app.mount("/", StaticFiles(directory=PASTA / "site", html=True), name="site")


if __name__ == "__main__":
    threading.Thread(target=simular if modo_teste else ler_arduino, daemon=True).start()
    print("Site em http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
