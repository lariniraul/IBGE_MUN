"""Catálogo de pesquisas, com indicadores municipais e fontes por ano."""
import pandas as pd
import streamlit as st
import ibge
from painel_ibge import cidades

ATALHOS = {
    "Panorama municipal (escolarização, trabalho, saúde e ambiente)": (10058, None),
    "PIB per capita — série revisada": (38, ["47001"]),
    "IDHM — desenvolvimento humano municipal": (10111, ["329756"]),
    "Natalidade — nascidos vivos por residência da mãe": (20, ["29778"]),
    "Todas as pesquisas do catálogo": (None, None),
}


@st.cache_data(ttl=86400, show_spinner=False)
def pesquisas():
    return ibge.catalogo_pesquisas()


@st.cache_data(ttl=86400, show_spinner=False)
def indicadores(codigo):
    return ibge.indicadores_pesquisa(codigo)


def exibir():
    st.subheader("Catálogo de indicadores municipais")
    st.caption("Explore as pesquisas disponibilizadas pela API de Pesquisas do IBGE. A cobertura municipal e os anos variam; este catálogo não equivale a todas as tabelas do SIDRA.")
    try:
        lista = cidades()
        nomes = {str(r["id"]): r["nome"] for r in lista}
        codigos = list(nomes)
        cidade = st.selectbox("Município / SP", codigos,
            index=next((i for i, c in enumerate(codigos) if nomes[c] == "Cosmópolis"), 0),
            format_func=nomes.get, key="catalogo_cidade")
        atalho = st.selectbox("Grupo de indicadores", list(ATALHOS), key="catalogo_grupo")
        pesquisa, padrao = ATALHOS[atalho]
        catalogo = pesquisas()
        if pesquisa is None:
            lista_p = sorted(catalogo, key=lambda r: r["nome"])
            nomes_p = {r["id"]: r["nome"] for r in lista_p}
            pesquisa = st.selectbox("Pesquisa (digite para buscar)", list(nomes_p), format_func=nomes_p.get)
        descricao = next(r for r in catalogo if r["id"] == pesquisa)
        with st.spinner("Carregando catálogo de indicadores…"):
            metas = indicadores(pesquisa)
        escolhas = {r["id"]: r for r in metas}
        todos = st.checkbox("Consultar todos os indicadores desta pesquisa", value=padrao is None, key=f"todos_{atalho}_{pesquisa}")
        if todos:
            ids = list(escolhas)
            st.caption(f"{len(ids)} indicadores. Totais e subdivisões serão mantidos separados.")
        else:
            ids = st.multiselect("Indicadores (digite para buscar)", list(escolhas),
                default=[i for i in (padrao or []) if i in escolhas],
                format_func=lambda i: escolhas[i]["nome"], key=f"indicadores_{atalho}_{pesquisa}")
    except (ValueError, KeyError, StopIteration) as erro:
        st.error(f"Não foi possível carregar o catálogo: {erro}")
        return
    if pesquisa == 20:
        st.info("Natalidade: a contagem abaixo é do Registro Civil, por residência da mãe. Não é uma taxa por mil habitantes, nem deve ser confundida com nascimentos por local do parto.")
    if pesquisa == 10111:
        st.info("IDHM é um indicador do PNUD, disponibilizado pelo IBGE. O último ano retornado pode ser antigo; consulte a referência na tabela.")
    assinatura = (cidade, pesquisa, tuple(ids))
    if st.button("Consultar indicadores", type="primary"):
        st.session_state.pop("catalogo_resultado", None)
        if not ids:
            st.warning("Selecione pelo menos um indicador.")
        else:
            linhas, falhas = [], []
            progresso = st.progress(0)
            for inicio in range(0, len(ids), 20):
                bloco = ids[inicio:inicio+20]
                try:
                    linhas.extend(ibge.consultar_indicadores(cidade, [escolhas[i] for i in bloco], descricao.get("periodos", [])))
                except ValueError as erro:
                    falhas.append(f"Indicadores {', '.join(bloco)}: {erro}")
                progresso.progress(min(1.0, (inicio+20)/len(ids)))
            progresso.empty()
            st.session_state.catalogo_resultado = dict(assinatura=assinatura, linhas=linhas, falhas=falhas)
    resultado = st.session_state.get("catalogo_resultado")
    if not resultado or resultado["assinatura"] != assinatura:
        st.info("Clique em Consultar indicadores para visualizar os dados desta seleção.")
        return
    for falha in resultado["falhas"]:
        st.warning("Consulta parcial. " + falha)
    if not resultado["linhas"]:
        st.warning("Sem dados municipais retornados. Isso não representa valor zero.")
        return
    df = pd.DataFrame(resultado["linhas"])
    st.markdown(f"**{nomes[cidade]} / SP · {descricao['nome']}**")
    modo = st.radio("Período dos resultados", ["Último disponível por indicador", "Escolher anos", "Todos os anos"], horizontal=True)
    if modo == "Último disponível por indicador":
        df = df.sort_values("Ano").groupby("Código", sort=False).tail(1)
    elif modo == "Escolher anos":
        anos = st.multiselect("Anos", sorted(df["Ano"].unique()), key=f"anos_catalogo_{cidade}_{pesquisa}")
        df = df[df["Ano"].isin(anos)]
    texto = st.text_input("Buscar nos indicadores apresentados", key="catalogo_busca")
    if texto:
        df = df[df["Indicador"].str.contains(texto, case=False, regex=False)]
    df = df.copy()
    df["Valor"] = df["Valor"].map(ibge.formatar_valor)
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.caption("Não some indicadores: podem existir totais, subdivisões, percentuais e índices. A unidade e o multiplicador são os informados pela fonte; nenhum valor foi multiplicado automaticamente. Ausências e símbolos especiais são preservados.")
    st.markdown("[Documentação e fontes da API de Pesquisas do IBGE](https://servicodados.ibge.gov.br/api/docs/pesquisas)")
