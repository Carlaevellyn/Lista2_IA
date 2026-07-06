"use strict";

// Estado do cliente.
let sid = null;            // id da sessão de consulta ativa
let varAtual = null;       // variável da pergunta em aberto
let nPerguntas = 0;        // contador de perguntas respondidas
let baseAtual = null;      // metadados da base carregada
let llmDisponivel = false; // camada de IA (explicações naturais) ativa?

// Atalhos de DOM.
const $ = (id) => document.getElementById(id);
const views = ["view-inicio", "view-pergunta", "view-resultado", "view-carregando"];

function mostrarView(id) {
  views.forEach((v) => $(v).classList.toggle("hidden", v !== id));
  esconderMensagem();
}

function mostrarMensagem(texto) {
  const el = $("mensagem");
  el.textContent = texto;
  el.classList.remove("hidden");
}
function esconderMensagem() { $("mensagem").classList.add("hidden"); }

async function api(rota, opcoes) {
  const resp = await fetch(rota, opcoes);
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dados.erro || `Erro ${resp.status}`);
  return dados;
}

// --------------------------------------------------------------------------- //
// Base de conhecimento                                                         //
// --------------------------------------------------------------------------- //
async function carregarEstadoBase() {
  baseAtual = await api("/api/base");
  $("dominio").textContent = baseAtual.dominio || "Expert Shell";
  $("subtitulo").textContent = baseAtual.arquivo
    ? `${baseAtual.n_regras} regras · ${baseAtual.arquivo}`
    : "Nenhuma base carregada";

  // seletor de bases
  const sel = $("seletor-base");
  sel.innerHTML = "";
  (baseAtual.bases_disponiveis || []).forEach((nome) => {
    const opt = document.createElement("option");
    opt.value = nome;
    opt.textContent = nome.replace(/\.json$/, "");
    if (nome === baseAtual.arquivo) opt.selected = true;
    sel.appendChild(opt);
  });

  renderizarDrawer();
}

function renderizarDrawer() {
  $("qtd-regras").textContent = `(${baseAtual.n_regras})`;
  const ul = $("lista-regras");
  ul.innerHTML = "";
  baseAtual.regras.forEach((r) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="rid">${r.id}</span>${escapeHtml(r.texto)}`;
    ul.appendChild(li);
  });
  const uv = $("lista-variaveis");
  uv.innerHTML = "";
  baseAtual.variaveis.forEach((v) => {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${escapeHtml(v.nome)}</strong><span class="vtipo">${v.tipo}</span>`;
    uv.appendChild(li);
  });
}

// --------------------------------------------------------------------------- //
// Consulta                                                                     //
// --------------------------------------------------------------------------- //
async function iniciarConsulta(modo) {
  nPerguntas = 0;
  mostrarView("view-carregando");
  try {
    const ev = await api("/api/consulta", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modo }),
    });
    sid = ev.sid;
    tratarEvento(ev);
  } catch (e) {
    mostrarView("view-inicio");
    mostrarMensagem(e.message);
  }
}

async function responder(valor) {
  $("caixa-porque").classList.add("hidden");
  mostrarView("view-carregando");
  try {
    const ev = await api("/api/responder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sid, valor }),
    });
    if (valor !== null) nPerguntas++;
    tratarEvento(ev);
  } catch (e) {
    mostrarMensagem(e.message);
  }
}

function tratarEvento(ev) {
  if (ev.tipo === "pergunta") return mostrarPergunta(ev);
  if (ev.tipo === "resultado") return mostrarResultado(ev);
  if (ev.tipo === "erro") {
    mostrarView("view-inicio");
    mostrarMensagem(ev.msg || "Erro na consulta.");
  }
}

function mostrarPergunta(ev) {
  varAtual = ev.variavel;
  $("texto-pergunta").textContent = ev.pergunta;
  $("nome-variavel").textContent = `variável: ${ev.variavel}`;
  $("contador-perguntas").textContent =
    nPerguntas > 0 ? `${nPerguntas} pergunta(s) respondida(s)` : "";
  $("caixa-porque").classList.add("hidden");

  const cont = $("opcoes");
  cont.innerHTML = "";
  (ev.valores || []).forEach((val) => {
    const btn = document.createElement("button");
    btn.className = "opcao";
    btn.type = "button";
    btn.textContent = val;
    btn.addEventListener("click", () => responder(val));
    cont.appendChild(btn);
  });
  // se a variável não tem valores fechados, oferece campo livre
  if (!ev.valores || ev.valores.length === 0) {
    const inp = document.createElement("input");
    inp.type = "text";
    inp.placeholder = "Digite o valor e Enter";
    inp.className = "opcao";
    inp.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && inp.value.trim()) responder(inp.value.trim());
    });
    cont.appendChild(inp);
  }
  mostrarView("view-pergunta");
}

// Renderiza uma explicação numa caixa e, se a IA estiver disponível, adiciona
// um botão para reescrevê-la em linguagem natural (alternando com a técnica).
function preencherExplicacao(caixa, url, textoSimbolico) {
  caixa.innerHTML = "";
  const corpo = document.createElement("div");
  corpo.className = "exp-corpo";
  corpo.textContent = textoSimbolico;
  caixa.appendChild(corpo);

  if (!llmDisponivel) return;

  const botao = document.createElement("button");
  botao.className = "btn link exp-ia";
  botao.type = "button";
  botao.textContent = "🤖 Tornar natural (IA)";
  caixa.appendChild(botao);

  let estado = "tecnico";     // tecnico | natural
  let textoNatural = null;    // cache local da reescrita

  botao.addEventListener("click", async () => {
    if (estado === "natural") {
      corpo.textContent = textoSimbolico;
      estado = "tecnico";
      botao.textContent = "🤖 Tornar natural (IA)";
      return;
    }
    if (textoNatural === null) {
      botao.disabled = true;
      botao.textContent = "🤖 Reescrevendo…";
      try {
        const d = await api(url + (url.includes("?") ? "&" : "?") + "natural=1");
        botao.disabled = false;
        if (d.fonte === "fallback") {
          botao.textContent = "🤖 IA indisponível agora";
          return;
        }
        textoNatural = d.texto_natural || d.texto;
      } catch (e) {
        botao.disabled = false;
        botao.textContent = "🤖 Falhou — tentar de novo";
        return;
      }
    }
    corpo.textContent = textoNatural;
    estado = "natural";
    botao.textContent = "Ver explicação técnica";
  });
}

