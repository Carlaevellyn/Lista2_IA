# Q1 — Expert Shell (Shell para Sistemas Baseados em Conhecimento)

Shell **genérica** para construir sistemas especialistas de **diagnóstico e
recomendação**, nos moldes do *Expert SINTA*. O conhecimento é declarativo: troca-se de
domínio trocando o arquivo da base — **sem alterar o código**.

> Disciplina de Inteligência Artificial (2026.1) — Lista 1 (AB2), Questão 1.
> Aplicação demonstrativa: **Suporte Técnico de Computadores**.

## Principais recursos
- Editor da base (fatos e regras `SE … E … ENTÃO …`) com persistência em JSON.
- Motor de inferência: **forward**, **backward** e **híbrido**.
- **Fatores de confiança** (estilo MYCIN) e **parada antecipada** no backward.
- Mecanismo de explicação **"Por quê?"** e **"Como?"**.
- Interface de linha de comando (consulta + edição da base).

## Requisitos
Python 3.8 ou superior. **Sem dependências externas** (apenas biblioteca padrão).

## Como executar

Rode a partir da **raiz do projeto**.

**Uso normal (consulta interativa de diagnóstico):**
```bash
python main.py
# equivalente: python -m expert_shell.cli bases/suporte_tecnico.json
```

**Interface web (consulta + visualização da base):**
```bash
pip install -r requirements.txt   # 1ª vez (instala Flask)
python run_web.py                 # abre em http://127.0.0.1:5000
```
Escolha a estratégia (backward/forward/híbrida), responda clicando nos valores,
use *Não sei* / *Por quê?* e veja o ranking de diagnósticos com a confiança (CF).
O motor de inferência é o mesmo da CLI — a web é só uma nova interface.

**Extensão opcional (IA generativa, local e gratuita)**

Na web, as explicações Por quê?/Como? ganham um botão *"🤖 Tornar natural (IA)"*
que reescreve o texto em linguagem fluida usando um modelo de linguagem **local
via [Ollama](https://ollama.com)** (grátis, offline, sem chave de API). O
**raciocínio continua 100% no motor de regras** — o LLM apenas reformula a
explicação já gerada. Sem o Ollama, a shell funciona normalmente e o botão nem
aparece.

```bash
# 1. instale o Ollama (https://ollama.com) e baixe um modelo:
ollama pull llama3.2
# 2. com o Ollama rodando, suba a shell (nesta ordem):
python run_web.py
```

Não precisa de pacote pip. Variáveis de ambiente opcionais: `OLLAMA_MODEL`
(padrão `llama3.2`), `OLLAMA_HOST` (padrão `http://localhost:11434`) e
`EXPERT_SHELL_LLM=off` para desativar o recurso.

> Ao clicar no botão, **o texto da explicação (com IDs de regra e fatos da base)
> é enviado ao Ollama** — que roda na sua própria máquina, então nada sai do seu
> computador.
No menu: escolha `2` (Realizar consulta) → selecione a estratégia → responda às
perguntas digitando o valor pedido, ou `por que?` para ver a justificativa, ou
`nao sei`. Ao final aparece o diagnóstico e a recomendação; digite, por exemplo,
`diagnostico=malware` para ver o **como?**. A opção `1` abre o **editor da base**.

**Exemplos não-interativos (opcionais):**
```bash
python exemplos/demo_automatica.py        # 6 cenários nos 3 modos, com explicações
python exemplos/demo_reuso.py             # a mesma shell em outro domínio (pragas agrícolas)
python exemplos/construir_base_suporte.py # regenera bases/suporte_tecnico.json
```

**Testes:**
```bash
python tests/test_expert_shell.py
```

## Usando como biblioteca
```python
from expert_shell import BaseConhecimento, AgenteEspecialista, ProvedorCLI

kb = BaseConhecimento.carregar("bases/suporte_tecnico.json")
agente = AgenteEspecialista(kb, ProvedorCLI(kb))
resultado = agente.consultar(modo="backward")   # "forward" | "hibrido"
print(resultado["diagnostico"])                  # [(valor, CF), ...] ordenado
```

## Estrutura do projeto
```
.
├── main.py                     # ponto de entrada (abre a CLI)
├── expert_shell/               # a SHELL (genérica, sem regras de domínio)
│   ├── knowledge_base.py       #   representação do conhecimento + persistência
│   ├── parser.py               #   SE...ENTAO  <->  Regra
│   ├── inference_engine.py     #   forward / backward / híbrido + CF + justificativas
│   ├── explanation.py          #   "Por quê?" e "Como?"
│   ├── kb_editor.py            #   editor da base
│   ├── shell.py                #   agente + provedores de evidência
│   └── cli.py                  #   interface de linha de comando
├── bases/                      # bases de conhecimento (declarativas, em JSON)
│   ├── suporte_tecnico.json    #   27 regras, 8 diagnósticos
│   └── pragas_agricolas.json   #   2ª base (demonstra reutilização)
├── exemplos/                   # scripts de demonstração (não são a aplicação)
├── tests/                      # testes automatizados
└── docs/                       # documentação
    ├── RELATORIO_TECNICO.md    #   relatório técnico completo
    └── diagrama_arquitetura.svg
```

## Documentação
O **relatório técnico completo** (arquitetura, representação do conhecimento, estratégias
de inferência, mecanismo de explicação, exemplos de consultas, limitações e melhorias)
está em [`docs/RELATORIO_TECNICO.md`](docs/RELATORIO_TECNICO.md).
