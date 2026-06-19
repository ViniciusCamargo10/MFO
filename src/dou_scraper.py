import re
import os
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
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")


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


def extrair_url_pdf_secao1(destino_pdf: str = "") -> tuple[bool, str, str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright nao instalado", ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()

            page.goto(DOU_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            btn = page.locator("button.btn-diario-completo")
            if btn.count() == 0:
                browser.close()
                return False, "Botao DIARIO COMPLETO nao encontrado", ""

            btn.click()
            page.wait_for_timeout(5000)

            content = page.content()

            pdfs = re.findall(
                r'https?://download\.in\.gov\.br/sgpub/do/secao1/[^"\']+\.pdf[^"\'\s]*',
                content,
            )
            if not pdfs:
                browser.close()
                return False, "Nenhum link de PDF da Secao 1 encontrado", ""

            url_pdf = pdfs[0]

            if not destino_pdf:
                browser.close()
                return True, url_pdf, ""

            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            url_pdf_clean = url_pdf.replace("&amp;", "&")

            page2 = context.new_page()
            with page2.expect_download(timeout=60000) as download_info:
                try:
                    page2.goto(url_pdf_clean, timeout=60000)
                except Exception:
                    pass

            download = download_info.value
            download.save_as(destino_pdf)
            page2.close()
            browser.close()
            return True, destino_pdf, url_pdf

    except Exception as e:
        return False, f"Erro: {e}", ""


def extrair_atos_do_pdf(caminho_pdf: str) -> tuple[bool, list, str]:
    try:
        import fitz
    except ImportError:
        return False, [], "PyMuPDF nao instalado. Execute: pip install pymupdf"

    try:
        doc = fitz.open(caminho_pdf)
    except Exception as e:
        return False, [], f"Erro ao abrir PDF: {e}"

    titulo_alvo = (
        "DEPARTAMENTO DE SANIDADE VEGETAL E INSUMOS AGRICOLAS "
        "COORDENACAO-GERAL DE AGROTOXICOS E AFINS"
    )
    titulo_alvo_acentos = (
        "DEPARTAMENTO DE SANIDADE VEGETAL E INSUMOS AGRÍCOLAS "
        "COORDENAÇÃO-GERAL DE AGROTÓXICOS E AFINS"
    )
    pagina_alvo = None

    def normalizar(texto):
        return re.sub(r"\s+", " ", texto).strip().upper()

    titulo_normalizado = normalizar(titulo_alvo)
    titulo_acentos_normalizado = normalizar(titulo_alvo_acentos)

    for pag_num in range(len(doc)):
        pagina = doc[pag_num]
        texto = normalizar(pagina.get_text("text"))
        if titulo_normalizado in texto or titulo_acentos_normalizado in texto:
            pagina_alvo = pag_num
            break

    if pagina_alvo is None:
        doc.close()
        return False, [], (
            "Procurei pelo departamento de Sanidade Vegetal no PDF de hoje, "
            "mas nao encontrei. Pode ser que nao tenha sido publicado ainda "
            "ou que nao tenha nada do DSV/CGAA nesta edicao."
        )

    pagina_fim = len(doc) - 1
    for pag_num in range(pagina_alvo + 1, len(doc)):
        pagina = doc[pag_num]
        texto_completo = pagina.get_text("text")
        for linha in texto_completo.split("\n"):
            linha_norm = normalizar(linha)
            if re.match(r"MINIST[ÉE]RIO\s+D(?:A|O|AS|OS|E)\s+[A-Z]", linha_norm, re.IGNORECASE):
                if "AGRICULTURA" not in linha_norm:
                    pagina_fim = pag_num - 1
                    break
        if pagina_fim < pag_num:
            break

    texto_completo = ""
    for pag_num in range(pagina_alvo, pagina_fim + 1):
        pagina = doc[pag_num]
        texto_pag = pagina.get_text("text")
        if pag_num == pagina_alvo:
            lines = texto_pag.split("\n")
            for line_idx, line in enumerate(lines):
                line_norm = normalizar(line)
                if "SANIDADE VEGETAL E INSUMOS AGRICOLAS" in line_norm or "SANIDADE VEGETAL E INSUMOS AGRÍCOLAS" in line_norm:
                    texto_pag = "\n".join(lines[line_idx:])
                    break
        texto_completo += texto_pag + "\n"

    doc.close()

    cabecalho_ato = re.search(
        r"(ATO\s+N[º°]?\s*\d[\d,.]*\s*,?\s*DE\s+\d{1,2}\s+DE\s+\w+\s+DE\s+\d{4})",
        texto_completo,
        re.IGNORECASE,
    )

    if not cabecalho_ato:
        return False, [], (
            f"Encontrei o DSV na pagina {pagina_alvo + 1}, "
            f"mas nao tinha nenhum ATO nesta edicao."
        )

    atos = [{
        "cabecalho": cabecalho_ato.group(1).strip(),
        "pagina_inicio": pagina_alvo + 1,
        "texto": texto_completo.strip(),
    }]

    return True, atos, "1 ATO do DSV/CGAA encontrado."


def extrair_retificacoes_do_pdf(caminho_pdf: str) -> tuple[bool, list, str]:
    try:
        import fitz
    except ImportError:
        return False, [], "PyMuPDF nao instalado. Execute: pip install pymupdf"

    try:
        doc = fitz.open(caminho_pdf)
    except Exception as e:
        return False, [], f"Erro ao abrir PDF: {e}"

    def normalizar(texto):
        return re.sub(r"\s+", " ", texto).strip().upper()

    titulo_dsv = (
        "DEPARTAMENTO DE SANIDADE VEGETAL E INSUMOS AGRICOLAS "
        "COORDENACAO-GERAL DE AGROTOXICOS E AFINS"
    )
    titulo_dsv_acentos = (
        "DEPARTAMENTO DE SANIDADE VEGETAL E INSUMOS AGRÍCOLAS "
        "COORDENAÇÃO-GERAL DE AGROTÓXICOS E AFINS"
    )
    titulo_normalizado = normalizar(titulo_dsv)
    titulo_acentos_normalizado = normalizar(titulo_dsv_acentos)

    pagina_dsv_inicio = None
    for pag_num in range(len(doc)):
        pagina = doc[pag_num]
        texto = normalizar(pagina.get_text("text"))
        if titulo_normalizado in texto or titulo_acentos_normalizado in texto:
            pagina_dsv_inicio = pag_num
            break

    if pagina_dsv_inicio is None:
        doc.close()
        return False, [], "DSV/CGAA nao encontrado neste PDF."

    pagina_dsv_fim = len(doc) - 1
    for pag_num in range(pagina_dsv_inicio + 1, len(doc)):
        pagina = doc[pag_num]
        texto_completo = pagina.get_text("text")
        for linha in texto_completo.split("\n"):
            linha_norm = normalizar(linha)
            if re.match(r"MINIST[ÉE]RIO\s+D(?:A|O|AS|OS|E)\s+[A-Z]", linha_norm, re.IGNORECASE):
                if "AGRICULTURA" not in linha_norm:
                    pagina_dsv_fim = pag_num - 1
                    break
        if pagina_dsv_fim < pag_num:
            break

    retificacoes = []

    for pag_num in range(pagina_dsv_inicio, pagina_dsv_fim + 1):
        pagina = doc[pag_num]
        texto = pagina.get_text("text")
        texto_normalizado = normalizar(texto)

        blocos_onde = list(re.finditer(
            r"ONDE\s+SE\s+L[EÊÉ]\s*[:\-]?\s*[\"\']?",
            texto_normalizado,
            re.IGNORECASE,
        ))

        blocos_leia = list(re.finditer(
            r"LEIA[\-\s]*SE\s*[:\-]?\s*[\"\']?",
            texto_normalizado,
            re.IGNORECASE,
        ))

        if blocos_onde and blocos_leia:
            for i, match_onde in enumerate(blocos_onde):
                inicio_onde = match_onde.end()

                closest_leia = None
                for match_leia in blocos_leia:
                    if match_leia.start() > match_onde.start():
                        closest_leia = match_leia
                        break

                if not closest_leia:
                    continue

                inicio_leia = closest_leia.start()

                onde_texto = texto_normalizado[inicio_onde:inicio_leia].strip()
                onde_texto = re.sub(r"[\"\']$", "", onde_texto).strip()
                onde_texto = re.sub(r"\s+", " ", onde_texto)

                fim_leia = min(closest_leia.end() + 300, len(texto_normalizado))
                leia_texto = texto_normalizado[closest_leia.end():fim_leia].strip()

                proximo_marcador = re.search(
                    r"(?:ONDE\s+SE\s+L[EÊÉ]|RETIFICAC|DELEGAC|COORDENAC|PORTARIA\s+N|ATO\s+N|DESPACHO|GERENCIA\s+REGIONAL)",
                    leia_texto,
                    re.IGNORECASE,
                )
                if proximo_marcador:
                    leia_texto = leia_texto[:proximo_marcador.start()].strip()

                leia_texto = re.sub(r"[\"\']$", "", leia_texto).strip()
                leia_texto = re.sub(r"\s+", " ", leia_texto)

                if onde_texto and leia_texto and len(onde_texto) > 5 and len(leia_texto) > 5:
                    ja_existe = any(
                        r.get("onde_se_le") == onde_texto and r.get("leia_se") == leia_texto
                        for r in retificacoes
                    )
                    if not ja_existe:
                        retificacoes.append({
                            "tipo": "direta",
                            "onde_se_le": onde_texto,
                            "leia_se": leia_texto,
                            "pagina": pag_num + 1,
                            "descricao": f"Onde se lê: \"{onde_texto}\" -> Leia-se: \"{leia_texto}\"",
                        })

    doc.close()

    qtd_diretas = len(retificacoes)

    if qtd_diretas == 0:
        return False, [], "Nenhuma retificacao do DSV/CGAA encontrada neste PDF."
    elif qtd_diretas > 0:
        msg = f"Total de {qtd_diretas} retificacao(oes) direta(s) do DSV/CGAA encontrada(s). Nenhuma retificacao indireta identificada (necessario implementar deteccao especifica para o DSV/CGAA)."
        return True, retificacoes, msg
