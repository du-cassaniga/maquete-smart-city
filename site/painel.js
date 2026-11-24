// Pede os dados ao servidor Python a cada segundo e coloca na página.
const $ = id => document.getElementById(id);
const fmt = (v, casas = 1) => v == null ? "--" : Number(v).toFixed(casas).replace(".", ",");
const faixa = r => r ? `${fmt(r.min, 2)} · ${fmt(r.media, 2)} · ${fmt(r.max, 2)}` : "--";

// desenha um gráfico de linha simples dentro de um <svg>
function grafico(svg, valores) {
  const v = valores.filter(x => x != null);
  if (v.length < 2) { svg.innerHTML = ""; return; }
  // escala de pelo menos 2 unidades, para variação de 0,01 não parecer um serrote
  const meio = (Math.min(...v) + Math.max(...v)) / 2;
  const amp = Math.max(2, Math.max(...v) - Math.min(...v));
  const pts = v.map((y, i) => `${(i / (v.length - 1)) * 200},${20 - ((y - meio) / amp) * 36}`).join(" ");
  svg.innerHTML = `<polyline points="${pts}"/>`;
}

function mostrar(d) {
  const a = d.atual;
  $("faixa-teste").hidden = d.modo !== "teste";
  $("conexao").className = "conexao " + (d.online ? "ok" : "erro");
  $("conexao").textContent = d.online ? (d.porta || "online") : "maquete offline";
  if (!a) return;

  $("atualizado").textContent = (d.online ? "última leitura às " : "sem dados desde ") +
    new Date(a.hora * 1000).toLocaleTimeString("pt-BR");

  const ligado = a.poste === "ligado";
  $("poste").textContent = ligado ? "Ligado" : "Desligado";
  $("poste").className = "estado" + (ligado ? " ligado" : "");
  $("ldr").textContent = a.ldr;

  const ocupada = a.vaga === "ocupada";
  $("vaga").textContent = ocupada ? "Ocupada" : "Livre";
  $("vaga").className = "estado " + (ocupada ? "ocupada" : "livre");
  $("vaga-detalhe").textContent = ocupada ? "há um carro na vaga" : "pode estacionar";

  $("temp").textContent = fmt(a.temperatura, 2);
  $("umid").textContent = fmt(a.umidade, 0);
  grafico($("graf-temp"), d.serie.map(s => s.t));
  grafico($("graf-umid"), d.serie.map(s => s.u));

  const an = d.analise;
  if (an) {
    $("sessao").textContent = `${an.leituras} leituras em ${fmt(an.minutos)} min desde que o servidor ligou`;
    $("a-vaga").textContent = an.vaga_ocupada_pct + "% do tempo";
    $("a-chegadas").textContent = an.chegadas;
    $("a-poste").textContent = an.poste_ligado_pct + "% do tempo";
    $("a-temp").textContent = faixa(an.temperatura) + " °C";
    $("a-umid").textContent = faixa(an.umidade) + " %";
    $("a-ldr").textContent = an.ldr ? `${an.ldr.min} · ${Math.round(an.ldr.media)} · ${an.ldr.max}` : "--";
    $("avisos").innerHTML = an.avisos.map(t => `<li>${t}</li>`).join("");
  }
  $("bruto").textContent = d.json_bruto || "--";
}

async function atualizar() {
  try {
    const resposta = await fetch("/api/dados");
    mostrar(await resposta.json());
  } catch {
    $("conexao").className = "conexao erro";
    $("conexao").textContent = "servidor desligado";
  }
}

atualizar();
setInterval(atualizar, 1000);
