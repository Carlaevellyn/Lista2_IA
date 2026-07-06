"""
agente_app.py — Interface (Streamlit chat) do agente baseado em LLM.

O agente (agente.py) conversa em linguagem natural e, quando precisa avaliar o
artigo, chama o Revisor de regras como ferramenta. Rode com:

    python -m streamlit run agente_app.py

Pré-requisito: Ollama instalado e rodando (`ollama pull llama3.2`).
"""
import streamlit as st

from agente import AgenteRevisor, disponivel, OLLAMA_HOST, OLLAMA_MODEL, OllamaIndisponivel

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


def extrair_texto_pdf(arquivo):
    if PdfReader is None:
        st.error("A biblioteca pypdf não está instalada. Instale com: pip install pypdf")
        return ""
    try:
        leitor = PdfReader(arquivo)
    except Exception as erro:
        st.error(f"Não foi possível ler o PDF: {erro}")
        return ""
    return "\n".join(p.extract_text() for p in leitor.pages if p.extract_text())


def painel_artigo(ollama_ok):
    """Painel recolhível de carregamento do artigo (largura cheia, não na sidebar)."""
    ja_carregado = "agente" in st.session_state
    with st.expander("📄 Artigo em análise", expanded=not ja_carregado):
        modo = st.radio("Forma de entrada", ["Texto manual", "PDF"], horizontal=True)
        if modo == "PDF":
            arquivo = st.file_uploader("Envie o artigo em PDF", type=["pdf"])
            texto = extrair_texto_pdf(arquivo) if arquivo else ""
            if texto:
                with st.expander("Ver texto extraído"):
                    st.text(texto)
        else:
            texto = st.text_area("Cole o texto do artigo", height=260,
                                 placeholder="Cole aqui o conteúdo do artigo…")

        col_botao, col_status = st.columns([1, 3])
        with col_botao:
            carregar = st.button("Carregar artigo", type="primary",
                                 use_container_width=True, disabled=not ollama_ok)
        with col_status:
            if ja_carregado:
                st.caption(f"✅ Artigo carregado ({st.session_state.n_palavras} palavras). "
                           "Pode conversar abaixo ou carregar outro.")

        if carregar:
            if texto.strip():
                st.session_state.agente = AgenteRevisor(texto)
                st.session_state.historico = []
                st.session_state.n_palavras = len(texto.split())
                st.rerun()
            else:
                st.warning("Nenhum texto de artigo foi informado.")


def main():
    st.set_page_config(page_title="Agente Revisor (LLM)", layout="wide")
    st.title("🤖 Agente Revisor de Artigos")
    st.caption(
        "O agente conversa em linguagem natural e usa o revisor de regras como "
        "ferramenta — o raciocínio de conformidade continua no motor simbólico."
    )

    ollama_ok = disponivel()
    if ollama_ok:
        st.success(f"Ollama conectado em `{OLLAMA_HOST}` · modelo `{OLLAMA_MODEL}`.")
    else:
        st.warning(
            f"**Ollama indisponível** em `{OLLAMA_HOST}`. O agente precisa dele para responder:\n\n"
            "1. Instale o Ollama — https://ollama.com\n"
            f"2. Baixe um modelo com suporte a *tool calling*: `ollama pull {OLLAMA_MODEL}`\n"
            "3. Deixe o Ollama aberto e recarregue esta página."
        )

    painel_artigo(ollama_ok)
    st.divider()
    st.subheader("💬 Conversa com o agente")

    if "agente" not in st.session_state:
        st.info("Carregue um artigo acima para começar a conversar.")
        return

    for msg in st.session_state.get("historico", []):
        with st.chat_message(msg["papel"]):
            st.markdown(msg["texto"])
            if msg.get("ferramentas"):
                st.caption("🔧 Ferramentas usadas: " + ", ".join(msg["ferramentas"]))

    pergunta = st.chat_input(
        "Pergunte algo sobre o artigo (ex.: a metodologia está adequada?)",
        disabled=not ollama_ok,
    )
    if pergunta:
        st.session_state.historico.append({"papel": "user", "texto": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)
        with st.chat_message("assistant"):
            with st.spinner("O agente está pensando…"):
                try:
                    resp = st.session_state.agente.conversar(pergunta)
                except Exception as e:  # OllamaIndisponivel ou falha inesperada
                    erro = f"⚠️ {e}"
                    st.error(erro)
                    # registra um turno de erro para não deixar balão de usuário órfão
                    st.session_state.historico.append({"papel": "assistant", "texto": erro})
                    return
            st.markdown(resp["resposta"])
            if resp["ferramentas"]:
                st.caption("🔧 Ferramentas usadas: " + ", ".join(resp["ferramentas"]))
        st.session_state.historico.append({
            "papel": "assistant",
            "texto": resp["resposta"],
            "ferramentas": resp["ferramentas"],
        })


if __name__ == "__main__":
    main()
