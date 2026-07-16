import sys
import os
import json
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.logger import registrar_execucao
from src.dou_scraper import (
    acessar_dou,
    extrair_url_pdf_secao1,
    extrair_atos_do_pdf,
    extrair_retificacoes_do_pdf,
    tratar_retificacoes_diretas,
    processar_retificacoes_referenciadas,
    aplicar_filtros_atos,
    salvar_dados_estruturados,
    DOWNLOAD_DIR,
)
from src.relatorio import gerar_relatorio
from src.email_sender import enviar_relatorio, enviar_email_texto
from src.scheduler import configurar, iniciar
from src.logger import LOG_FILE


def salvar_atos_json(atos: list, retificacoes: list, caminho_pdf: str):
    base = os.path.splitext(caminho_pdf)[0]
    caminho_json = base + ".json"
    caminho_txt = base + ".txt"
    dados = {
        "atos_dsv": atos,
        "retificacoes": retificacoes,
    }
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    with open(caminho_txt, "w", encoding="utf-8") as f:
        if atos:
            f.write("=" * 60 + "\n")
            f.write("ATOS DO DSV/CGAA\n")
            f.write("=" * 60 + "\n\n")
            for ato in atos:
                f.write("-" * 60 + "\n")
                f.write(f"{ato['cabecalho']}\n")
                f.write(f"Pagina inicial: {ato['pagina_inicio']}\n")
                f.write("-" * 60 + "\n")
                f.write(ato["texto"] + "\n\n")
        if retificacoes:
            f.write("=" * 60 + "\n")
            f.write("RETIFICACOES\n")
            f.write("=" * 60 + "\n\n")
            for ret in retificacoes:
                f.write("-" * 60 + "\n")
                f.write(f"Pagina: {ret['pagina']}\n")
                f.write(f"Tipo: {ret['tipo']}\n")
                f.write(f"{ret['descricao']}\n\n")
    return caminho_json, caminho_txt


def _notificar_sem_dou(data_display: str):
    enviar_email_texto(data_display, status="sem_dou")


