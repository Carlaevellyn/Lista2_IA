# Q3 — Agente de Revisão de Artigos (baseado em LLM)

**Sistema:** um **agente controlado por LLM** (via Ollama, local) que conversa em linguagem natural e usa um **revisor de artigos baseado em regras** como ferramenta.

A questão 3 pede uma aplicação envolvendo **agentes baseados em LLM**. Aqui o LLM é o agente: interpreta o pedido do usuário, **decide quando chamar as ferramentas**, integra os resultados e responde de forma conversacional. O **raciocínio de conformidade continua simbólico** — quem julga o artigo é o motor de regras (`revisor.py`); o LLM não inventa notas nem achados, apenas orquestra e explica.

## Componentes

| Arquivo | Papel |
|---|---|
| `agente.py` | O agente LLM (`AgenteRevisor`): loop de conversa, *tool calling* via Ollama. |
| `agente_app.py` | Interface de **chat** (Streamlit) — foco da questão. |
| `revisor.py` | Motor de regras que avalia o artigo (a **ferramenta** do agente). |
| `app.py` | Interface avulsa do revisor de regras, sem LLM. |

As ferramentas expostas ao agente são `revisar_artigo()` (roda o motor de regras sobre o artigo carregado) e `detalhar_dimensao(nome)` (recorta os achados de uma dimensão).

## Requisitos

* Python 3.11+
* Streamlit, PyPDF (`requirements.txt`)
* **Ollama** com um modelo que suporte *tool calling* (ex.: `llama3.2`) — **essencial para o agente**

## Como executar

```bash
python -m pip install -r requirements.txt

# pré-requisito do agente: Ollama instalado e aberto (https://ollama.com)
ollama pull llama3.2

# agente conversacional (LLM + ferramentas) — foco da questão 3
python -m streamlit run agente_app.py

# revisor de regras avulso (sem LLM)
python -m streamlit run app.py
```

> Sem o Ollama rodando, o agente exibe instruções de configuração. O revisor avulso (`app.py`) funciona sem LLM.

## Como o revisor (ferramenta) calcula o score

Cada dimensão começa em 100 e perde pontos por falha; a nota final passa por um **gate de gravidade**: achado grave de **integridade** (fraude, pseudociência, ausência declarada de método) é **eliminatório** (teto 25%); demais graves reduzem o teto (12 pontos por grave); sem graves, a média ponderada vale integralmente.

## Testes

```bash
python -m pip install pytest
python -m pytest
```

`testes/test_agente.py` trava o contrato entre o agente e o motor de regras; `testes/test_revisor.py`, o motor em si. (O loop de conversa com o LLM depende do Ollama e é coberto pela demonstração.)

> Relatório técnico completo em [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md) (versão em PDF: `RELATORIO_TECNICO.pdf`).
