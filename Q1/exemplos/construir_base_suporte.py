"""
construir_base_suporte.py
=========================
Constrói a base de conhecimento demonstrativa do domínio
"Suporte Técnico de Computadores" usando o EDITOR da shell e a salva em JSON.

Requisitos atendidos:
  - 27 regras (> 20 exigidas);
  - 17 variáveis perguntáveis com vários valores (> 30 fatos possíveis);
  - 8 diagnósticos distintos (> 5 hipóteses exigidas);
  - regras de recomendação associadas a cada diagnóstico.
"""
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  # permite rodar de qualquer diretório
from expert_shell import EditorBase

ed = EditorBase()
ed.kb.dominio = "Suporte Técnico de Computadores"

# ------------------------------------------------------------------ #
# 1) Variáveis PERGUNTÁVEIS (evidências)  -> cada par var=valor é um fato possível
# ------------------------------------------------------------------ #
V = ed.definir_variavel
V("liga",                  "O computador liga (acende luz/ventoinha)?",            ["sim", "nao"])
V("tela",                  "Como está a imagem na tela?",                          ["normal", "preta", "azul"])
V("bipes",                 "Há bipes (beeps) ao ligar?",                           ["nenhum", "repetidos", "longo"])
V("cheiro_queimado",       "Você sente cheiro de queimado vindo do gabinete?",     ["sim", "nao"])
V("reinicia",              "O computador reinicia ou desliga sozinho?",            ["sim", "nao"])
V("temperatura",           "O computador esquenta muito (fica quente ao toque)?",  ["alta", "normal"])
V("ventoinha",             "Como está o barulho da ventoinha (cooler)?",           ["alta", "normal", "parada"])
V("lentidao",              "O sistema está anormalmente lento?",                   ["sim", "nao"])
V("popups",                "Aparecem pop-ups/anúncios estranhos?",                 ["sim", "nao"])
V("programas_desconhecidos","Surgiram programas que você não instalou?",           ["sim", "nao"])
V("internet_neste_pc",     "A internet funciona NESTE computador?",                ["sim", "nao"])
V("internet_outros",       "A internet funciona em OUTROS aparelhos (celular/TV)?",["sim", "nao"])
V("ruido_hd",              "O HD/disco faz barulho de clique repetitivo?",         ["sim", "nao"])
V("erro_disco",            "Aparecem mensagens de erro de leitura/disco?",         ["sim", "nao"])
V("bateria_dura",          "A bateria do notebook descarrega muito rápido?",       ["sim", "nao"])
V("e_notebook",            "O equipamento é um notebook?",                         ["sim", "nao"])
V("poeira",                "Há muita poeira acumulada dentro do gabinete?",        ["sim", "nao"])

# ------------------------------------------------------------------ #
# 2) Regras de DIAGNÓSTICO  (variável-alvo: diagnostico)
# ------------------------------------------------------------------ #
R = ed.adicionar_regra_texto
R("SE liga = nao E cheiro_queimado = sim ENTAO diagnostico = fonte_defeituosa CF 95", "R1")
R("SE liga = nao E bipes = nenhum E cheiro_queimado = nao ENTAO diagnostico = fonte_defeituosa CF 60", "R2")
R("SE liga = sim E bipes = repetidos ENTAO diagnostico = memoria_ram CF 85", "R3")
R("SE liga = sim E tela = preta E bipes = repetidos ENTAO diagnostico = memoria_ram CF 92", "R4")
R("SE temperatura = alta E ventoinha = parada ENTAO diagnostico = superaquecimento CF 90", "R5")
R("SE temperatura = alta E poeira = sim ENTAO diagnostico = superaquecimento CF 80", "R6")
R("SE reinicia = sim E temperatura = alta ENTAO diagnostico = superaquecimento CF 75", "R7")
R("SE lentidao = sim E popups = sim ENTAO diagnostico = malware CF 85", "R8")
R("SE popups = sim E programas_desconhecidos = sim ENTAO diagnostico = malware CF 90", "R9")
R("SE lentidao = sim E programas_desconhecidos = sim ENTAO diagnostico = malware CF 70", "R10")
R("SE ruido_hd = sim ENTAO diagnostico = falha_disco CF 80", "R11")
R("SE erro_disco = sim E lentidao = sim ENTAO diagnostico = falha_disco CF 75", "R12")
R("SE ruido_hd = sim E erro_disco = sim ENTAO diagnostico = falha_disco CF 95", "R13")
R("SE tela = azul E erro_disco = sim ENTAO diagnostico = falha_disco CF 70", "R14")
R("SE internet_neste_pc = nao E internet_outros = nao ENTAO diagnostico = problema_provedor CF 90", "R15")
R("SE internet_neste_pc = nao E internet_outros = sim ENTAO diagnostico = rede_local CF 85", "R16")
R("SE e_notebook = sim E bateria_dura = sim ENTAO diagnostico = bateria_degradada CF 85", "R17")
R("SE tela = azul E temperatura = alta ENTAO diagnostico = superaquecimento CF 60", "R18")
R("SE reinicia = sim E temperatura = normal E lentidao = sim ENTAO diagnostico = malware CF 55", "R19")

# ------------------------------------------------------------------ #
# 3) Regras de RECOMENDAÇÃO  (variável-alvo: recomendacao; encadeiam a partir de diagnostico)
# ------------------------------------------------------------------ #
R("SE diagnostico = fonte_defeituosa ENTAO recomendacao = trocar_fonte CF 100", "R20")
R("SE diagnostico = memoria_ram ENTAO recomendacao = reassentar_testar_ram CF 100", "R21")
R("SE diagnostico = superaquecimento ENTAO recomendacao = limpar_e_pasta_termica CF 100", "R22")
R("SE diagnostico = malware ENTAO recomendacao = antivirus_e_backup CF 100", "R23")
R("SE diagnostico = falha_disco ENTAO recomendacao = backup_e_trocar_disco CF 100", "R24")
R("SE diagnostico = problema_provedor ENTAO recomendacao = reiniciar_roteador_contatar_provedor CF 100", "R25")
R("SE diagnostico = rede_local ENTAO recomendacao = verificar_drivers_e_config_rede CF 100", "R26")
R("SE diagnostico = bateria_degradada ENTAO recomendacao = substituir_bateria CF 100", "R27")

# ------------------------------------------------------------------ #
# 4) Objetivos (hipóteses que o motor tenta resolver, nesta ordem)
# ------------------------------------------------------------------ #
ed.definir_objetivos(["diagnostico", "recomendacao"])

# Texto amigável das recomendações (armazenado como pergunta da variável de valor)
# -> usamos um dicionário separado para apresentação no relatório/CLI:
ed.kb.variaveis["recomendacao"].pergunta = "Recomendação de ação"
ed.kb.variaveis["diagnostico"].pergunta = "Diagnóstico provável"

destino = os.path.join(ROOT, "bases", "suporte_tecnico.json")
ed.salvar(destino)
print(f"Base salva em: {destino}")
print(f"Variáveis: {len(ed.kb.variaveis)} | Regras: {len(ed.kb.regras)} | Objetivos: {ed.kb.objetivos}")
diags = sorted({r.valor_conclusao for r in ed.kb.regras.values() if r.variavel_conclusao == 'diagnostico'})
print(f"Diagnósticos distintos ({len(diags)}): {diags}")
