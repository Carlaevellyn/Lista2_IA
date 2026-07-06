import json
import streamlit as st
from collections import Counter

ARQUIVO = "casos.json"
ARQUIVO_HISTORICO = "historico.json"

SINTOMAS_DISPONIVEIS = [
    "febre",
    "tosse",
    "dor_muscular",
    "dor_cabeca",
    "falta_ar",
    "nausea",
    "coriza",
    "congestao_nasal",
    "azia",
    "dor_estomago",
    "dor_garganta",
    "espirros",
    "coceira_nariz",
    "dor_ouvido",
    "perda_audicao",
    "diarreia",
    "chiado_peito",
    "manchas_pele"
]


# =========================
# BANCO DE CASOS
# =========================

def carregar_casos():
    try:
        with open(
            ARQUIVO,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)

    except Exception:
        return []


def salvar_casos(casos):

    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            casos,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


# =========================
# CBR
# =========================

def calcular_similaridade(
    sintomas_usuario,
    caso
):

    pontos_obtidos = 0
    pontos_totais = 0

    pesos = caso.get(
        "pesos",
        {}
    )

    for sintoma in caso["sintomas"]:

        peso = pesos.get(
            sintoma,
            1
        )

        pontos_totais += peso

        if sintoma in sintomas_usuario:

            pontos_obtidos += peso

    if pontos_totais == 0:
        return 0

    return round(
        (
            pontos_obtidos /
            pontos_totais
        ) * 100,
        2
    )
def sintomas_em_comum(
    sintomas_usuario,
    sintomas_caso
):

    return list(
        set(sintomas_usuario)
        &
        set(sintomas_caso)
    )
def nivel_confianca(similaridade):

    if similaridade >= 80:
        return "🟢 Alta"

    elif similaridade >= 60:
        return "🟡 Média"

    else:
        return "🔴 Baixa"
def sintomas_diferentes(
    sintomas_usuario,
    sintomas_caso
):

    return list(
        set(sintomas_caso)
        -
        set(sintomas_usuario)
    )    
def recuperar_casos(
    sintomas_usuario,
    casos
):

    resultados = []

    for caso in casos:

        similaridade = calcular_similaridade(
            sintomas_usuario,
            caso
        )

        resultados.append(
            {
                "caso": caso,
                "similaridade": similaridade
            }
        )

    resultados.sort(
        key=lambda x: x["similaridade"],
        reverse=True
    )

    return resultados
def salvar_historico(registro):

    try:

        with open(
            ARQUIVO_HISTORICO,
            "r",
            encoding="utf-8"
        ) as f:

            historico = json.load(f)

    except:

        historico = []

    historico.append(
        registro
    )

    with open(
        ARQUIVO_HISTORICO,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            historico,
            f,
            ensure_ascii=False,
            indent=4
        )