async function verPorque() {
  const caixa = $("caixa-porque");
  if (!caixa.classList.contains("hidden")) {
    caixa.classList.add("hidden");
    return;
  }
  try {
    const url = `/api/porque?sid=${encodeURIComponent(sid)}`;
    const d = await api(url);
    preencherExplicacao(caixa, url, d.texto);
    caixa.classList.remove("hidden");
  } catch (e) {
    mostrarMensagem(e.message);
  }
}

// --------------------------------------------------------------------------- //
// Resultado                                                                    //
// --------------------------------------------------------------------------- //
function corCF(cf) {
  if (cf >= 70) return "var(--ok)";
  if (cf >= 40) return "var(--warn)";
  return "var(--bad)";
}

function mostrarResultado(ev) {
  const cont = $("resultado-conteudo");
  cont.innerHTML = "";
  let houve = false;

  (ev.objetivos || []).forEach((obj) => {
    if (!obj.conclusoes.length) return;
    houve = true;
    const bloco = document.createElement("div");
    bloco.className = "objetivo-bloco";
    bloco.innerHTML = `<h3>${escapeHtml(obj.objetivo)}</h3>`;

    obj.conclusoes.forEach((c) => {
      const cf = Math.max(0, Math.min(100, c.cf));
      const div = document.createElement("div");
      div.className = "conclusao";
      div.innerHTML = `
        <div class="conclusao-topo">
          <span class="conclusao-valor">${escapeHtml(c.valor)}</span>
          <span class="conclusao-cf">confiança ${c.cf.toFixed(0)}</span>
        </div>
        <div class="barra"><span style="width:${cf}%;background:${corCF(cf)}"></span></div>`;
      const btn = document.createElement("button");
      btn.className = "btn link btn-como";
      btn.type = "button";
      btn.textContent = "Como cheguei a isto?";
      const exp = document.createElement("div");
      exp.className = "explicacao hidden";
      btn.addEventListener("click", () => alternarComo(obj.objetivo, c.valor, exp));
      div.appendChild(btn);
      div.appendChild(exp);
      bloco.appendChild(div);
    });
    cont.appendChild(bloco);
  });

  if (!houve) {
    cont.innerHTML =
      `<p class="muted">Nenhuma conclusão pôde ser estabelecida com as evidências fornecidas.</p>`;
  }

  const rd = $("regras-disparadas");
  if (ev.regras_disparadas && ev.regras_disparadas.length) {
    rd.innerHTML = "Regras disparadas: " +
      ev.regras_disparadas.map((r) => `<code>${escapeHtml(r)}</code>`).join("");
  } else {
    rd.innerHTML = "";
  }
  mostrarView("view-resultado");
}

async function alternarComo(objetivo, valor, caixa) {
  if (!caixa.classList.contains("hidden")) {
    caixa.classList.add("hidden");
    return;
  }
  try {
    const url = `/api/como?sid=${encodeURIComponent(sid)}&var=${encodeURIComponent(objetivo)}&val=${encodeURIComponent(valor)}`;
    const d = await api(url);
    preencherExplicacao(caixa, url, d.texto);
    caixa.classList.remove("hidden");
  } catch (e) {
    mostrarMensagem(e.message);
  }
}

// --------------------------------------------------------------------------- //
// Drawer e seletor de base                                                     //
// --------------------------------------------------------------------------- //
function abrirDrawer() {
  $("drawer").classList.remove("hidden");
  $("overlay").classList.remove("hidden");
}
function fecharDrawer() {
  $("drawer").classList.add("hidden");
  $("overlay").classList.add("hidden");
}

async function trocarBase(arquivo) {
  try {
    await api("/api/carregar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ arquivo }),
    });
    sid = null;
    await carregarEstadoBase();  // já refaz o fetch de /api/base e re-renderiza
    mostrarView("view-inicio");
  } catch (e) {
    mostrarMensagem(e.message);
  }
}

// --------------------------------------------------------------------------- //
// Utilidades                                                                   //
// --------------------------------------------------------------------------- //
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// --------------------------------------------------------------------------- //
// Ligações de eventos                                                          //
// --------------------------------------------------------------------------- //
document.querySelectorAll(".card-estrategia").forEach((c) => {
  c.addEventListener("click", () => iniciarConsulta(c.dataset.modo));
});
$("btn-naosei").addEventListener("click", () => responder(null));
$("btn-porque").addEventListener("click", verPorque);
$("btn-nova").addEventListener("click", () => mostrarView("view-inicio"));
$("btn-regras").addEventListener("click", abrirDrawer);
$("btn-fechar-drawer").addEventListener("click", fecharDrawer);
$("overlay").addEventListener("click", fecharDrawer);
$("seletor-base").addEventListener("change", (e) => trocarBase(e.target.value));

// Início.
api("/api/llm")
  .then((d) => { llmDisponivel = !!d.disponivel; })
  .catch(() => { llmDisponivel = false; });
carregarEstadoBase().then(() => mostrarView("view-inicio"));
