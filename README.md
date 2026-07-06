# Lista de Exercícios de IA — Questões 1, 2 e 3

Repositório unificado com as três questões da lista. Cada questão fica em sua própria pasta, totalmente autocontida (código, base de conhecimento, testes e relatório técnico próprios).

## Integrantes

* Carla Evellyn
* Jhennifer Kyria
* Sthefany Barboza

## Os sistemas

| Pasta | Sistema | Técnica de IA | Relatório |
|-------|---------|---------------|-----------|
| [`Q1/`](Q1/) | **Expert Shell** — shell genérica para sistemas especialistas | Regras de produção · encadeamento forward/backward/híbrido · fatores de confiança (MYCIN) | [`Q1/docs/RELATORIO_TECNICO.md`](Q1/docs/RELATORIO_TECNICO.md) (+ PDF) |
| [`Q2/`](Q2/) | **Akinator Anime** (inferência) + **CBR Médico** (diagnóstico) | Busca em espaço de hipóteses · Case-Based Reasoning (Retrieve/Reuse/Revise/Retain) | [`Q2/relatorios/`](Q2/relatorios/) (2 PDFs) |
| [`Q3/`](Q3/) | **Agente de Revisão de Artigos** (baseado em LLM) | Agente LLM (Ollama) + *tool calling* · revisor de regras como ferramenta | [`Q3/RELATORIO_TECNICO.md`](Q3/RELATORIO_TECNICO.md) (+ PDF) |

Cada pasta tem seu próprio `README.md` com descrição completa, requisitos e instruções.

## Instalação única (todas as questões)

A partir da raiz do repositório, instale todas as dependências de uma vez:

```bash
python -m pip install -r requirements.txt
```

> Cada questão também tem seu `requirements.txt` próprio, caso queira instalar/rodar apenas uma isoladamente.

## Como executar cada sistema

```bash
# Q1 — Expert Shell (CLI, só biblioteca padrão)
cd Q1 && python main.py
#   interface web opcional: python run_web.py   (requer flask)

# Q2 — Akinator Anime
cd Q2/Akinator && streamlit run app.py

# Q2 — CBR Médico
cd Q2/CBR && streamlit run CBR.py

# Q3 — Agente de Revisão de Artigos (LLM via Ollama)
cd Q3 && streamlit run agente_app.py    # agente conversacional (requer Ollama)
#   revisor de regras avulso (sem LLM): streamlit run app.py
```

## Requisitos

Python 3.11+. Dependências por questão:

* **Q1:** biblioteca padrão (CLI); `flask` para a interface web; **Ollama** *opcional* (explicações em linguagem natural)
* **Q2:** `streamlit`
* **Q3:** `streamlit`, `pypdf`; **Ollama** *necessário* para o agente LLM (o revisor avulso roda sem ele)

> **Ollama não é um pacote pip** — é um aplicativo à parte ([ollama.com](https://ollama.com)). Instale-o e rode `ollama pull llama3.2` se for usar o agente da Q3 (ou a explicação natural opcional da Q1).
