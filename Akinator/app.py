import json
import streamlit as st

# =====================================================
# ARQUIVOS
# =====================================================

ARQUIVO_PERSONAGENS = "personagens.json"
ARQUIVO_TESTES = "testes.json"

# =====================================================
# PERGUNTAS
# =====================================================

PERGUNTAS = {
    "humano": "O personagem é humano?",
    "poder": "Possui poderes especiais?",
    "pirata": "É pirata?",
    "ninja": "É ninja?",
    "estudante": "É estudante?",
    "protagonista": "É protagonista?",
    "espada": "Usa espada?",
    "vilao": "É vilão?",
    "masculino": "É masculino?",
    "alien": "É alienígena?",
    "professor": "É professor?",
    "detetive": "É detetive?",
    "guerreiro": "É guerreiro?",
    "magico": "Utiliza magia?",
    "anime_moderno": "É de anime recente?",
    "crianca": "É criança ou adolescente?",
    "cacador": "É um caçador?",
    "transformacao": "Possui transformação marcante?",
    "olhos_especiais": "Possui olhos especiais?",
    "anti_heroi": "É um anti-herói?"
}
# =====================================================
# PERSONAGENS
# =====================================================

def carregar_personagens():

    try:

        with open(
            ARQUIVO_PERSONAGENS,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return []


def salvar_personagens(personagens):

    with open(
        ARQUIVO_PERSONAGENS,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            personagens,
            f,
            ensure_ascii=False,
            indent=4
        )


# =====================================================
# TESTES
# =====================================================

def carregar_testes():

    try:

        with open(
            ARQUIVO_TESTES,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return []


def salvar_testes(testes):

    with open(
        ARQUIVO_TESTES,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            testes,
            f,
            ensure_ascii=False,
            indent=4
        )
# =====================================================
# TESTE AUTOMÁTICO

def executar_teste(personagem):

    candidatos = carregar_personagens()
    respostas = {}
    perguntas_feitas = []
    personagem_chutado = None

    while True:

        if len(candidatos) == 0:
            break

        if len(candidatos) == 1:
            personagem_chutado = candidatos[0]
            break

        atributo = melhor_pergunta(
            candidatos,
            perguntas_feitas
        )

        if atributo is None:

            ranking = ranking_candidatos(
                candidatos,
                respostas
            )

            if ranking:
                personagem_chutado = ranking[0][1]

            break

        resposta = personagem.get(
            atributo,
            "?"
        )

        respostas[atributo] = resposta
        perguntas_feitas.append(atributo)
        candidatos = filtrar_candidatos(
            candidatos,
            atributo,
            resposta
        )

    if personagem_chutado is None:
        return {
            "resultado": "falha",
            "personagem_pensado": personagem["nome"],
            "personagem_chutado": "desconhecido",
            "quantidade_perguntas": len(perguntas_feitas)
        }

    resultado = (
        "acerto"
        if personagem_chutado["nome"] == personagem["nome"]
        else "falha"
    )

    return {
        "resultado": resultado,
        "personagem_pensado": personagem["nome"],
        "personagem_chutado": personagem_chutado["nome"],
        "quantidade_perguntas": len(perguntas_feitas)
    }
# =====================================================
# ELIMINAÇÃO DE HIPÓTESES
# =====================================================

def filtrar_candidatos(

    candidatos,
    atributo,
    resposta

):

    if resposta == "?":

        return candidatos.copy()

    filtrados = []

    for personagem in candidatos:

        valor = personagem.get(
            atributo,
            "?"
        )

        if valor == resposta:

            filtrados.append(
                personagem
            )

    return filtrados
# =====================================================
# CÁLCULO DA HIPÓTESE MAIS PROVÁVEL
# =====================================================

def calcular_pontuacao(personagem, respostas):

    pontos = 0

    for atributo, resposta_usuario in respostas.items():

        if resposta_usuario == "?":
            continue

        resposta_personagem = personagem.get(atributo, "?")

        if resposta_personagem == resposta_usuario:
            pontos += 1

    return pontos

# =====================================================
# RANKING DAS HIPÓTESES
# =====================================================

def ranking_candidatos(candidatos, respostas):

    ranking = []

    for personagem in candidatos:

        pontos = calcular_pontuacao(

            personagem,

            respostas

        )

        ranking.append((pontos, personagem))

    ranking.sort(

        reverse=True,

        key=lambda x: x[0]

    )

    return ranking
# =====================================================
# MELHOR PERGUNTA
# =====================================================

def melhor_pergunta(

    candidatos,
    perguntas_feitas

):

    melhor = None

    menor_diferenca = float("inf")

    for atributo in PERGUNTAS:

        if atributo in perguntas_feitas:

            continue

        sim = 0
        nao = 0

        for personagem in candidatos:

            valor = personagem.get(
                atributo,
                "?"
            )

            if valor == "s":

                sim += 1

            elif valor == "n":

                nao += 1

        if sim == 0 or nao == 0:

            continue

        diferenca = abs(
            sim - nao
        )

        if diferenca < menor_diferenca:

            menor_diferenca = diferenca

            melhor = atributo

    return melhor
# =====================================================
# APRENDIZADO
# =====================================================

def adicionar_personagem(

    nome,
    anime,
    respostas

):

    personagens = carregar_personagens()

    novo = {

        "nome": nome,

        "anime": anime

    }

    for atributo in PERGUNTAS:

        novo[atributo] = respostas.get(
            atributo,
            "?"
        )

    personagens.append(
        novo
    )

    salvar_personagens(
        personagens
    )
# =====================================================
# LOG DE TESTES
# =====================================================

def registrar_teste(

    resultado,
    pensado,
    chutado,
    perguntas

):

    testes = carregar_testes()

    testes.append({

        "resultado": resultado,

        "personagem_pensado": pensado,

        "personagem_chutado": chutado,

        "quantidade_perguntas": perguntas

    })

    salvar_testes(
        testes
    )
# =====================================================
# STREAMLIT
# =====================================================

st.set_page_config(

    page_title="Akinator Anime",

    page_icon="🎭",

    layout="centered"

)

personagens = carregar_personagens()

# =====================================================
# SESSION
# =====================================================

if "candidatos" not in st.session_state:

    st.session_state.candidatos = personagens.copy()

if "perguntas_feitas" not in st.session_state:

    st.session_state.perguntas_feitas = []

if "respostas" not in st.session_state:

    st.session_state.respostas = {}

if "modo_aprendizado" not in st.session_state:

    st.session_state.modo_aprendizado = False

if "personagem_chutado" not in st.session_state:

    st.session_state.personagem_chutado = None

if "jogo_finalizado" not in st.session_state:

    st.session_state.jogo_finalizado = False

if "estado" not in st.session_state:

    st.session_state.estado = "perguntas"

if "mostrar_formulario" not in st.session_state:

    st.session_state.mostrar_formulario = False
# =====================================================
# RESET
# =====================================================

def reiniciar():

    personagens = carregar_personagens()

    st.session_state.candidatos = personagens.copy()
    st.session_state.perguntas_feitas = []
    st.session_state.respostas = {}
    st.session_state.modo_aprendizado = False
    st.session_state.personagem_chutado = None
    st.session_state.jogo_finalizado = False
    st.session_state.mostrar_formulario = False


# =====================================================
# TABS
# =====================================================

tab_jogo, tab_testes = st.tabs(
    [
        "🎮 Jogo",
        "📊 Testes"
    ]
)

# =====================================================
# INTERFACE DO JOGO
# =====================================================

with tab_jogo:

    st.title("🎭 Akinator Anime")

    st.caption(
        "Pense em um personagem de anime e responda às perguntas."
    )

    st.info(
        "Considere a versão pela qual o personagem é mais conhecido."
    )

    personagens = carregar_personagens()

    animes = sorted(
        set(
            p.get("anime", "")
            for p in personagens
            if p.get("anime")
        )
    )

    with st.expander("📚 Animes cadastrados"):

        st.write(" • ".join(animes))

    progresso = (
        len(st.session_state.perguntas_feitas)
        / len(PERGUNTAS)
    )

    st.progress(min(progresso, 1.0))

    # =================================================
    # SEM CANDIDATOS
    # =================================================

    if len(st.session_state.candidatos) == 0:

        st.error("Não consegui identificar o personagem.")

        st.session_state.modo_aprendizado = True

    # =================================================
    # SE RESTOU APENAS UM
    # =================================================

    if (
        len(st.session_state.candidatos) == 1
        and
        st.session_state.personagem_chutado is None
    ):

        st.session_state.personagem_chutado = (
            st.session_state.candidatos[0]
        )

    # =================================================
    # PERGUNTAS
    # =================================================

    if (
        st.session_state.personagem_chutado is None
        and
        not st.session_state.modo_aprendizado
    ):

        atributo = melhor_pergunta(

            st.session_state.candidatos,

            st.session_state.perguntas_feitas

        )

        if atributo is None:

            ranking = ranking_candidatos(
                st.session_state.candidatos,
                st.session_state.respostas
            )

            if ranking:

                maior = ranking[0][0]

                empatados = sum(
                    1 for pontos, _ in ranking
                    if pontos == maior
                )

                if empatados == len(ranking):

                    st.session_state.modo_aprendizado = True

                else:

                    st.session_state.personagem_chutado = ranking[0][1]

                st.rerun()

        else:

            st.markdown("---")

            st.subheader(
                PERGUNTAS[atributo]
            )

            st.markdown("---")

            col1, col2, col3 = st.columns(3)

            with col1:

                if st.button(
                    "✅ Sim",
                    use_container_width=True
                ):

                    st.session_state.respostas[
                        atributo
                    ] = "s"

                    st.session_state.candidatos = (
                        filtrar_candidatos(
                            st.session_state.candidatos,
                            atributo,
                            "s"
                        )
                    )

                    st.session_state.perguntas_feitas.append(
                        atributo
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "❌ Não",
                    use_container_width=True
                ):

                    st.session_state.respostas[
                        atributo
                    ] = "n"

                    st.session_state.candidatos = (
                        filtrar_candidatos(
                            st.session_state.candidatos,
                            atributo,
                            "n"
                        )
                    )

                    st.session_state.perguntas_feitas.append(
                        atributo
                    )

                    st.rerun()

            with col3:

                if st.button(
                    "🤔 Não sei",
                    use_container_width=True
                ):

                    st.session_state.respostas[
                        atributo
                    ] = "?"

                    st.session_state.perguntas_feitas.append(
                        atributo
                    )

                    st.rerun()

    # =================================================
    # HIPÓTESES
    # =================================================

    if (
        st.session_state.personagem_chutado is None
        and
        len(st.session_state.candidatos) > 1
    ):

        ranking = ranking_candidatos(

            st.session_state.candidatos,

            st.session_state.respostas

        )

        with st.expander("🔍 Ver hipóteses atuais"):

            st.write(
                f"**Hipótese mais provável:** {ranking[0][1]['nome']}"
            )

            st.write(
                f"**Hipóteses restantes:** {len(ranking)}"
            )

            st.divider()

            for posicao, (pontos, personagem) in enumerate(
                ranking[:5],
                start=1
            ):

                st.write(
                    f"{posicao}. {personagem['nome']} — {pontos} pontos"
                )

            if (
                len(ranking) > 1
                and
                ranking[0][0] == ranking[1][0]
            ):

                st.warning(
                    "Ainda existem várias hipóteses com a mesma pontuação."
                )
     # =================================================
    # MOMENTO DO CHUTE
    # =================================================

    if st.session_state.personagem_chutado is not None:

        personagem = st.session_state.personagem_chutado

        st.success("🎉 Acho que descobri!")

        st.markdown(f"# {personagem['nome']}")

        st.markdown(
            f"### 📺 {personagem.get('anime', 'Anime não informado')}"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "✅ Acertei",
                use_container_width=True
            ):

                registrar_teste(

                    "acerto",

                    personagem["nome"],

                    personagem["nome"],

                    len(
                        st.session_state.perguntas_feitas
                    )

                )

                st.session_state.jogo_finalizado = True

                st.rerun()

        with col2:

            if st.button(
                "❌ Errou",
                use_container_width=True
            ):

                registrar_teste(

                    "falha",

                    "desconhecido",

                    personagem["nome"],

                    len(
                        st.session_state.perguntas_feitas
                    )

                )

                st.session_state.modo_aprendizado = True

                st.rerun()

    # =================================================
    # APRENDIZADO
    # =================================================

    if st.session_state.modo_aprendizado:

        st.warning(
        "Não consegui identificar o personagem com as informações fornecidas."
    )

        st.info(
        "Você pode iniciar uma nova partida ou ensinar um novo personagem para ampliar a base de conhecimento."
    )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
            "🔄 Jogar novamente",
            use_container_width=True
        ):

                reiniciar()
                st.rerun()

        with col2:

            if st.button(
            "📖 Ensinar personagem",
            use_container_width=True
        ):

                st.session_state.mostrar_formulario = True
                st.rerun()

        if st.session_state.mostrar_formulario:

            st.divider()

            st.subheader("📖 Novo personagem")

            nome = st.text_input("Nome")

            anime = st.text_input("Anime")

            respostas = {}

            for atributo, pergunta in PERGUNTAS.items():

                respostas[atributo] = st.selectbox(

                pergunta,

                ["?", "s", "n"],

                key=f"novo_{atributo}"

            )

            if st.button(
                "Salvar Personagem",
                use_container_width=True
            ):

                adicionar_personagem(
                    nome,
                    anime,
                    respostas
            )

                st.success(
                "Novo personagem aprendido com sucesso!"
            )

                reiniciar()

                st.rerun()

    # =================================================
    # FIM DA PARTIDA
    # =================================================

    if st.session_state.jogo_finalizado:

        st.divider()

        st.success("🏁 Partida encerrada.")

        if st.button(

            "🔄 Jogar novamente",

            use_container_width=True

        ):

            reiniciar()

            st.rerun()
# =====================================================
# ABA TESTES
# =====================================================

with tab_testes:

    st.title("📊 Avaliação do Sistema")

    st.write(
        """
        Esta aba executa testes automáticos utilizando
        todos os personagens cadastrados na base de conhecimento.
        """
    )

    if st.button(
        "▶ Executar Testes",
        use_container_width=True
    ):

        personagens = carregar_personagens()

        resultados = []

        barra = st.progress(0)

        for i, personagem in enumerate(personagens):

            resultado = executar_teste(personagem)

            resultados.append(resultado)

            barra.progress(
                (i + 1) / len(personagens)
            )

        salvar_testes(resultados)

        st.success(
            "Testes concluídos!"
        )

    testes = carregar_testes()

    if len(testes) > 0:

        total = len(testes)

        acertos = sum(

            1

            for t in testes

            if t["resultado"] == "acerto"

        )

        falhas = total - acertos

        media = sum(

            t["quantidade_perguntas"]

            for t in testes

        ) / total

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(

                "Taxa de acerto",

                f"{100*acertos/total:.1f}%"

            )

        with col2:

            st.metric(

                "Falhas",

                falhas

            )

        with col3:

            st.metric(

                "Perguntas médias",

                f"{media:.1f}"

            )

        st.divider()

        st.subheader("Histórico")

        for teste in testes:

            emoji = "✅"

            if teste["resultado"] == "falha":

                emoji = "❌"

            st.write(

                f"""{emoji}
                **Pensado:** {teste['personagem_pensado']}
                |
                **Chutado:** {teste['personagem_chutado']}
                |
                **Perguntas:** {teste['quantidade_perguntas']}
                """

            )

    else:

        st.info(

            "Nenhum teste executado."

        )
       