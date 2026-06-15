import requests
from bs4 import BeautifulSoup
from typing import Optional

DOU_URL = "https://www.in.gov.br/leiturajornal"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

TIMEOUT = 60


def _extrair_secao(url_secao: str, soup_secao: BeautifulSoup) -> dict:
    artigos = []
    for artigo in soup_secao.select("article"):
        titulo_tag = artigo.select_one("h3 a, h2 a, .titulo a")
        if not titulo_tag:
            continue
        titulo = titulo_tag.get_text(strip=True)
        link = titulo_tag.get("href", "")
        if link and not link.startswith("http"):
            link = f"https://www.in.gov.br{link}"
        resumo_tag = artigo.select_one(".resumo, p, .texto-resumo")
        resumo = resumo_tag.get_text(strip=True)[:200] if resumo_tag else ""
        artigos.append({"titulo": titulo, "link": link, "resumo": resumo})
    return {"artigos": artigos}


def _extrair_edicao(soup: BeautifulSoup) -> Optional[str]:
    padroes = [
        "span.data-edicao",
        ".edicao-data",
        "[class*=data]",
        "time",
    ]
    for seletor in padroes:
        tag = soup.select_one(seletor)
        if tag:
            texto = tag.get_text(strip=True)
            if texto:
                return texto
    return None


def acessar_dou() -> tuple[bool, str]:
    try:
        response = requests.get(DOU_URL, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            return False, f"DOU retornou status {response.status_code}"

        soup = BeautifulSoup(response.text, "lxml")

        # Data da edição
        data_edicao = _extrair_edicao(soup)

        # Seções disponíveis
        secoes_encontradas = []
        secoes = soup.select("section[id*=secao], .secao-card, [class*=secao]")
        for secao in secoes:
            nome_tag = secao.select_one("h2, h3, .secao-titulo, [class*=titulo]")
            nome = nome_tag.get_text(strip=True) if nome_tag else secao.get("id", "secao")
            qtd = len(secao.select("article, li, .artigo"))
            secoes_encontradas.append({"nome": nome, "qtd_artigos": qtd})

        linhas = [f"DOU acessado com sucesso"]
        if data_edicao:
            linhas.append(f"Edicao: {data_edicao}")
        if secoes_encontradas:
            for s in secoes_encontradas:
                linhas.append(f"  {s['nome']}: {s['qtd_artigos']} artigos")
        else:
            linhas.append("  (nenhuma secao identificada no parser)")

        return True, "\n".join(linhas)

    except requests.RequestException as e:
        return False, f"Erro ao acessar DOU: {e}"
