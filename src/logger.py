import json
import os
from datetime import datetime


LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "execucao.jsonl")


def registrar(
    data_hora: str,
    status: str,
    erro: str = "",
    info: str = "",
    pdf_baixado: bool = False,
    atos_encontrados: int = 0,
    atos_info: str = "",
    dsv_encontrado: bool = False,
    retificacoes_encontradas: int = 0,
    retificacoes_info: str = "",
    cabecalho_ato: str = "",
    itens_por_categoria: dict = None,
    itens_filtrados: int = 0,
    itens_total: int = 0,
    retificacoes_tratadas: int = 0,
    retificacoes_aplicadas: int = 0,
    retificacoes_referenciadas: int = 0,
    retificacoes_indiretas: int = 0,
):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        "data_hora": data_hora,
        "status": status,
        "erro": erro,
        "info": info,
        "pdf_baixado": pdf_baixado,
        "atos_encontrados": atos_encontrados,
        "atos_info": atos_info,
        "dsv_encontrado": dsv_encontrado,
        "retificacoes_encontradas": retificacoes_encontradas,
        "retificacoes_info": retificacoes_info,
        "cabecalho_ato": cabecalho_ato,
        "itens_por_categoria": itens_por_categoria,
        "itens_filtrados": itens_filtrados,
        "itens_total": itens_total,
        "retificacoes_tratadas": retificacoes_tratadas,
        "retificacoes_aplicadas": retificacoes_aplicadas,
        "retificacoes_referenciadas": retificacoes_referenciadas,
        "retificacoes_indiretas": retificacoes_indiretas,
    }
    entry = {k: v for k, v in entry.items() if v is not None and v != ""}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def registrar_execucao(
    status: str,
    erro: str = "",
    info: str = "",
    pdf_baixado: bool = False,
    atos_encontrados: int = 0,
    atos_info: str = "",
    dsv_encontrado: bool = False,
    retificacoes_encontradas: int = 0,
    retificacoes_info: str = "",
    cabecalho_ato: str = "",
    itens_por_categoria: dict = None,
    itens_filtrados: int = 0,
    itens_total: int = 0,
    retificacoes_tratadas: int = 0,
    retificacoes_aplicadas: int = 0,
    retificacoes_referenciadas: int = 0,
    retificacoes_indiretas: int = 0,
):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registrar(agora, status, erro, info, pdf_baixado, atos_encontrados, atos_info, dsv_encontrado, retificacoes_encontradas, retificacoes_info, cabecalho_ato, itens_por_categoria, itens_filtrados, itens_total, retificacoes_tratadas, retificacoes_aplicadas, retificacoes_referenciadas, retificacoes_indiretas)
