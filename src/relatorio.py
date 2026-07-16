import re
from datetime import datetime
from fpdf import FPDF


class RelatorioPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "ROBO DOU - Relatorio de Mudancas em Cadastros", align="C")
        self.ln(8)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")


def _norm(s):
    return s.lower().replace("ç", "c").replace("ã", "a").replace("á", "a").replace("à", "a") \
        .replace("ê", "e").replace("é", "e").replace("è", "e") \
        .replace("ó", "o").replace("õ", "o").replace("ô", "o") \
        .replace("í", "i").replace("ú", "u").replace("ü", "u")


def extrair_de_para(item: dict) -> dict:
    desc = item.get("mudanca", "")
    cat = item["categoria"]
    tipo_norm = _norm(item["tipo_mudanca"])
    desc_norm = _norm(desc)
    produto = item.get("produto", "")
    registro = item.get("registro", "")

    de = ""
    para = ""

    is_alteracao = tipo_norm == "alteracao"
    is_inclusao = tipo_norm == "inclusao"
    is_exclusao = tipo_norm == "exclusao"
    cat_norm = _norm(cat)
    
    ctx_prod = f" | Produto: {produto}" if produto else ""
    ctx_reg = f" | Registro: {registro}" if registro else ""

    def texto_apos(desc, padrao):
        m = re.search(padrao, desc)
        return m.group(1).strip().rstrip("., ") if m else ""

    if "marca comercial" in cat_norm and is_alteracao:
        de = f"Marca atual: {produto}{ctx_reg}" if produto else desc[:120]
        para = texto_apos(desc, r"para\s+marca\s+comercial\s+(.+?)(?:\.|$)")
        if para:
            para = f"Nova marca: {para}"
        elif "exclus" in desc_norm:
            para = "Item alterado tambem contem exclusao de alvos/culturas (ver descricao completa)"

    elif "marca comercial" in cat_norm and is_inclusao:
        de = f"Produto base: {produto}{ctx_reg}" if produto else "Antes: nao constava"
        para = texto_apos(desc, r"inclus[ãa]o\s+da\s+marca\s+comercial\s+(.+?)\s*,")
        if para:
            para = f"Marca incluida: {para}"
        else:
            para = desc[:200]

    elif "marca comercial" in cat_norm and is_exclusao:
        if "alvo" in desc_norm or "cultura" in desc_norm:
            de = desc[:200] + "..."
            para = "(exclusao de alvos biologicos e/ou culturas)"
        else:
            de = texto_apos(desc, r"exclus[ãa]o\s+(?:da|de)\s+marca\s+comercial\s+(.+?)\s*,")
            if not de:
                de = desc[:150]
            para = "(marca comercial excluida do registro)"

    elif "endere" in cat_norm and is_alteracao:
        m_de = re.search(r"endere[ço]o\s+(.+?)\s+para\s+o\s+endere[ço]o", desc)
        m_para = re.search(r"para\s+o\s+endere[ço]o\s+(.+?)(?:,?\s*esta\s*altera|$)", desc)
        de = m_de.group(1).strip() if m_de else desc[:200]
        de = f"Endereco antigo: {de}"
        para = m_para.group(1).strip() if m_para else desc[:200]
        para = f"Novo endereco: {para}"

    elif "transfer" in cat_norm and is_alteracao:
        m_de = re.search(r"da\s+empresa\s+(.+?)(?:,|\s+sito)", desc)
        m_para = re.search(r"para\s+a\s+empresa\s+(.+?)(?:,|\s+sito|\s+esta\s+transfer)", desc)
        titulares = ""
        if produto:
            titulares = f"Produtos transferidos: {produto}\n"
        de = f"{titulares}Titular anterior: {m_de.group(1).strip()}" if m_de else desc[:200]
        para = f"Novo titular: {m_para.group(1).strip()}" if m_para else desc[:200]

    elif "formula" in cat_norm and is_alteracao:
        de = f"Produto: {produto}{ctx_reg}" if produto else desc[:150]
        para = f"Alteracao de formulacao: {desc[:250]}"

    elif is_inclusao:
        if "fabricante" in desc_norm or "formulador" in desc_norm:
            incluido = texto_apos(desc, r"inclus[ãa]o\s+(?:do\s+fabricante|do\s+formulador|dos\s+formuladores|de\s+fabricante/formulador)\s+(.+?)\s*,")
            de = f"Produto afetado: {produto}{ctx_reg}" if produto else desc[:120]
            if incluido:
                restante = ""
                m_resto = re.search(re.escape(incluido) + r"(.+?)(?:no\s+produto|registro\s+n)", desc, re.IGNORECASE)
                if m_resto:
                    restante = m_resto.group(1).strip().rstrip(",").lstrip(",").strip()
                resto = f", {restante}" if restante else ""
                para = f"Inclusao de: {incluido.rstrip(',')}{resto}"
        elif "produto tecnico" in desc_norm:
            incluido = texto_apos(desc, r"inclus[ãa]o\s+do\s+produto\s+t[ée]cnico\s+(.+?)\s*,")
            m_destino = re.search(r"no\s+produto\s+formulado\s+(.+?)\s*,", desc)
            destino = m_destino.group(1).strip() if m_destino else ""
            de = f"Formulado afetado: {destino}" if destino else f"Produto tecnico adicionado a formulados"
            if incluido:
                m_resto = re.search(re.escape(incluido) + r"(.+?)(?:no\s+produto|registro\s+n)", desc, re.IGNORECASE)
                restante = m_resto.group(1).strip().rstrip(",").lstrip(",").strip() if m_resto else ""
                resto = f", {restante}" if restante else ""
                para = f"Produto tecnico incluido: {incluido.rstrip(',')}{resto}"
        else:
            de = f"Produto: {produto}{ctx_reg}" if produto else desc[:120]
            para = desc[:300]
        if not para:
            para = desc[:300]

    elif is_exclusao:
        if "fabricante" in desc_norm or "formulador" in desc_norm:
            excluido = texto_apos(desc, r"(?:exclus[ãa]o\s+do\s+fabricante|exclus[ãa]o\s+do\s+formulador|exclus[ãa]o\s+dos\s+formuladores|autorizamos\s+a\s+empresa)\s+(.+?)(?:\s*,|\s+CNPJ)")
            de = f"Excluido: {excluido}" if excluido else desc[:200]
            para = f"Produto afetado: {produto}{ctx_reg}" if produto else "(exclusao)"
        else:
            de = desc[:200] + "..."
            para = "(exclusao)"
        if not de:
            de = desc[:200]

    else:
        de = desc[:200] if desc else ""
        para = ""

    return {"de": de or "-", "para": para or "-", "descricao": desc}


