"""
demo_automatica.py
==================
Demonstração NÃO-INTERATIVA da shell sobre a base de Suporte Técnico.
Roda vários cenários (respostas pré-definidas) nos três modos de inferência
e exibe diagnósticos ranqueados, recomendações e explicações 'Por quê?'/'Como?'.

Serve como demonstração e como teste de regressão.
"""
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  # permite rodar de qualquer diretório
from expert_shell import BaseConhecimento, AgenteEspecialista, ProvedorAutomatico

BASE = os.path.join(ROOT, "bases", "suporte_tecnico.json")

# Pausa entre cenários: ativa só num terminal real (bom para gravar o vídeo).
# Em execução automatizada (pipe/redirecionamento) ou com '--sem-pausa', segue direto.
PAUSAR = sys.stdin.isatty() and "--sem-pausa" not in sys.argv


def pausa():
    if PAUSAR:
        try:
            input("\n   [Enter para o próximo cenário] ")
        except (EOFError, KeyboardInterrupt):
            pass


# Provedor que conta quantas perguntas o motor fez (mostra a economia do backward).
class ProvedorContando(ProvedorAutomatico):
    def __init__(self, respostas):
        super().__init__(respostas)
        self.perguntas = 0

    def obter(self, variavel, motor):
        self.perguntas += 1
        return super().obter(variavel, motor)


# Rótulos amigáveis para apresentação
ROTULO = {
    "fonte_defeituosa": "Fonte de alimentação defeituosa",
    "memoria_ram": "Problema na memória RAM",
    "superaquecimento": "Superaquecimento",
    "malware": "Infecção por malware",
    "falha_disco": "Falha no disco (HD/SSD)",
    "problema_provedor": "Problema no provedor de internet",
    "rede_local": "Configuração de rede local",
    "bateria_degradada": "Bateria do notebook degradada",
    "trocar_fonte": "Substituir a fonte e verificar tomada/estabilizador.",
    "reassentar_testar_ram": "Reassentar os pentes de RAM e testá-los individualmente.",
    "limpar_e_pasta_termica": "Limpar a poeira, trocar pasta térmica e checar coolers.",
    "antivirus_e_backup": "Rodar antivírus atualizado, remover programas suspeitos, fazer backup.",
    "backup_e_trocar_disco": "Fazer backup imediato e substituir o disco.",
    "reiniciar_roteador_contatar_provedor": "Reiniciar o roteador e contatar o provedor.",
    "verificar_drivers_e_config_rede": "Verificar drivers de rede e configurações deste PC.",
    "substituir_bateria": "Substituir a bateria do notebook.",
}
rot = lambda x: ROTULO.get(x, x)


def mostrar_resultado(titulo, resultados, agente):
    print(f"\n{'='*70}\n{titulo}\n{'='*70}")
    diag = resultados.get("diagnostico", [])
    if diag:
        print("Diagnósticos (ordenados por confiança):")
        for val, cf in diag:
            print(f"   • {rot(val):42s}  CF = {cf:5.0f}")
        topo_val = diag[0][0]
        rec = resultados.get("recomendacao", [])
        if rec:
            print("Recomendações:")
            for val, cf in rec:
                print(f"   -> {rot(val)}  (CF={cf:.0f})")
        print(f"Regras disparadas: {agente.regras_disparadas()}")
        print("\n[COMO?] Explicação do diagnóstico principal:")
        for ln in agente.como("diagnostico", topo_val).splitlines():
            print("   " + ln)
    else:
        print("Nenhum diagnóstico pôde ser estabelecido com as evidências dadas.")


def cenario(nome, respostas, modo):
    kb = BaseConhecimento.carregar(BASE)
    prov = ProvedorContando(respostas)
    agente = AgenteEspecialista(kb, prov)
    resultados = agente.consultar(modo=modo)
    mostrar_resultado(f"{nome}  [modo: {modo}]", resultados, agente)
    print(f"Perguntas feitas ao usuário: {prov.perguntas}")
    pausa()
    return agente


# --------------------------- CENÁRIOS --------------------------- #
print("\n" + "#"*70)
print("# DEMONSTRAÇÃO — Shell de Sistema Baseado em Conhecimento")
print("# Domínio: Suporte Técnico de Computadores")
print("#"*70)

