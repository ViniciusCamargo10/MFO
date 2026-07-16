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

    qtd_diretas = len(retificacoes)
    doc.close()

    if qtd_diretas == 0:
        return False, [], "Nenhuma retificacao direta do DSV/CGAA encontrada neste PDF."
    msg = f"Total de {qtd_diretas} retificacao(oes) direta(s) do DSV/CGAA encontrada(s)."
    return True, retificacoes, msg


def extrair_retificacoes_indiretas_do_pdf(caminho_pdf: str) -> tuple[bool, list, str]:
    """
    Segunda passada independente no PDF buscando retificacoes indiretas do DSV/CGAA.

    Retificacoes indiretas ficam na secao 'RETIFICACOES' ou 'ERRATA' no final do PDF,
    fora do bloco do DSV/CGAA. Sao frases do tipo:
      - "Retifica-se o Ato no X do DSV publicado no DOU de..."
      - "Errata: No Ato no Y do CGAA..."
      - "Correcao: Na publicacao do Ato no Z do DSV..."

    Diferente das retificacoes diretas (ONDE SE LE / LEIA-SE), estas nao trazem
    o par de correcao — apenas referenciam o ato e a data originais.
    """
    try:
        import fitz
    except ImportError:
        return False, [], "PyMuPDF nao instalado. Execute: pip install pymupdf"

    try:
        doc = fitz.open(caminho_pdf)
    except Exception as e:
        return False, [], f"Erro ao abrir PDF: {e}"

    def normalizar(texto: str) -> str:
        return re.sub(r"\s+", " ", texto).strip().upper()

    # Padroes para identificar inicio de secao de retificacoes no PDF
    PADROES_SECAO_RETIF = re.compile(
        r"^\s*RETIFICA[ÇC][ÕO]ES\s*$|^\s*ERRATA\s*$|^\s*ERRATA[S]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    # Padroes para detectar retificacao indireta do DSV/CGAA
    PADROES_RETIF_INDIRETA = [
        # "Retifica-se o Ato no 39 do DSV..."
        re.compile(
            r"RETIFICA[- ]?SE\s+O\s+ATO\s+N[Oº°]?\s*\.?\s*(\d+)[^,.\n]*?"
            r"(?:DSV|CGAA|SANIDADE\s+VEGETAL|AGROT[ÓO]XICOS)[^,.\n]*?"
            r"(?:PUBLICADO\s+NO\s+DOU\s+DE\s+([\d]{1,2}[/\-][\d]{1,2}[/\-][\d]{4}))?",
            re.IGNORECASE,
        ),
        # "Errata: No Ato no 49 do CGAA..."
        re.compile(
            r"ERRATA\s*[:\-]?\s*NO\s+ATO\s+N[Oº°]?\s*\.?\s*(\d+)[^,.\n]*?"
            r"(?:DSV|CGAA|SANIDADE\s+VEGETAL|AGROT[ÓO]XICOS)",
            re.IGNORECASE,
        ),
        # "Correcao: Na publicacao do Ato no 45 do DSV..."
        re.compile(
            r"CORRE[ÇC][ÃA]O\s*[:\-]?\s*NA\s+PUBLICA[ÇC][ÃA]O\s+DO\s+ATO\s+N[Oº°]?\s*\.?\s*(\d+)[^,.\n]*?"
            r"(?:DSV|CGAA|SANIDADE\s+VEGETAL|AGROT[ÓO]XICOS)",
            re.IGNORECASE,
        ),
        # "Corrigir a publicacao do Ato do DSV..."
        re.compile(
            r"CORRIGIR\s+A\s+PUBLICA[ÇC][ÃA]O\s+DO\s+ATO[^,.\n]*?"
            r"(?:DSV|CGAA|SANIDADE\s+VEGETAL|AGROT[ÓO]XICOS)",
            re.IGNORECASE,
        ),
    ]

    # Palavras que indicam que NAO e retificacao indireta — sao ATOS normais do DSV
    PADROES_FALSO_POSITIVO = re.compile(
        r"CANCELAMOS\s+O\s+REGISTRO|TORNAMOS\s+SEM\s+EFEITO|REVOGAMOS",
        re.IGNORECASE,
    )

    retificacoes_indiretas = []

    for pag_num in range(len(doc)):
        pagina = doc[pag_num]
        texto_pag = pagina.get_text("text")
        texto_norm = normalizar(texto_pag)

        # Checar se esta pagina contem secao de RETIFICACOES / ERRATA
        em_secao_retif = bool(PADROES_SECAO_RETIF.search(texto_norm))

        # Varrer linha a linha em busca dos padroes de retificacao indireta
        linhas = texto_pag.split("\n")
        for i, linha in enumerate(linhas):
            linha_norm = normalizar(linha)

            # Ignorar linhas muito curtas ou que sejam falsos positivos
            if len(linha_norm) < 15:
                continue
            if PADROES_FALSO_POSITIVO.search(linha_norm):
                continue

            for padrao in PADROES_RETIF_INDIRETA:
                m = padrao.search(linha_norm)
                if not m:
                    continue

                # Extrair numero do ato (grupo 1 quando disponivel)
                num_ato = ""
                try:
                    num_ato = m.group(1) if m.lastindex and m.lastindex >= 1 else ""
                except IndexError:
                    pass

                # Extrair data referenciada do match ou do contexto (proximas 3 linhas)
                data_ref = ""
                try:
                    data_ref = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
                except IndexError:
                    pass

                if not data_ref:
                    # Buscar "DOU de DD/MM/AAAA" ou "DOU de DD-MM-AAAA" nas proximas linhas
                    contexto = " ".join(linhas[i:min(i + 4, len(linhas))])
                    m_data = re.search(
                        r"DOU\s+DE\s+(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})",
                        normalizar(contexto),
                        re.IGNORECASE,
                    )
                    if not m_data:
                        m_data = re.search(
                            r"(\d{1,2})\s+DE\s+(\w+)\s+DE\s+(\d{4})",
                            normalizar(contexto),
                            re.IGNORECASE,
                        )
                        if m_data:
                            dia_r = m_data.group(1).zfill(2)
                            mes_r = MESES_BR.get(m_data.group(2).upper(), "")
                            ano_r = m_data.group(3)
                            data_ref = f"{dia_r}/{mes_r}/{ano_r}" if mes_r else ""
                    else:
                        dia_r = m_data.group(1).zfill(2)
                        mes_r = m_data.group(2).zfill(2)
                        ano_r = m_data.group(3)
                        data_ref = f"{dia_r}/{mes_r}/{ano_r}"

                # Capturar bloco de texto da retificacao (linha atual + proximas ate linha em branco)
                bloco_linhas = []
                for j in range(i, min(i + 8, len(linhas))):
                    l = linhas[j].strip()
                    if not l and bloco_linhas:
                        break
                    if l:
                        bloco_linhas.append(l)
                texto_bloco = " ".join(bloco_linhas)

                # Evitar duplicatas
                ja_existe = any(
                    r.get("ato_original") == num_ato and r.get("pagina") == pag_num + 1
                    for r in retificacoes_indiretas
                )
                if ja_existe:
                    break

                retificacoes_indiretas.append({
                    "tipo": "indireta",
                    "ato_original": f"ATO Nº {num_ato}" if num_ato else "ATO (numero nao identificado)",
                    "data_original": data_ref,
                    "texto": texto_bloco,
                    "pagina": pag_num + 1,
                    "em_secao_retificacoes": em_secao_retif,
                    "descricao": (
                        f"Retificacao indireta: {texto_bloco[:120]}..."
                        if len(texto_bloco) > 120
                        else f"Retificacao indireta: {texto_bloco}"
                    ),
                })
                break  # Um match por linha e suficiente

    doc.close()

    qtd = len(retificacoes_indiretas)
    if qtd == 0:
        return False, [], "Nenhuma retificacao indireta do DSV/CGAA encontrada neste PDF."

    msg = f"Total de {qtd} retificacao(oes) indireta(s) do DSV/CGAA encontrada(s)."
    return True, retificacoes_indiretas, msg


MESES_BR = {
    "JANEIRO": "01", "FEVEREIRO": "02", "MARÇO": "03", "MARCO": "03",
    "ABRIL": "04", "MAIO": "05", "JUNHO": "06", "JULHO": "07",
    "AGOSTO": "08", "SETEMBRO": "09", "OUTUBRO": "10", "NOVEMBRO": "11", "DEZEMBRO": "12",
}


def extrair_data_dou_referenciada(texto: str) -> str:
    match = re.search(
        r"NO\s+DOU\s+DE\s+(\d{1,2})\s+DE\s+(\w+)\s+DE\s+(\d{4})",
        texto, re.IGNORECASE
    )
    if not match:
        return ""
    dia, mes_ext, ano = match.group(1), match.group(2).upper(), match.group(3)
    mes = MESES_BR.get(mes_ext)
    if not mes:
        return ""
    return f"{dia.zfill(2)}/{mes}/{ano}"


def extrair_url_pdf_secao1_por_data(data_str: str, destino_pdf: str = "") -> tuple[bool, str, str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright nao instalado", ""

    if "/" in data_str:
        partes = data_str.split("/")
    elif "-" in data_str:
        partes = data_str.split("-")
    else:
        return False, f"Formato de data invalido: {data_str}", ""

    if len(partes) != 3:
        return False, f"Formato de data invalido: {data_str}", ""

    dia, mes, ano = partes
    nome_arquivo = f"secao1_{ano}_{mes.zfill(2)}_{dia.zfill(2)}.pdf"
    if not destino_pdf:
        destino_pdf = os.path.join(DOWNLOAD_DIR, nome_arquivo)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                locale="pt-BR", timezone_id="America/Sao_Paulo",
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            page = context.new_page()

            urls_tentativas = [
                f"https://www.in.gov.br/leiturajornal?data={dia}-{mes}-{ano}",
                f"https://www.in.gov.br/leiturajornal?data={ano}-{mes.zfill(2)}-{dia.zfill(2)}",
                f"https://www.in.gov.br/leiturajornal?data={dia}/{mes}/{ano}",
            ]

            for url in urls_tentativas:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)

                    btn = page.locator("button.btn-diario-completo, button:has-text('DIARIO COMPLETO'), button:has-text('DIÁRIO COMPLETO')")
                    if btn.count() > 0:
                        btn.click()
                        page.wait_for_timeout(5000)

                        content = page.content()
                        pdfs = re.findall(
                            r'https?://download\.in\.gov\.br/sgpub/do/secao1/[^"\']+\.pdf[^"\'\s]*',
                            content,
                        )
                        if pdfs:
                            url_pdf = pdfs[0].replace("&amp;", "&")
                            os.makedirs(DOWNLOAD_DIR, exist_ok=True)

                            page2 = context.new_page()
                            with page2.expect_download(timeout=120000) as download_info:
                                try:
                                    page2.goto(url_pdf, timeout=120000)
                                except Exception:
                                    pass

                            download = download_info.value
                            download.save_as(destino_pdf)
                            page2.close()
                            browser.close()
                            return True, destino_pdf, url_pdf
                except Exception:
                    continue

            browser.close()
            return False, f"Nao foi possivel acessar DOU de {data_str}", ""
    except Exception as e:
        return False, f"Erro ao acessar DOU de {data_str}: {e}", ""


def processar_retificacoes_referenciadas(retificacoes: list) -> list:
    resultados = []
    for ret in retificacoes:
        data_ref = ret.get("data_dou_referenciada", "")
        if not data_ref:
            resultados.append(ret)
            continue

        nome_pdf = data_ref.replace("/", "_") + ".pdf"
        caminho_pdf = os.path.join(DOWNLOAD_DIR, f"referenciado_{nome_pdf}")

        sucesso, msg, url = extrair_url_pdf_secao1_por_data(data_ref, caminho_pdf)
        if not sucesso:
            ret["referencia_erro"] = msg
            resultados.append(ret)
            continue

        sucesso_atos, atos_ref, msg_atos = extrair_atos_do_pdf(caminho_pdf)
        if not sucesso_atos:
            ret["referencia_erro"] = msg_atos
            resultados.append(ret)
            continue

        texto_original = atos_ref[0].get("texto", "")
        onde = ret.get("onde_se_le", "")
        leia = ret.get("leia_se", "")

        def _aplicar_correcao(texto_original: str, onde_se_le: str, leia_se: str) -> tuple[str, bool]:
            texto_c = texto_original
            ocorrencias = 0
            onde_clean = onde_se_le.strip(" .")
            leia_clean = leia_se.strip(" .")
            leia_sem_data = re.sub(
                r"\s*NO\s+DOU\s+DE\s+\d+\s+DE\s+\w+\s+DE\s+\d+\s*,?\s*EM\s*",
                "", leia_clean, flags=re.IGNORECASE
            ).strip()

            partes_onde = [p.strip() for p in re.split(r'(?<=\.)(?=\s)', onde_clean) if p.strip()]
            partes_leia = [p.strip() for p in re.split(r'(?<=\.)(?=\s)', leia_sem_data) if p.strip()]

            for po, pl in zip(partes_onde, partes_leia):
                if len(po) > 10 and texto_c.upper().count(po.upper()) > 0:
                    ocorrencias += 1
                    texto_c = re.sub(re.escape(po), pl, texto_c, flags=re.IGNORECASE)
            return texto_c, ocorrencias > 0

        texto_corrigido_ref, correcao_aplicada_ref = _aplicar_correcao(texto_original, onde, leia)

        ret["referencia_data"] = data_ref
        ret["referencia_pdf"] = caminho_pdf
        ret["referencia_cabecalho"] = atos_ref[0].get("cabecalho", "")
        ret["correcao_aplicada_referencia"] = correcao_aplicada_ref
        if correcao_aplicada_ref:
            ret["texto_original_referencia"] = texto_original
            ret["texto_corrigido_referencia"] = texto_corrigido_ref

        resultados.append(ret)

    return resultados


def tratar_retificacoes_diretas(atos: list, retificacoes: list) -> list:
    if not retificacoes or not atos:
        return retificacoes

    texto_ato = atos[0].get("texto", "").upper() if atos else ""

    PADROES_CATEGORIA = [
        ("Marca comercial", r"MARCA\s+COMERCIAL"),
        ("Fabricantes", r"(?:ALTERAÇÃO|INCLUSÃO|EXCLUSÃO)\s+(?:DO|DE)\s+FABRICANTE"),
        ("Formuladores", r"(?:ALTERAÇÃO|INCLUSÃO|EXCLUSÃO)\s+(?:DO|DE)\s+FORMULADOR"),
        ("Manipuladores", r"(?:ALTERAÇÃO|INCLUSÃO|EXCLUSÃO)\s+(?:DO|DE)\s+MANIPULADOR"),
        ("Razão social", r"RAZÃO\s+SOCIAL|RAZAO\s+SOCIAL"),
        ("Endereço", r"ALTERAÇÃO\s+DE\s+ENDEREÇO|ALTERACAO\s+DE\s+ENDERECO"),
        ("Transferência de titularidade", r"TRANSFERÊNCIA\s+DE\s+TITULARIDADE|TRANSFERENCIA\s+DE\s+TITULARIDADE"),
        ("Produto técnico no formulado", r"PRODUTO\s+TÉCNICO|PRODUTO\s+TECNICO"),
        ("Nome químico / comum", r"NOME\s+QUÍMICO|NOME\s+QUIMICO|NOME\s+COMUM"),
        ("Classificação ambiental", r"CLASSIFICAÇÃO\s+(?:QUANTO\s+)?AO?\s+POTENCIAL"),
        ("Classificação toxicológica", r"CLASSIFICAÇÃO\s+TOXICOLÓGICA|CLASSIFICACAO\s+TOXICOLOGICA"),
        ("Recomendações de uso", r"RECOMENDAÇÕES\s+DE\s+USO|RECOMENDACOES\s+DE\s+USO"),
    ]

    def classificar_motivo(texto: str) -> str:
        texto_u = texto.upper()
        for categoria, padrao in PADROES_CATEGORIA:
            if re.search(padrao, texto_u):
                return categoria
        return "Outros"

    def classificar_tipo(texto: str) -> str:
        texto_u = texto.upper()
        if "EXCLUSÃO" in texto_u or "EXCLUSAO" in texto_u or "EXCLUIR" in texto_u:
            return "Exclusão"
        if "INCLUSÃO" in texto_u or "INCLUSAO" in texto_u or "INCLUIR" in texto_u:
            return "Inclusão"
        if "ALTERAÇÃO" in texto_u or "ALTERACAO" in texto_u:
            return "Alteração"
        return "Correção"

    def extrair_numero_registro(texto: str) -> str:
        match = re.search(r"REGISTRO\s+N[º°]?\s*(\d+)", texto, re.IGNORECASE)
        return match.group(1) if match else ""

    def extrair_numero_processo(texto: str) -> str:
        match = re.search(r"PROCESSO\s+N[º°]?\s*([\d./-]+)", texto, re.IGNORECASE)
        return match.group(1).strip(" .") if match else ""

    def extrair_nome_produto(texto: str) -> str:
        match = re.search(r"PRODUTO\s+([^,]+?)(?:\s*,\s*REGISTRO|\s*,\s*PROCESSO|\s*REGISTRO|\s*PROCESSO)", texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"DO\s+PRODUTO\s+([^,]+?)(?:\s*,\s*REGISTRO|\s*,\s*PROCESSO)", texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def aplicar_correcao(texto_original: str, onde_se_le: str, leia_se: str) -> tuple[str, bool]:
        texto_corrigido = texto_original
        ocorrencias = 0

        onde_clean = onde_se_le.strip(" .")
        leia_clean = leia_se.strip(" .")
        leia_sem_data = re.sub(
            r"\s*NO\s+DOU\s+DE\s+\d+\s+DE\s+\w+\s+DE\s+\d+\s*,?\s*EM\s*",
            "", leia_clean, flags=re.IGNORECASE
        ).strip()

        partes_onde = [p.strip() for p in re.split(r'(?<=\.)(?=\s)', onde_clean) if p.strip()]
        partes_leia = [p.strip() for p in re.split(r'(?<=\.)(?=\s)', leia_sem_data) if p.strip()]

        for parte_onde, parte_leia in zip(partes_onde, partes_leia):
            if len(parte_onde) > 10:
                count = texto_corrigido.upper().count(parte_onde.upper())
                if count > 0:
                    ocorrencias += count
                    texto_corrigido = re.sub(
                        re.escape(parte_onde), parte_leia, texto_corrigido, flags=re.IGNORECASE
                    )

        return texto_corrigido, ocorrencias > 0

    resultados = []
    for ret in retificacoes:
        onde = ret.get("onde_se_le", "")
        leia = ret.get("leia_se", "")

        categoria = classificar_motivo(onde + " " + leia)
        tipo = classificar_tipo(onde + " " + leia)
        registro = extrair_numero_registro(onde + " " + leia)
        processo = extrair_numero_processo(onde + " " + leia)
        produto = extrair_nome_produto(onde + " " + leia)

        texto_corrigido, aplicada = aplicar_correcao(texto_ato, onde, leia)

        data_referenciada = extrair_data_dou_referenciada(leia) if not aplicada else ""

        ret_enriquecida = {
            **ret,
            "categoria": categoria,
            "tipo_mudanca": tipo,
            "registro": registro,
            "processo": processo,
            "produto": produto,
            "correcao_aplicada": aplicada,
            "data_dou_referenciada": data_referenciada,
        }
        resultados.append(ret_enriquecida)

    if resultados:
        atos[0]["texto_corrigido"] = texto_corrigido

    return resultados


MATRIZ_FILTROS = {
    "Fabricantes": {"inclusao": True, "alteracao": True, "exclusao": True},
    "Formuladores": {"inclusao": True, "alteracao": True, "exclusao": True},
    "Manipuladores": {"inclusao": True, "alteracao": True, "exclusao": True},
    "Marca comercial": {"inclusao": True, "alteracao": True, "exclusao": True},
    "Razão social": {"inclusao": True, "alteracao": True, "exclusao": True},
    "Produto técnico no formulado": {"inclusao": True, "alteracao": True, "exclusao": True},
    "Endereço": {"alteracao": True},
    "Formulação": {"inclusao": True, "alteracao": True, "exclusao": True},
    "Transferência de titularidade": {"alteracao": True},
    "Retificações no DOU": {"alteracao": True},
}


def aplicar_filtros_atos(atos: list) -> list:
    if not atos:
        return []

    texto = atos[0].get("texto", "")
    padrao_item = re.compile(r"(\d+)\.\s*De\s+Acordo\s+com\s+o\s+Art\.", re.IGNORECASE)

    items_raw = []
    matches = list(padrao_item.finditer(texto))
    for i, match in enumerate(matches):
        inicio = match.start()
        fim = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        items_raw.append({
            "numero": int(match.group(1)),
            "texto": texto[inicio:fim].strip().replace("\n", " "),
        })

    PADROES_CATEGORIA = [
        ("Marca comercial", r"MARCA\s+COMERCIAL"),
        ("Fabricantes", r"(?:DO|DE|DOS)\s+FABRICANTE"),
        ("Formuladores", r"(?:DO|DE|DOS)\s+FORMULADOR"),
        ("Manipuladores", r"(?:DO|DE|DOS)\s+MANIPULADOR"),
        ("Razão social", r"RAZÃO\s+SOCIAL|RAZAO\s+SOCIAL"),
        ("Produto técnico no formulado", r"PRODUTO\s+TÉCNICO|PRODUTO\s+TECNICO"),
        ("Endereço", r"ALTERAÇÃO\s+DE\s+ENDEREÇO|ALTERACAO\s+DE\s+ENDERECO"),
        ("Transferência de titularidade", r"TRANSFERÊNCIA\s+DE\s+TITULARIDADE|TRANSFERENCIA\s+DE\s+TITULARIDADE"),
        ("Formulação", r"FORMULAÇÃO|FORMULACAO"),
        ("Nome químico", r"NOME\s+QUÍMICO|NOME\s+QUIMICO"),
        ("Nome comum", r"NOME\s+COMUM"),
        ("Classificação ambiental", r"CLASSIFICAÇÃO\s+(?:QUANTO\s+)?AO?\s+POTENCIAL"),
        ("Classificação toxicológica", r"CLASSIFICAÇÃO\s+TOXICOLÓGICA|CLASSIFICACAO\s+TOXICOLOGICA"),
        ("Recomendações de uso", r"RECOMENDAÇÕES\s+DE\s+USO|RECOMENDACOES\s+DE\s+USO"),
        ("Inclusão de fabricante", r"INCLUSÃO\s+(?:DO|DE)\s+FABRICANTE|INCLUSAO\s+(?:DO|DE)\s+FABRICANTE"),
    ]

    def classificar_categoria(texto_item: str) -> str:
        texto_u = texto_item.upper()
        matches_encontrados = []
        for categoria, padrao in PADROES_CATEGORIA:
            if re.search(padrao, texto_u):
                matches_encontrados.append(categoria)
        return matches_encontrados[0] if matches_encontrados else "Outros"

    def classificar_tipo(texto_item: str) -> str:
        texto_u = texto_item.upper()
        if "EXCLUSÃO" in texto_u or "EXCLUSAO" in texto_u:
            return "Exclusão"
        if "INCLUSÃO" in texto_u or "INCLUSAO" in texto_u:
            return "Inclusão"
        if "ALTERAÇÃO" in texto_u or "ALTERACAO" in texto_u:
            return "Alteração"
        if "TRANSFERÊNCIA" in texto_u or "TRANSFERENCIA" in texto_u:
            return "Alteração"
        if "AUTORIZAMOS" in texto_u or "AUTORIZADO" in texto_u:
            return "Autorização"
        return "Outros"

    def extrair_registro(texto_item: str) -> str:
        match = re.search(r"REGISTRO\s+N[º°]?\s*(?:TC)?(\d[\dA-Z]*)", texto_item, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r"registro\s+n[º°]?\s*(?:TC)?(\d[\dA-Z]*)", texto_item, re.IGNORECASE)
        return match.group(1) if match else ""

    def extrair_processo(texto_item: str) -> str:
        match = re.search(r"PROCESSO\s+N[º°]?\s*(\d[\d./-]*?\d)(?:\s*[,.]?\s*(?:conforme|$))", texto_item, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    def extrair_produto(texto_item: str) -> str:
        delim = r"(?:registro\s+(?:n[º°])?|para\s+(?:a\s+)?marca\s+comercial|conforme\s+processo|processo)"
        padroes = [
            re.compile(r"(?:do|no)\s+produto\s+(?:formulado\s+)?(.+?)\s*,\s*" + delim, re.IGNORECASE),
            re.compile(r"(?:do|no)\s+registro\s+(?:do|dos)\s+produto(?:s)?\s+(.+?)\s*,\s*" + delim, re.IGNORECASE),
            re.compile(r"inclus[ãa]o\s+do\s+produto\s+t[ée]cnico\s+(.+?)\s*,\s*" + delim, re.IGNORECASE),
            re.compile(r"produto\s+(?:formulado\s+)?(.+?)\s*,\s*(?:" + delim + r")", re.IGNORECASE),
        ]
        for padrao in padroes:
            match = padrao.search(texto_item)
            if match:
                nome = match.group(1).strip()
                nome = re.sub(r"^\s*(?:FORMULADO\s+)?T[ÉE]CNICO\s+", "", nome, flags=re.IGNORECASE).strip()
                nome = re.sub(r"\s+", " ", nome)
                return nome
        return ""

    def extrair_descricao_mudanca(texto_item: str) -> str:
        texto_limpo = re.sub(r"\s+", " ", texto_item)
        texto_u = texto_limpo.upper()
        palavras_chave = [
            "ALTERACAO",
            "ALTERA" + "\u00c7\u00c3" + "O",
            "INCLUSAO",
            "INCLUS" + "\u00c3" + "O",
            "EXCLUSAO",
            "EXCLUS" + "\u00c3" + "O",
            "TRANSFERENCIA",
            "TRANSFER" + "\u00ca" + "NCIA",
            "AUTORIZAMOS", "CANCELAMOS",
        ]
        melhor_pos = len(texto_limpo)
        for palavra in palavras_chave:
            pos = texto_u.find(palavra)
            if pos != -1 and pos < melhor_pos:
                melhor_pos = pos
        if melhor_pos < len(texto_limpo):
            fim = texto_limpo.find(", conforme", melhor_pos)
            if fim == -1:
                fim = texto_limpo.find(", registro", melhor_pos)
            if fim == -1:
                fim = texto_limpo.find(", processo", melhor_pos)
            if fim == -1:
                fim = texto_limpo.find(" n", melhor_pos + 50)
            if fim == -1:
                fim = texto_limpo.find(".", melhor_pos + 50)
            if fim == -1:
                fim = len(texto_limpo)
            desc = texto_limpo[melhor_pos:fim].strip().rstrip(",").strip()
            if "autorizamos" in desc.lower() and len(desc) > 60:
                desc = desc[:60] + "..."
            return desc
        return ""

    def extrair_artigo_inciso(texto_item: str) -> str:
        match = re.search(r"(Art\.\s*\d+[^,]*?)(?:,|$)", texto_item, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def verificar_filtro(categoria: str, tipo: str) -> bool:
        config = MATRIZ_FILTROS.get(categoria)
        if not config:
            return False
        tipo_key = tipo.lower().replace("ção", "cao").replace("ão", "ao")
        if tipo_key == "exclusão":
            tipo_key = "exclusao"
        if tipo_key == "inclusão":
            tipo_key = "inclusao"
        if tipo_key == "alteração":
            tipo_key = "alteracao"
        return config.get(tipo_key, False)

    resultados = []
    for item in items_raw:
        categoria = classificar_categoria(item["texto"])
        tipo = classificar_tipo(item["texto"])
        registro = extrair_registro(item["texto"])
        processo = extrair_processo(item["texto"])
        produto = extrair_produto(item["texto"])
        artigo = extrair_artigo_inciso(item["texto"])
        filtro_ativo = verificar_filtro(categoria, tipo)

        descricao = extrair_descricao_mudanca(item["texto"])

        resultados.append({
            "numero": item["numero"],
            "categoria": categoria,
            "tipo_mudanca": tipo,
            "registro": registro,
            "processo": processo,
            "produto": produto,
            "mudanca": descricao,
            "artigo_inciso": artigo,
            "filtro_ativo": filtro_ativo,
        })

    atos[0]["itens_filtrados"] = resultados
    return resultados


def salvar_dados_estruturados(atos: list, retificacoes: list, caminho_excel: str):
    from openpyxl import Workbook
    if not atos:
        return

    itens = atos[0].get("itens_filtrados", [])
    campos = ["numero", "status_filtro", "categoria", "tipo_mudanca",
              "registro", "produto", "mudanca", "processo", "artigo_inciso"]

    wb = Workbook()

    # --- Aba 1: Passaram ---
    ws_filtro = wb.active
    ws_filtro.title = "Passaram"
    ws_filtro.append(campos)
    for item in itens:
        if item.get("filtro_ativo"):
            row = [item.get(c, "") for c in campos]
            row[campos.index("status_filtro")] = "PASSOU"
            ws_filtro.append(row)

    # --- Aba 2: Todos ---
    ws_todos = wb.create_sheet("Todos")
    ws_todos.append(campos)
    for item in itens:
        row = [item.get(c, "") for c in campos]
        row[campos.index("status_filtro")] = "PASSOU" if item.get("filtro_ativo") else "IGNORADO"
        ws_todos.append(row)

    wb.save(caminho_excel)