def gerar_relatorio(atos: list, itens_filtrados: list, retificacoes_tratadas: list,
                    caminho_pdf: str, status_geral: str = "executado"):
    pdf = RelatorioPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    cabecalho_ato = atos[0].get("cabecalho", "") if atos else "N/A"
    data_exec = datetime.now().strftime("%d/%m/%Y %H:%M")

    qtd_filtro = sum(1 for i in itens_filtrados if i.get("filtro_ativo"))
    qtd_total = len(itens_filtrados)
    qtd_ret = len(retificacoes_tratadas)
    qtd_ret_aplicadas = sum(1 for r in retificacoes_tratadas if r.get("correcao_aplicada"))

    # ===== PAGINA 1: CABECALHO =====
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    tem_dados = qtd_filtro > 0 or qtd_ret > 0
    pdf.set_text_color(26, 82, 118)
    pdf.cell(0, 10, "Relatorio de Execucao - ROBO DOU", align="C")
    pdf.ln(14)

    status_label = status_geral.upper()
    if not atos:
        status_label = "SEM ATOS DO DSV/CGAA"
        cor_status = (180, 60, 60)
    elif not tem_dados:
        status_label = "EXECUTADO - SEM MUDANCAS RELEVANTES"
        cor_status = (180, 140, 20)
    else:
        cor_status = (50, 150, 50)
    pdf.set_fill_color(*cor_status)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, f"  {status_label}", fill=True)
    pdf.ln(10)

    pdf.set_text_color(50, 50, 50)
    info = [
        ("Data/Hora", data_exec),
        ("ATO", cabecalho_ato),
    ]
    for label, value in info:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 7, label + ":")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, value)
        pdf.ln(7)

    pdf.ln(5)

    # ===== RESUMO =====
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 82, 118)
    pdf.cell(0, 8, "Resumo", align="L")
    pdf.ln(10)

    pdf.set_text_color(50, 50, 50)
    resumo_items = [
        ("Total de itens no ATO", str(qtd_total)),
        ("Mudancas relevantes", str(qtd_filtro)),
        ("Ignorados pelo filtro", str(qtd_total - qtd_filtro)),
    ]
    if qtd_ret:
        resumo_items.append(("Retificacoes encontradas", str(qtd_ret)))
        resumo_items.append(("Correcoes aplicadas", str(qtd_ret_aplicadas)))

    for label, value in resumo_items:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(80, 7, "  " + label)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, value, align="R")
        pdf.ln(7)

    # ===== CATEGORIAS =====
    pdf.ln(5)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 82, 118)
    pdf.cell(0, 8, "Itens por Categoria", align="L")
    pdf.ln(10)

    cat_counts = {}
    for item in itens_filtrados:
        if item["filtro_ativo"]:
            cat = item["categoria"]
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    for cat, qtd in sorted(cat_counts.items(), key=lambda x: -x[1]):
        pdf.cell(100, 6, f"  {cat}")
        pdf.cell(0, 6, str(qtd), align="R")
        pdf.ln(6)

    # ===== DETALHAMENTO DE/PARA =====
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 82, 118)
    pdf.cell(0, 10, "Detalhamento das Mudancas (DE / PARA)", align="L")
    pdf.ln(12)

    itens_para_mostrar = [i for i in itens_filtrados if i["filtro_ativo"]]

    if not itens_para_mostrar:
        if not atos:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(180, 60, 60)
            pdf.cell(0, 10, "NENHUM ATO DO DSV/CGAA ENCONTRADO NESTA EDICAO", align="C")
            pdf.ln(8)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 6, (
                "O ROBO DOU verificou o Diario Oficial da Uniao desta data, "
                "mas nao localizou nenhum Atodo Departamento de Sanidade Vegetal "
                "e Insumos Agricolas / CGAA relacionado ao MFO.\n\n"
                "Possiveis motivos:\n"
                "  - Nao houve publicacao de agrotoxicos e afins nesta data\n"
                "  - O DOU pode ainda nao estar disponivel para esta data\n"
                "  - Houve uma falha na extracao do conteudo\n\n"
                "Nenhum relatorio de mudancas foi gerado."
            ))
        else:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(180, 140, 20)
            pdf.cell(0, 10, "ATENCAO: Nenhuma mudanca relevante apos aplicar o filtro MFO", align="C")
            pdf.ln(8)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 6, (
                f"Foram encontrados {qtd_total} itens no ATO, mas todos foram "
                f"classificados como fora do escopo MFO (ignorados pelo filtro). "
                f"Nenhuma mudanca relevante para reportar."
            ))
    else:
        for idx, item in enumerate(itens_para_mostrar, 1):
            dp = extrair_de_para(item)

            if pdf.get_y() > 240:
                pdf.add_page()

            # Categoria header
            pdf.set_fill_color(240, 245, 250)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(26, 82, 118)
            cat_label = f"{item['categoria']} ({item['tipo_mudanca']})"
            if item.get("registro"):
                cat_label += f" | Reg: {item['registro']}"
            if item.get("produto"):
                cat_label += f" | {item['produto']}"
            pdf.cell(0, 7, f"  #{idx}  {cat_label}", fill=True)
            pdf.ln(8)

            # DE
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(200, 50, 50)
            pdf.cell(0, 5, "DE:")
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(50, 50, 50)
            pdf.set_x(20)
            pdf.multi_cell(170, 5, dp["de"])

            # PARA
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(50, 150, 50)
            pdf.cell(0, 5, "PARA:")
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(50, 50, 50)
            pdf.set_x(20)
            pdf.multi_cell(170, 5, dp["para"])

            pdf.ln(3)

    # ===== RETIFICACOES =====
    if retificacoes_tratadas:
        if pdf.get_y() > 220:
            pdf.add_page()
        pdf.ln(3)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(26, 82, 118)
        pdf.cell(0, 8, "Retificacoes", align="L")
        pdf.ln(10)

        for ret in retificacoes_tratadas:
            if pdf.get_y() > 235:
                pdf.add_page()
            cat = ret.get("categoria", "?")
            tipo_ret = ret.get("tipo_mudanca", "?")
            reg = ret.get("registro", "") or ret.get("processo", "")
            prod = ret.get("produto", "")
            data_ref = ret.get("data_dou_referenciada", "")
            ref_str = f" [ref: DOU {data_ref}]" if data_ref else ""
            status_c = "APLICADA" if ret.get("correcao_aplicada") else "REFERENCIADA"
            onde_se_le = ret.get("onde_se_le", "")
            leia_se = ret.get("leia_se", "")

            # Header
            pdf.set_fill_color(250, 240, 240)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(180, 60, 60)
            pdf.cell(0, 6, f"  [{status_c}] {cat} ({tipo_ret}) | {reg} | {prod}{ref_str}", fill=True)
            pdf.ln(7)

            if onde_se_le and leia_se:
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(200, 50, 50)
                pdf.cell(0, 4, "  ONDE SE LE:")
                pdf.ln(4)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(50, 50, 50)
                pdf.set_x(15)
                pdf.multi_cell(175, 4, onde_se_le.strip("., ")[:300])

                pdf.ln(1)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(50, 150, 50)
                pdf.cell(0, 4, "  LEIA-SE:")
                pdf.ln(4)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(50, 50, 50)
                pdf.set_x(15)
                pdf.multi_cell(175, 4, leia_se.strip("., ")[:300])
                pdf.ln(3)
            else:
                desc_ret = ret.get("descricao", "")
                if desc_ret:
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(100, 100, 100)
                    pdf.set_x(15)
                    pdf.multi_cell(175, 4, desc_ret[:250])
                    pdf.ln(3)

    # Save
    pdf.output(caminho_pdf)
    return caminho_pdf
