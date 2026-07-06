"""
Testes das FERRAMENTAS do agente (a parte que não depende do Ollama).

Travam o contrato entre o agente e o motor de regras: a tool `revisar_artigo`
devolve o parecer real e `detalhar_dimensao` recorta uma dimensão. A ida ao LLM
(loop de conversa) depende de um servidor Ollama e fica coberta pela demonstração.

Rode a partir da raiz do projeto (Q3):  python -m pytest
"""
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from agente import AgenteRevisor, _sem_acento  # noqa: E402

TEXTO_PROBLEMATICO = """Este artigo prova com certeza absoluta que uma geladeira quantica cura diabetes por wi-fi.
Nao utilizamos metodologia.
A amostra foi de 3 alunos.
Inventamos os dados para comprovar definitivamente o resultado.
A Wikipedia foi a principal fonte."""


def test_tool_revisar_artigo_retorna_parecer_do_motor():
    ag = AgenteRevisor(TEXTO_PROBLEMATICO)
    r = ag._tool_revisar_artigo()
    # a tool reflete o motor de regras: fraude é eliminatória
    assert r["pontuacao"] <= 25, r["pontuacao"]
    assert r["decisao"] == "Não recomendado na forma atual"
    assert r["achados_graves"], "deveria haver achados graves"
    assert any(d["nome"] for d in r["dimensoes"])


def test_tool_detalhar_dimensao_recorta_uma_dimensao():
    ag = AgenteRevisor(TEXTO_PROBLEMATICO)
    ag._tool_revisar_artigo()
    r = ag._tool_detalhar_dimensao("ética")
    assert "Ética" in r["dimensao"]
    assert isinstance(r["achados"], list)


def test_detalhar_dimensao_inexistente_lista_disponiveis():
    ag = AgenteRevisor(TEXTO_PROBLEMATICO)
    r = ag._tool_detalhar_dimensao("inexistente")
    assert "erro" in r
    assert isinstance(r["dimensoes"], list) and r["dimensoes"]


def test_executar_tool_desconhecida():
    ag = AgenteRevisor(TEXTO_PROBLEMATICO)
    assert "erro" in ag._executar_tool("nao_existe", {})


def test_artigo_vazio():
    ag = AgenteRevisor("")
    assert "erro" in ag._tool_revisar_artigo()


@pytest.mark.parametrize("termo,fragmento_esperado", [
    ("metodologia", "metodolog"),   # -> "Rigor metodológico"
    ("referencias", "referencial"),  # -> "Referencial teórico e citações"
    ("evidencias", "evid"),          # -> "Evidências e resultados"
    ("etica", "tica"),               # -> "Ética e integridade científica"
])
def test_detalhar_dimensao_aceita_termos_naturais_sem_acento(termo, fragmento_esperado):
    ag = AgenteRevisor(TEXTO_PROBLEMATICO)
    ag._tool_revisar_artigo()
    r = ag._tool_detalhar_dimensao(termo)
    assert "dimensao" in r, r
    assert fragmento_esperado in _sem_acento(r["dimensao"])