def carregar_historico():

    try:

        with open(
            ARQUIVO_HISTORICO,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return []
# =========================
# CONFIGURAÇÃO STREAMLIT
# =========================

st.set_page_config(
    page_title="Sistema CBR Médico",
    page_icon="🩺",
    layout="centered"
)
casos = carregar_casos()

tab_consulta, tab_estatisticas = st.tabs(
    [
        "🩺 Consulta",
        "📊 Estatísticas"
    ]
)
with tab_consulta:

    st.title("🩺 Sistema CBR Médico")
    
    st.caption(
    "Case-Based Reasoning (CBR)"
)
    st.info(
    """
    🔄 Ciclo CBR utilizado:

    1️⃣ Retrieve → Recupera os casos mais parecidos

    2️⃣ Reuse → Sugere diagnóstico e tratamento

    3️⃣ Revise → Usuário valida ou corrige

    4️⃣ Retain → Novo caso é armazenado
    """
)
    casos = carregar_casos()

# =========================
# SESSION STATE
# =========================

    if "buscou" not in st.session_state:
        st.session_state.buscou = False

    if "resultados" not in st.session_state:
        st.session_state.resultados = []

    if "sintomas_usuario" not in st.session_state:
        st.session_state.sintomas_usuario = []
    
    if "historico_salvo" not in st.session_state:
        st.session_state.historico_salvo = False

# =========================
# SINTOMAS
# =========================

    st.subheader(
        "Selecione os sintomas"
)
    st.subheader(
    "Observações do paciente"
)

    observacoes = st.text_area(
    "Descreva informações adicionais"
)
    col1, col2 = st.columns(2)

    sintomas_usuario = []

    with col1:

        for sintoma in SINTOMAS_DISPONIVEIS[:9]:

            if st.checkbox(
                sintoma,
                key=f"cb_{sintoma}"
        ):
                sintomas_usuario.append(
                    sintoma
            )

    with col2:

        for sintoma in SINTOMAS_DISPONIVEIS[9:]:

            if st.checkbox(
                sintoma,
                key=f"cb_{sintoma}"
        ):
                sintomas_usuario.append(
                    sintoma
            )


# =========================
# BUSCA
# =========================

    if st.button(
        "🔍 Buscar Diagnóstico",
        use_container_width=True
    ):

        if len(sintomas_usuario) == 0:

            st.warning(
                "Selecione pelo menos um sintoma."
        )

        else:

            resultados = recuperar_casos(
                sintomas_usuario,
                casos
        )

            st.session_state.resultados = resultados
            st.session_state.sintomas_usuario = sintomas_usuario
            st.session_state.buscou = True


# =========================
# EXIBIÇÃO DOS RESULTADOS
# =========================

    if st.session_state.buscou:

        resultados = (
            st.session_state.resultados
    )
        resultados_filtrados = []
        diagnosticos_vistos = set()

        for resultado in resultados:

            diagnostico = resultado["caso"]["diagnostico"]

            if diagnostico not in diagnosticos_vistos:

                resultados_filtrados.append(
                    resultado
        )

                diagnosticos_vistos.add(
                    diagnostico
        )
        st.divider()

        st.header(
            "1️⃣ Retrieve (Recuperação)"
    )

        st.subheader(
            "🏆 Casos Mais Semelhantes"
    )
        with st.expander("📋 Ver todos os casos recuperados"
                         ):

            st.write(
                "Casos recuperados com base nos sintomas fornecidos."
        )

            st.write(
                f"Total de casos recuperados: "
                f"{len(resultados_filtrados)}"
        )
            dados = []

            for resultado in resultados_filtrados:

                dados.append({

                    "Diagnóstico":
                    resultado["caso"]["diagnostico"],

                    "Similaridade":
                    resultado["similaridade"]

                })

            st.dataframe(
                dados,
                use_container_width=True
            )

            st.caption(
                f"{len(resultados_filtrados)} casos encontrados"
        )

        for posicao, resultado in enumerate(
            resultados_filtrados[:3],
            start=1
            ):

            caso = resultado["caso"]

            coincidentes = sintomas_em_comum(
                st.session_state.sintomas_usuario,
                caso["sintomas"]
        )
            diferentes = sintomas_diferentes(
                st.session_state.sintomas_usuario,
                caso["sintomas"]
        )
            
            st.subheader(
                f"🏅 {posicao}º Lugar"
        )

            st.write(
                f"**Diagnóstico:** "
                f"{caso['diagnostico']}"
        )
            st.write(
                "✅ Sintomas coincidentes:"
        )

            st.success(
                ", ".join(coincidentes)
        )
            st.write(
                "❌ Sintomas não coincidentes:"
            )

            st.warning(
                ", ".join(diferentes)
            )
            st.progress(
                int(resultado["similaridade"])
        )

            st.write(
                f"Similaridade: "
                f"{resultado['similaridade']}%"
        )

            st.write(
                f"Sintomas do caso: "
                f"{', '.join(caso['sintomas'])}"
        )
            if "pesos" in caso:

                 with st.expander(
                "⚖️ Pesos dos sintomas:"
                ):

                    st.json(
                        caso["pesos"]
            )
            st.divider()

    # =====================
    # REUSE
    # =====================
        st.header(
            "2️⃣ Reuse (Reutilização)"
    )

        melhor_caso = resultados[0]["caso"]

        melhor_similaridade = resultados[0]["similaridade"]

    # Salva no histórico apenas uma vez
        if not st.session_state.historico_salvo:

            salvar_historico({

            "sintomas":
            st.session_state.sintomas_usuario,

            "observacoes":
            observacoes,

            "diagnostico":
            melhor_caso["diagnostico"],

            "similaridade":
            melhor_similaridade

    })

            st.session_state.historico_salvo = True


        confianca = nivel_confianca(
            melhor_similaridade
    )
        st.subheader(
        "Resultado da Análise"
    )

        
        st.progress(
            int(melhor_similaridade)
        )
        st.success(
            f"🩺 Diagnóstico sugerido: "
            f"{melhor_caso['diagnostico']}"
        )

        st.warning(
            f"💊 Tratamento sugerido: "
            f"{melhor_caso['tratamento']}"
        )
        st.info(
            f"Grau de confiança: {confianca} ({melhor_similaridade}%)"
    )
    # =====================
    # REVISE
    # =====================
        st.header(
            "3️⃣ Revise (Revisão)"
    )
        st.subheader(
            "Revise a solução"
    )
        if st.button(
            "✅ Aceitar Diagnóstico"
        ):
            salvar_historico({

                "sintomas":
                st.session_state.sintomas_usuario,

                "diagnostico":
                melhor_caso["diagnostico"],

                "similaridade":
                melhor_similaridade,

                "validado":
                True

            })

            st.success(
            "Diagnóstico validado."
    )
        ajudou = st.radio(
            "A solução foi útil?",
            ["Sim", "Não"]
    )

    # =====================
    # RETAIN
    # =====================

        if ajudou == "Não":

            st.header(
            "4️⃣ Retain (Retenção)"
        )
            st.subheader(
            "➕ Adicionar Novo Caso"
        )

            novo_diagnostico = st.text_input(
            "Diagnóstico correto"
        )

            novo_tratamento = st.text_area(
            "Tratamento correto"
        )

            if st.button(
                "💾 Salvar Novo Caso"
        ):

                if (
                    novo_diagnostico.strip()
                    and
                    novo_tratamento.strip()
            ):

                    novo_caso = {

                    "id":
                    len(casos) + 1,

                    "sintomas":
                    st.session_state.sintomas_usuario,

                    "diagnostico":
                    novo_diagnostico,

                    "tratamento":
                    novo_tratamento,

                    "pesos": {
                        sintoma: 2
                        for sintoma in st.session_state.sintomas_usuario
                    }
                }
                
            

                    casos.append(
                        novo_caso
                )

                    salvar_casos(
                        casos
                )

                    st.success(
                        "✅ Novo caso adicionado à base de conhecimento!"
                )

                else:

                    st.error(
                        "Preencha diagnóstico e tratamento."
                )

    # =====================
    # NOVA CONSULTA
    # =====================

        st.divider()

        if st.button(
            "🔄 Nova Consulta"
    ):

            st.session_state.buscou = False
            st.session_state.resultados = []
            st.session_state.sintomas_usuario = []
            st.session_state.historico_salvo = False

            st.rerun()

with tab_estatisticas:

    st.title("📊 Estatísticas do Sistema")

    historico = carregar_historico()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Casos cadastrados",
            len(casos)
        )

    with col2:

        st.metric(
            "Doenças cadastradas",
            len(
                set(
                    caso["diagnostico"]
                    for caso in casos
                )
            )
        )

    st.metric(
        "Consultas realizadas",
        len(historico)
    )

    if len(historico) > 0:

        media = sum(
            h["similaridade"]
            for h in historico
        ) / len(historico)

        st.metric(
            "Média de Similaridade",
            f"{media:.1f}%"
        )
    if len(historico) > 0:

        contador = Counter(
            h["diagnostico"]
            for h in historico
        )

        st.subheader(
        "Diagnósticos mais sugeridos"
    )

        for nome, qtd in contador.most_common(5):

            st.write(
                f"• {nome}: {qtd} consultas"
        )       
    if len(historico) > 0:

        st.subheader(
            "Histórico de Consultas"
        )

        for consulta in reversed(
            historico[-10:]
        ):

            st.write(
                f"""
                Diagnóstico: {consulta['diagnostico']}
                | Similaridade: {consulta['similaridade']}%
                """
        )        

    st.subheader(
    "📈 Distribuição dos Diagnósticos"
)

    dados_grafico = Counter(
        h["diagnostico"]
        for h in historico
)

    st.bar_chart(
        dados_grafico,
        horizontal=True
)