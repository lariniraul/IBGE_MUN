"""Dados públicos usados pelo portal da SSP-SP (sem autenticação)."""
import gzip
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

BASE = "https://www.ssp.sp.gov.br/"
MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def obter(caminho):
    try:
        req = Request(BASE+caminho, headers={"Accept": "application/json", "User-Agent": "ConsultaMunicipal/1.0"})
        with urlopen(req, timeout=45) as resposta:
            raw = resposta.read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        dados = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(dados, dict) or dados.get("success") is not True or not isinstance(dados.get("data"), list):
            raise ValueError("Resposta inesperada da SSP-SP.")
        return dados["data"]
    except (URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise ValueError("Não foi possível consultar a SSP-SP. Tente novamente mais tarde.") from erro


def municipios():
    return obter("v1/Municipios/RecuperaMunicipios")


def consultar(codigo, ano, meses):
    query = urlencode(dict(ano=ano, grupoDelito=6, tipoGrupo="MUNICÍPIO", idGrupo=codigo))
    dados = obter("v1/OcorrenciasMensais/RecuperaDadosMensaisAgrupados?"+query)
    linhas = []
    try:
        for grupo in dados:
            if int(grupo["ano"]) != ano:
                raise ValueError("A SSP retornou um ano diferente do solicitado.")
            for item in grupo["listaDados"]:
                publicado = int(item["publicado"])
                if not 0 <= publicado <= 12:
                    raise ValueError("A SSP informou um limite de publicação inesperado.")
                delito = item["delito"]["delito"]
                for mes in meses:
                    valor = item.get(MESES[mes-1])
                    disponivel = mes <= publicado and valor is not None
                    linhas.append({"Competência": f"{ano}-{mes:02d}", "Indicador": delito,
                        "Código do delito": item["idDelito"],
                        "Quantidade": valor if disponivel else None,
                        "Situação": "Publicado" if disponivel else "Não publicado / indisponível",
                        "Fonte": "SSP-SP"})
    except (KeyError, TypeError) as erro:
        raise ValueError("A estrutura da resposta da SSP-SP mudou.") from erro
    return linhas
