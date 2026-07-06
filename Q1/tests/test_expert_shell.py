"""
testes.py
=========
Testes automatizados (regressão) da shell. Execute com:  python testes.py
Não depende de frameworks externos.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  # permite rodar de qualquer diretório
from expert_shell import (BaseConhecimento, AgenteEspecialista, ProvedorAutomatico,
                          parse_regra, combinar_cf)

BASE = os.path.join(ROOT, "bases", "suporte_tecnico.json")
falhas = 0

def checar(cond, msg):
    global falhas
    status = "OK  " if cond else "FALHA"
    if not cond:
        falhas += 1
    print(f"  [{status}] {msg}")

print("== 1. Parser de regras ==")
r = parse_regra("SE febre = alta E tosse = sim ENTAO suspeita = gripe CF 80", "R1")
checar(r.condicoes == [("febre", "alta"), ("tosse", "sim")], "condições parseadas")
checar(r.conclusao == ("suspeita", "gripe"), "conclusão parseada")
checar(r.cf == 80.0, "fator de confiança parseado")
r2 = parse_regra("SE temperatura = alta ENTÃO diagnostico = quente", "R2")  # com acento, sem CF
checar(r2.cf == 100.0 and r2.conclusao == ("diagnostico", "quente"), "ENTÃO acentuado e CF default")

print("== 2. Combinação de fatores de confiança (MYCIN) ==")
checar(abs(combinar_cf(85, 92) - 98.8) < 0.5, "dois positivos -> ~98.8")
checar(combinar_cf(100, 50) == 100.0, "saturação em 100")
checar(combinar_cf(-40, -40) < -40, "dois negativos reforçam negativo")

def consulta(respostas, modo):
    kb = BaseConhecimento.carregar(BASE)
    ag = AgenteEspecialista(kb, ProvedorAutomatico(respostas))
    res = ag.consultar(modo=modo)
    return ag, res

print("== 3. Diagnóstico correto nos três modos ==")
malware = {"liga":"sim","lentidao":"sim","popups":"sim","programas_desconhecidos":"sim",
           "tela":"normal","bipes":"nenhum","cheiro_queimado":"nao","reinicia":"nao",
           "temperatura":"normal","ventoinha":"normal","internet_neste_pc":"sim",
           "internet_outros":"sim","ruido_hd":"nao","erro_disco":"nao","bateria_dura":"nao",
           "e_notebook":"nao","poeira":"nao"}
for modo in ("backward", "forward", "hibrido"):
    ag, res = consulta(malware, modo)
    top = res["diagnostico"][0][0] if res["diagnostico"] else None
    checar(top == "malware", f"modo {modo}: diagnóstico = malware")

print("== 4. Encadeamento diagnóstico -> recomendação ==")
ag, res = consulta(malware, "backward")
checar(res["recomendacao"] and res["recomendacao"][0][0] == "antivirus_e_backup",
       "recomendação encadeada a partir do diagnóstico")

print("== 5. Backward pergunta menos que forward ==")
# fonte: backward deve precisar de poucas evidências
ag_b, _ = consulta({"liga":"nao","cheiro_queimado":"sim","bipes":"nenhum"}, "backward")
perguntas_backward = len(ag_b.motor.fatos_perguntados) + len(
    [v for v in ag_b.motor.avaliadas if ag_b.kb.is_perguntavel(v)])
checar(perguntas_backward < 17, f"backward usou {perguntas_backward} variáveis perguntáveis (< 17 totais)")

print("== 6. Explicação 'como' referencia regras reais ==")
ag, res = consulta(malware, "backward")
texto = ag.como("diagnostico", "malware")
checar("R8" in texto or "R9" in texto, "explicação cita regras que dispararam")

print("== 7. Explicação 'por que' usa a pilha de objetivos ==")
kb = BaseConhecimento.carregar(BASE)
ag = AgenteEspecialista(kb, ProvedorAutomatico({}))
# simula uma pilha
from expert_shell.inference_engine import ItemPilha
ag.motor.pilha.append(ItemPilha("R3", ("diagnostico","memoria_ram"), ("bipes","repetidos")))
pq = ag.por_que("bipes")
checar("memoria_ram" in pq and "R3" in pq, "por quê cita hipótese e regra")

print("== 8. Parada antecipada economiza perguntas ==")
class _Log(ProvedorAutomatico):
    def __init__(self, r): super().__init__(r); self.n = 0
    def obter(self, var, motor): self.n += 1; return super().obter(var, motor)
fonte = {"liga":"nao","cheiro_queimado":"sim","bipes":"nenhum"}
# com parada antecipada (default 85)
kb = BaseConhecimento.carregar(BASE); p1 = _Log(fonte)
AgenteEspecialista(kb, p1).consultar(modo="backward")
# exaustivo (limiar None)
kb = BaseConhecimento.carregar(BASE); p2 = _Log(fonte)
AgenteEspecialista(kb, p2).consultar(modo="backward", limiar_parada=None)
checar(p1.n < p2.n, f"early-stop perguntou {p1.n} < exaustivo {p2.n}")
checar(p1.n <= 3, f"early-stop fechou 'fonte' com {p1.n} perguntas (<= 3)")

print("== 9. Camada de IA (llm) — degradação graciosa ==")
from expert_shell import llm

# texto vazio nunca chama provedor
checar(llm.naturalizar("como", "")["fonte"] == "fallback", "texto vazio -> fallback")

# sem provedor ativo (força 'off') -> sempre fallback, texto preservado
os.environ["EXPERT_SHELL_LLM"] = "off"
r = llm.naturalizar("por_que", "explicação simbólica X")
checar(r["fonte"] == "fallback" and r["texto"] == "explicação simbólica X",
       "sem provedor -> fallback preserva o texto simbólico")
checar(llm.disponivel() is False, "disponivel() False com EXPERT_SHELL_LLM=off")

# provedor Ollama com HTTP mockado (não depende do Ollama real)
os.environ["EXPERT_SHELL_LLM"] = "ollama"
_orig_http = llm._http_json
llm._ollama_ok = True  # finge que o /api/tags respondeu
llm._cache.clear()
llm._http_json = lambda url, body=None, timeout=None: {
    "message": {"content": "Texto reescrito."}, "done_reason": "stop"}
checar(llm.naturalizar("como", "exp A")["fonte"] == "llm", "ollama OK -> fonte llm")

llm._cache.clear()
llm._http_json = lambda url, body=None, timeout=None: {
    "message": {"content": "cortado"}, "done_reason": "length"}
checar(llm.naturalizar("como", "exp B")["fonte"] == "fallback", "ollama truncado -> fallback")

llm._cache.clear()
def _boom(url, body=None, timeout=None): raise RuntimeError("rede caiu")
llm._http_json = _boom
r = llm.naturalizar("como", "exp C")
checar(r["fonte"] == "fallback" and r["texto"] == "exp C", "ollama erro -> fallback preserva texto")

# restaura estado para não afetar nada depois
llm._http_json = _orig_http
llm._cache.clear()
os.environ.pop("EXPERT_SHELL_LLM", None)

print("\n" + ("TODOS OS TESTES PASSARAM." if falhas == 0 else f"{falhas} TESTE(S) FALHARAM."))
sys.exit(1 if falhas else 0)
