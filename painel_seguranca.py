import pandas as pd
import streamlit as st
import seguranca
from api import meses_periodo


@st.cache_data(ttl=86400, show_spinner=False)
def cidades():
    return seguranca.municipios()


def exibir():
    st.subheader("Segurança pública • SSP-SP")
    st.caption("Homicídios, furtos e demais indicadores criminais publicados para o município. Fonte: Secretaria da Segurança Pública de São Paulo, não IBGE.")
    try:
        lista = cidades()
        nomes = {r["codMunicipio"]: r["nome"] for r in lista}
        codigos = list(nomes)
        cidade = st.selectbox("Município / SP", codigos,
            index=next((i for i, c in enumerate(codigos) if nomes[c] == "Cosmópolis"), 0),
            format_func=nomes.get, key="ssp_cidade")
    except (ValueError, KeyError) as erro:
        st.error(str(erro))
        return
    c1, c2 = st.columns(2)
    inicio = c1.text_input("De (MM/AAAA)", "01/2026", key="ssp_inicio")
    fim = c2.text_input("Até (MM/AAAA)", "01/2026", key="ssp_fim")
    assinatura = (cidade, inicio, fim)
    if st.button("Consultar segurança pública", type="primary"):
        st.session_state.pop("ssp_resultado", None)
        try:
            meses = meses_periodo(inicio, fim)
            linhas, falhas = [], []
            with st.spinner("Consultando a SSP-SP…"):
                for ano in sorted({a for a, m in meses}):
                    try:
                        linhas.extend(seguranca.consultar(cidade, ano, [m for a, m in meses if a == ano]))
                    except ValueError as erro:
                        falhas.append(f"{ano}: {erro}")
            st.session_state.ssp_resultado = dict(assinatura=assinatura, linhas=linhas, falhas=falhas)
        except ValueError as erro:
            st.error(str(erro))
    resultado = st.session_state.get("ssp_resultado")
    if not resultado or resultado["assinatura"] != assinatura:
        st.info("Clique em Consultar segurança pública para visualizar esta seleção.")
        return
    for falha in resultado["falhas"]:
        st.warning("Consulta parcial: " + falha)
    if not resultado["linhas"]:
        st.warning("Sem registros retornados. Ausência de dados não significa ausência de crimes.")
        return
    df = pd.DataFrame(resultado["linhas"])
    st.markdown(f"**{nomes[cidade]} / SP · {inicio} a {fim}**")
    opcoes = sorted(df["Indicador"].unique())
    padrao = [x for x in opcoes if "HOMICÍDIO DOLOSO" in x or "FURTO" in x]
    escolhidos = st.multiselect("Indicadores criminais", opcoes, default=padrao, key=f"ssp_indicadores_{cidade}_{inicio}_{fim}")
    df = df[df["Indicador"].isin(escolhidos)].copy()
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="raise").astype("Int64")
    if (df["Situação"] != "Publicado").any():
        st.warning("Há meses ainda não publicados. Esses valores estão em branco e não são tratados como zero.")
    st.dataframe(df, hide_index=True, use_container_width=True)
    if not df.empty:
        resumo = df.groupby("Indicador", as_index=False).agg(
            **{"Soma dos meses publicados": ("Quantidade", lambda s: s.sum(min_count=1)),
               "Meses publicados": ("Quantidade", "count"), "Meses selecionados": ("Competência", "count")})
        st.dataframe(resumo, hide_index=True, use_container_width=True)
    st.caption("Cada natureza é apresentada separadamente. Não some ocorrências com vítimas, nem totais com suas subcategorias. Registros policiais podem sofrer revisão e não representam necessariamente todos os crimes ocorridos.")
    st.markdown("[Fonte e notas da SSP-SP](https://www.ssp.sp.gov.br/estatistica/dados-mensais) · [Nota técnica](https://www.ssp.sp.gov.br/estatistica/nota-tecnica)")
