"""
demo_reuso.py
=============
Prova de REUTILIZAÇÃO: a MESMA shell, sem qualquer alteração de código, é
aplicada a um SEGUNDO domínio (diagnóstico de pragas agrícolas e recomendação
de tratamento). Basta definir outra base de conhecimento.
"""
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  # permite rodar de qualquer diretório
from expert_shell import EditorBase, BaseConhecimento, AgenteEspecialista, ProvedorAutomatico

PRAGAS = os.path.join(ROOT, "bases", "pragas_agricolas.json")

# ---- especialista define uma base totalmente diferente, só com texto ---- #
ed = EditorBase()
ed.kb.dominio = "Diagnóstico de Pragas Agrícolas (tomate)"
ed.definir_variavel("folhas",       "Como estão as folhas?",                ["amareladas", "manchas_escuras", "buracos", "normais"])
ed.definir_variavel("teias",        "Há teias finas sob as folhas?",        ["sim", "nao"])
ed.definir_variavel("insetos_verdes","Vê pequenos insetos verdes nos brotos?",["sim", "nao"])
ed.definir_variavel("frutos",       "Como estão os frutos?",                ["podres", "furados", "normais"])
ed.definir_variavel("umidade",      "A umidade do ambiente está alta?",     ["sim", "nao"])

ed.adicionar_regra_texto("SE teias = sim E folhas = amareladas ENTAO praga = acaro CF 90", "R1")
ed.adicionar_regra_texto("SE insetos_verdes = sim ENTAO praga = pulgao CF 88", "R2")
ed.adicionar_regra_texto("SE folhas = manchas_escuras E umidade = sim ENTAO praga = fungo_requeima CF 85", "R3")
ed.adicionar_regra_texto("SE frutos = furados E folhas = buracos ENTAO praga = lagarta CF 90", "R4")
ed.adicionar_regra_texto("SE frutos = podres E umidade = sim ENTAO praga = fungo_requeima CF 70", "R5")
ed.adicionar_regra_texto("SE praga = acaro ENTAO tratamento = acaricida_e_aumentar_umidade CF 100", "R6")
ed.adicionar_regra_texto("SE praga = pulgao ENTAO tratamento = oleo_de_neem_ou_inseticida CF 100", "R7")
ed.adicionar_regra_texto("SE praga = fungo_requeima ENTAO tratamento = fungicida_e_reduzir_umidade CF 100", "R8")
ed.adicionar_regra_texto("SE praga = lagarta ENTAO tratamento = bacillus_thuringiensis CF 100", "R9")
ed.definir_objetivos(["praga", "tratamento"])

ed.salvar(PRAGAS)
print(f"Segunda base criada: {ed.kb.dominio} ({len(ed.kb.regras)} regras)\n")

# ---- a mesma shell consulta esse novo domínio ---- #
kb = BaseConhecimento.carregar(PRAGAS)
agente = AgenteEspecialista(kb, ProvedorAutomatico(
    {"folhas": "manchas_escuras", "umidade": "sim", "teias": "nao",
     "insetos_verdes": "nao", "frutos": "podres"}))
res = agente.consultar(modo="hibrido")
print("Consulta (mesma shell, novo domínio):")
for obj, rk in res.items():
    for val, cf in rk:
        print(f"   {obj}: {val}  (CF={cf:.0f})")
print(f"\nRegras disparadas: {agente.regras_disparadas()}")
print("\n[COMO?]")
if res["praga"]:
    print(agente.como("praga", res["praga"][0][0]))