# Cenário 1: malware (backward) — só perguntas relevantes são usadas
cenario(
    "Cenário 1 — Lentidão + pop-ups + programas estranhos",
    {"liga": "sim", "tela": "normal", "bipes": "nenhum", "cheiro_queimado": "nao",
     "reinicia": "nao", "temperatura": "normal", "ventoinha": "normal",
     "lentidao": "sim", "popups": "sim", "programas_desconhecidos": "sim",
     "internet_neste_pc": "sim", "internet_outros": "sim", "ruido_hd": "nao",
     "erro_disco": "nao", "bateria_dura": "nao", "e_notebook": "nao", "poeira": "nao"},
    modo="backward",
)

# Cenário 2: superaquecimento (forward)
cenario(
    "Cenário 2 — Esquenta muito, reinicia sozinho, com poeira",
    {"liga": "sim", "tela": "normal", "bipes": "nenhum", "cheiro_queimado": "nao",
     "reinicia": "sim", "temperatura": "alta", "ventoinha": "alta",
     "lentidao": "nao", "popups": "nao", "programas_desconhecidos": "nao",
     "internet_neste_pc": "sim", "internet_outros": "sim", "ruido_hd": "nao",
     "erro_disco": "nao", "bateria_dura": "nao", "e_notebook": "nao", "poeira": "sim"},
    modo="forward",
)

# Cenário 3: falha de disco (híbrido) — combinação forte de evidências
cenario(
    "Cenário 3 — HD fazendo clique + erros de disco + lentidão",
    {"liga": "sim", "tela": "normal", "bipes": "nenhum", "cheiro_queimado": "nao",
     "reinicia": "nao", "temperatura": "normal", "ventoinha": "normal",
     "lentidao": "sim", "popups": "nao", "programas_desconhecidos": "nao",
     "internet_neste_pc": "sim", "internet_outros": "sim", "ruido_hd": "sim",
     "erro_disco": "sim", "bateria_dura": "nao", "e_notebook": "nao", "poeira": "nao"},
    modo="hibrido",
)

# Cenário 4: não liga + cheiro de queimado -> fonte (backward, poucas perguntas)
cenario(
    "Cenário 4 — Não liga e há cheiro de queimado",
    {"liga": "nao", "cheiro_queimado": "sim", "bipes": "nenhum"},
    modo="backward",
)

# Cenário 5: provedor de internet (backward)
cenario(
    "Cenário 5 — Sem internet no PC e em nenhum outro aparelho",
    {"liga": "sim", "internet_neste_pc": "nao", "internet_outros": "nao"},
    modo="backward",
)

# --------- Demonstração explícita de 'POR QUÊ?' durante a coleta --------- #
print("\n" + "="*70)
print("DEMONSTRAÇÃO DO 'POR QUÊ?' (justificativa de uma pergunta)")
print("="*70)


class ProvedorComPorque(ProvedorAutomatico):
    """Provedor que, antes de responder, imprime a explicação 'Por quê?'."""
    def __init__(self, respostas, agente_ref):
        super().__init__(respostas)
        self.agente_ref = agente_ref
        self.ja_explicou = False

    def obter(self, variavel, motor):
        # explica a primeira pergunta encadeada a uma hipótese
        if motor.pilha and not self.ja_explicou:
            print(f"\nPergunta sobre '{variavel}'. Usuário digita 'por que?':")
            for ln in self.agente_ref.explicador.por_que(variavel).splitlines():
                print("   " + ln)
            self.ja_explicou = True
        return super().obter(variavel, motor)


kb = BaseConhecimento.carregar(BASE)
respostas = {"liga": "sim", "tela": "preta", "bipes": "repetidos"}
agente = AgenteEspecialista.__new__(AgenteEspecialista)  # adiar p/ injetar provedor c/ ref
# construção manual para o provedor poder referenciar o agente:
from expert_shell.inference_engine import MotorInferencia
from expert_shell.explanation import Explicador
prov = ProvedorComPorque(respostas, None)
agente.kb = kb
agente.motor = MotorInferencia(kb, prov)
agente.explicador = Explicador(agente.motor)
prov.agente_ref = agente
res = agente.consultar(modo="backward")
mostrar_resultado("Cenário 6 — Tela preta + bipes repetidos (memória RAM)", res, agente)