def executar(pdf_path_override: str = ""):
    data_str = datetime.now().strftime("%Y_%m_%d")
    data_display = datetime.now().strftime("%d/%m/%Y")
    data_arq = datetime.now().strftime("%d_%m_%Y")
    pdf_path = pdf_path_override or os.path.join(DOWNLOAD_DIR, f"secao1_{data_str}.pdf")
    url_pdf = ""

    print("=" * 50)
    print(f"  ROBÔ DOU - Execucao de {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50)

    if pdf_path_override:
        m_data = re.search(r"(\d{4})_(\d{2})_(\d{2})", pdf_path_override)
        if m_data:
            data_arq = f"{m_data.group(3)}_{m_data.group(2)}_{m_data.group(1)}"
            data_display = f"{m_data.group(3)}/{m_data.group(2)}/{m_data.group(1)}"
        print(f"\n  Modo offline: processando PDF existente")
        print(f"  Arquivo: {pdf_path_override}")
    else:
        print("\n[1/4] Verificando site do DOU...")
        sucesso, mensagem = acessar_dou()
        if not sucesso:
            registrar_execucao(status="FALHA", erro=mensagem, dsv_encontrado=False, retificacoes_encontradas=0)
            print(f"  ERRO: {mensagem}")
            _notificar_sem_dou(data_display)
            return
        print(f"  {mensagem}")

        print("\n[2/4] Buscando o Diario Oficial de hoje...")
        sucesso, resultado, url_pdf = extrair_url_pdf_secao1(destino_pdf=pdf_path)
        if not sucesso:
            registrar_execucao(
                status="FALHA",
                erro=resultado,
                info=f"acesso dou ok | url: {url_pdf[:100] if url_pdf else 'n/a'}",
                dsv_encontrado=False,
                retificacoes_encontradas=0,
            )
            print(f"  ERRO: {resultado}")
            _notificar_sem_dou(data_display)
            return
        print(f"  PDF salvo em: {resultado}")

    print("\n[3/8] Procurando por ATOS do DSV/CGAA no PDF...")
    sucesso, atos, mensagem_atos = extrair_atos_do_pdf(pdf_path)
    if not sucesso:
        atos = []
        mensagem_atos = "Nenhum ATO do DSV/CGAA encontrado."
    print(f"  {mensagem_atos}")

    print("\n[4/8] Aplicando filtros nos itens do ATO...")
    itens_filtrados = aplicar_filtros_atos(atos) if atos else []
    qtd_filtro_ativo = sum(1 for i in itens_filtrados if i.get("filtro_ativo"))
    print(f"  {len(itens_filtrados)} item(ns) encontrados, {qtd_filtro_ativo} passaram pelo filtro")
    if itens_filtrados:
        for item in itens_filtrados[:5]:
            status = "[FILTRO]" if item["filtro_ativo"] else "[IGNORADO]"
            print(f"    #{item['numero']} {status} | {item['categoria']} ({item['tipo_mudanca']}) | {item.get('registro', '-')} | {item.get('produto', '-')}")
        if len(itens_filtrados) > 5:
            print(f"    ... +{len(itens_filtrados)-5} item(ns)")

    print("\n[5/8] Procurando por RETIFICACOES no PDF...")
    sucesso_ret, retificacoes, mensagem_retificacoes = extrair_retificacoes_do_pdf(pdf_path)
    if not sucesso_ret:
        retificacoes = []
        mensagem_retificacoes = "Nenhuma retificacao encontrada."
    print(f"  {mensagem_retificacoes}")

    print("\n[6/8] Tratando retificacoes diretas...")
    retificacoes_tratadas = tratar_retificacoes_diretas(atos, retificacoes)
    qtd_aplicadas = sum(1 for r in retificacoes_tratadas if r.get("correcao_aplicada"))
    qtd_referenciadas = sum(1 for r in retificacoes_tratadas if r.get("data_dou_referenciada"))
    print(f"  {len(retificacoes_tratadas)} retificacao(oes) tratada(s), {qtd_aplicadas} correcao(oes) aplicada(s) ao ATO atual")
    if qtd_referenciadas:
        print(f"  {qtd_referenciadas} retificacao(oes) referenciam edicoes anteriores do DOU")

    if qtd_referenciadas and not pdf_path_override:
        print(f"\n[7/8] Processando retificacoes referenciadas (buscando edicoes anteriores)...")
        retificacoes_referenciadas = processar_retificacoes_referenciadas(retificacoes_tratadas)
        qtd_ref_aplicadas = sum(1 for r in retificacoes_referenciadas if r.get("correcao_aplicada_referencia"))
        print(f"  {qtd_ref_aplicadas}/{qtd_referenciadas} correcoes aplicadas nas edicoes referenciadas")
        for ret in retificacoes_referenciadas:
            if ret.get("data_dou_referenciada"):
                status = "[OK]" if ret.get("correcao_aplicada_referencia") else "[ERR]"
                erro = ret.get("referencia_erro", "")
                if erro:
                    print(f"    {status} DOU {ret['data_dou_referenciada']} | ERRO: {erro[:80]}")
                else:
                    print(f"    {status} DOU {ret['data_dou_referenciada']} | {ret.get('referencia_cabecalho', '?')[:60]}")
        retificacoes_tratadas = retificacoes_referenciadas
    elif qtd_referenciadas:
        print(f"\n[7/8] Modo offline: pulando download das edicoes referenciadas")
        for ret in retificacoes_tratadas:
            if ret.get("data_dou_referenciada"):
                print(f"    [OFFLINE] DOU {ret['data_dou_referenciada']} (pulado)")

    dsv_encontrado = len(atos) > 0
    retificacoes_encontradas = len(retificacoes)
    cabecalho_ato = atos[0].get("cabecalho", "") if atos else ""

    cat_counts = {}
    if itens_filtrados:
        for item in itens_filtrados:
            if item["filtro_ativo"]:
                cat = item["categoria"]
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

    info_parts = []
    info_parts.append("[OK] DOU acessado")
    if dsv_encontrado:
        cab = atos[0].get("cabecalho", "")[:80]
        info_parts.append(f"[OK] ATO: Pag {atos[0]['pagina_inicio']} - {cab}")
        if itens_filtrados:
            info_parts.append(f"[OK] {qtd_filtro_ativo}/{len(itens_filtrados)} itens filtrados")
            for cat, qtd in sorted(cat_counts.items(), key=lambda x: -x[1]):
                info_parts.append(f"     {cat}: {qtd}")
    else:
        info_parts.append("[ERR] DSV/CGAA NAO encontrado")
    if retificacoes_encontradas > 0:
        info_parts.append(f"[OK] Retificacoes: {retificacoes_encontradas} encontradas, {qtd_aplicadas} aplicadas")
        if qtd_referenciadas:
            ref_ok = sum(1 for r in retificacoes_tratadas if r.get("correcao_aplicada_referencia"))
            info_parts.append(f"     {ref_ok}/{qtd_referenciadas} referenciadas")
    else:
        info_parts.append("[OK] Sem retificacoes")

    info_str = " | ".join(info_parts)
    tem_dados = bool(atos or retificacoes_tratadas)

    if not tem_dados:
        print(f"\n  Nenhum dado MFO encontrado. Enviando notificacao por email...")
        enviar_email_texto(data_display, status="sem_atos")
    else:
        print(f"\n[8/8] Gerando relatorio e enviando por email...")
        caminho_json, caminho_txt = salvar_atos_json(atos, retificacoes_tratadas, pdf_path)
        caminho_excel = os.path.join(DOWNLOAD_DIR, f"filtragem_dos_itens_da_dou_{data_arq}.xlsx")
        if tem_dados:
            salvar_dados_estruturados(atos, retificacoes_tratadas, caminho_excel)
        caminho_pdf_rel = os.path.join(DOWNLOAD_DIR, f"{data_arq} Relatorio da execucao da DOU.pdf")
        gerar_relatorio(atos, itens_filtrados or [], retificacoes_tratadas, caminho_pdf_rel)
        print(f"  PDF relatorio:  {caminho_pdf_rel}")
        print(f"  Enviando relatorio por email...")
        enviar_relatorio(caminho_pdf_rel, pdf_path, caminho_excel, data_display)
    print(f"  {mensagem_atos}")
    if retificacoes_tratadas:
        print(f"  {mensagem_retificacoes}")
    print(f"\nSalvando dados...")
    print(f"Registrando execucao...")
    status_log = "SUCESSO" if tem_dados else "PARCIAL"
    erro_log = "" if tem_dados else "Nenhum ATO nem retificacao encontrados"
    registrar_execucao(
        status=status_log,
        erro=erro_log,
        info=info_str,
        pdf_baixado=not pdf_path_override,
        atos_encontrados=len(atos),
        atos_info=mensagem_atos,
        dsv_encontrado=dsv_encontrado,
        retificacoes_encontradas=retificacoes_encontradas,
        retificacoes_info=mensagem_retificacoes,
        cabecalho_ato=cabecalho_ato,
        itens_por_categoria=cat_counts,
        itens_filtrados=qtd_filtro_ativo,
        itens_total=len(itens_filtrados) if itens_filtrados else 0,
        retificacoes_tratadas=len(retificacoes_tratadas),
        retificacoes_aplicadas=qtd_aplicadas,
        retificacoes_referenciadas=qtd_referenciadas,
    )
    print("\n" + "-" * 40)
    if tem_dados:
        print(f"Arquivos gerados:")
        print(f"  JSON:   {caminho_json}")
        print(f"  TXT:    {caminho_txt}")
        print(f"  Excel:  {caminho_excel}")
    print("\nResumo:")
    if tem_dados:
        print(f"  {len(atos)} ATO(s) do DSV/CGAA")
        if itens_filtrados:
            print(f"  {len(itens_filtrados)} item(ns) no ATO, {qtd_filtro_ativo} passaram pelo filtro:")
            cat_counts = {}
            for item in itens_filtrados:
                if item["filtro_ativo"]:
                    cat = item["categoria"]
                    cat_counts[cat] = cat_counts.get(cat, 0) + 1
            for cat, qtd in sorted(cat_counts.items(), key=lambda x: -x[1]):
                print(f"    {cat}: {qtd}")
        if retificacoes_tratadas:
            print(f"  {len(retificacoes_tratadas)} Retificacao(oes) tratada(s)")
            print(f"  {qtd_aplicadas} correcao(oes) aplicada(s) ao texto do ATO atual")
            if qtd_referenciadas:
                qtd_ref_ok = sum(1 for r in retificacoes_tratadas if r.get("correcao_aplicada_referencia"))
                print(f"  {qtd_ref_ok}/{qtd_referenciadas} correcao(oes) aplicada(s) em edicoes referenciadas")
            for ret in retificacoes_tratadas[:5]:
                cat = ret.get("categoria", "?")
                tipo = ret.get("tipo_mudanca", "?")
                reg = ret.get("registro", "") or ret.get("processo", "")
                prod = ret.get("produto", "")
                data_ref = ret.get("data_dou_referenciada", "")
                ref_str = f" [ref: DOU {data_ref}]" if data_ref else ""
                print(f"    Pag {ret['pagina']} | {cat} ({tipo}) | {reg} | {prod}{ref_str}")
        for ato in atos[:10]:
            print(f"  Pag {ato['pagina_inicio']}: {ato['cabecalho']}")
        if len(atos) > 10:
            print(f"  ... e mais {len(atos) - 10} ATO(s)")
    else:
        print("  Nenhum ATO do DSV/CGAA nem retificacao encontrados nesta edicao.")
    print("-" * 40)
    print("\n" + "=" * 50)
    print("  Execucao finalizada com sucesso!")
    print("=" * 50)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--manual":
            executar()
            return
        if sys.argv[1] == "--pdf" and len(sys.argv) > 2:
            executar(pdf_path_override=sys.argv[2])
            return

    configurar(lambda: executar())
    print(f"Agendador iniciado. Horarios: {', '.join(['08:00', '16:00'])}")
    iniciar()


if __name__ == "__main__":
    main()
