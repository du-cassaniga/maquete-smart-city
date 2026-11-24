# Maquete Smart City

Painel web de uma maquete de cidade inteligente. Um Arduino Uno lê os sensores
(luz, vaga de estacionamento, temperatura e umidade), envia os dados em JSON pela USB,
um servidor em Python lê, analisa e mostra tudo num site atualizado em tempo real.

```
Sensores ──► Arduino Uno ──(USB, JSON a cada 2 s)──► servidor.py (FastAPI) ──► site no navegador
```

## Como rodar

Precisa do [Python 3](https://www.python.org/downloads/) (marque **"Add python.exe to PATH"** na instalação).

- **Com o Arduino:** dois cliques em `ABRIR_SITE.bat`. Pode plugar o Arduino antes ou depois: ele é encontrado sozinho.
- **Sem o Arduino (dados de teste):** dois cliques em `ABRIR_SITE_TESTE.bat`. O site mostra uma faixa amarela "SIMULAÇÃO".

O site abre em http://localhost:8000. Na primeira vez as bibliotecas são instaladas sozinhas (precisa de internet).
Feche a Arduino IDE (ou o Monitor Serial) antes: só um programa pode usar a porta USB por vez.

Pelo terminal, o mesmo:

```
pip install -r requirements.txt
python servidor.py            # procura o Arduino
python servidor.py COM6       # porta específica
python servidor.py --teste    # sem Arduino
```

## Arquivos

| Arquivo | O que faz |
|---|---|
| `servidor.py` | Lê a porta serial (pyserial), converte o JSON, guarda o histórico, faz a análise e serve a API (FastAPI) |
| `site/index.html` | Estrutura da página |
| `site/estilo.css` | **Visual do site** |
| `site/painel.js` | Busca `/api/dados` a cada segundo e preenche a página |
| `arduino/smart_city/smart_city.ino` | Código do Arduino |

Rotas da API: `/api/dados` (tudo), `/iluminacao`, `/estacionamento`, `/clima` e `/docs` (documentação automática).

## Para quem vai mexer no visual (CSS)

1. Abra `ABRIR_SITE_TESTE.bat` (não precisa de Arduino).
2. Edite **só** o arquivo `site/estilo.css` e aperte F5 no navegador para ver.
3. Mande a mudança por Pull Request.

Pull Requests de colaboradores que alterem qualquer arquivo além de `site/estilo.css`
são barrados automaticamente pela verificação "Só CSS" (`.github/workflows/so-css.yml`).

As cores ficam no começo do arquivo, em `:root` (tema claro) e logo abaixo em
`@media (prefers-color-scheme: dark)` (tema escuro).
