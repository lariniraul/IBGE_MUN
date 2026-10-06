import pandas as pd
import streamlit as st
import ibge


@st.cache_data(ttl=86400, show_spinner=False)
def cidades():
    return ibge.municipios_sp()


@st.cache_data(ttl=86400, show_spinner=False)
def anos_disponiveis(tabela):
    return ibge.periodos(tabela)


def exibir():
    st.subheader("Indicadores do IBGE")
    modo = st.radio("Consulta IBGE", ["Catálogo ampliado", "Censo e PIB (SIDRA)"], horizontal=True)
    if modo == "Catálogo ampliado":
        from catalogo_ibge import exibir as exibir_catalogo
        exibir_catalogo()
        return
    st.caption("Dados municipais de São Paulo. Cada indicador mantém seu próprio ano de referência; não utiliza o período mensal das receitas e despesas.")
    try:
        with st.spinner("Carregando municípios e anos do IBGE…"):
            lista = cidades()
            nomes = {str(r["id"]): r["nome"] for r in lista}
            codigos = list(nomes)
            padrao = next((i for i, codigo in enumerate(codigos) if nomes[codigo] == "Cosmópolis"), 0)
            cidade = st.selectbox("Município / SP", codigos, index=padrao,
                format_func=lambda codigo: nomes[codigo], key="ibge_cidade")
            consulta = st.selectbox("Indicadores", list(ibge.CONSULTAS), key="ibge_consulta")
            tabela, variaveis = ibge.CONSULTAS[consulta]
            disponiveis = anos_disponiveis(tabela)
    except ValueError as erro:
        st.error(str(erro))
        return
    anos = st.multiselect("Anos de referência", disponiveis, default=[disponiveis[-1]], key=f"ibge_anos_{tabela}")
    if st.button("Consultar IBGE", type="primary"):
        try:
            with st.spinner("Consultando indicadores…"):
                registros = ibge.consultar(tabela, variaveis, cidade, anos)
            st.session_state.ibge_resultado = dict(registros=registros, cidade=nomes[cidade],
                codigo=cidade, anos=sorted(anos), consulta=consulta, tabela=tabela)
        except ValueError as erro:
            st.session_state.pop("ibge_resultado", None)
            st.error(str(erro))
    resultado = st.session_state.get("ibge_resultado")
    if not resultado:
        st.info("Escolha os indicadores e clique em Consultar IBGE para visualizar os dados aqui.")
        return
    if (resultado["codigo"], resultado["consulta"], resultado["anos"]) != (cidade, consulta, sorted(anos)):
        st.info("Os filtros foram alterados. Clique em Consultar IBGE para atualizar os resultados.")
        return
    st.markdown(f"**{resultado['cidade']} / SP · Código IBGE {resultado['codigo']}**")
    if not resultado["registros"]:
        st.warning("O IBGE não retornou registros para esta seleção. Isso não significa valor zero.")
        return
    registros = resultado["registros"]
    ultimo = max(r["Ano"] for r in registros)
    recentes = [r for r in registros if r["Ano"] == ultimo]
    for coluna, registro in zip(st.columns(len(recentes)), recentes):
        coluna.metric(registro["Indicador"], ibge.formatar_valor(registro["Valor"]))
        coluna.caption(f"{registro['Unidade']} · {registro['Ano']}")
    df = pd.DataFrame(registros)
    df["Valor"] = df["Valor"].map(ibge.formatar_valor)
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.caption("PIB a preços correntes: valores nominais, sem correção pela inflação. A unidade ‘Mil Reais’ significa que cada unidade equivale a R$ 1.000. Sinais especiais retornados pelo IBGE são preservados, sem conversão para zero.")
    st.markdown(f"Fonte: [IBGE / SIDRA — tabela {resultado['tabela']}](https://sidra.ibge.gov.br/tabela/{resultado['tabela']})")
    with st.expander("Exportar indicadores (opcional)"):
        st.download_button("Salvar indicadores em CSV", pd.DataFrame(registros).to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name=f"ibge_{resultado['codigo']}_{resultado['tabela']}.csv", mime="text/csv")
