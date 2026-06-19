import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.logger import registrar_execucao
from src.dou_scraper import (
    acessar_dou,
    extrair_url_pdf_secao1,
    extrair_atos_do_pdf,
    extrair_retificacoes_do_pdf,
    DOWNLOAD_DIR,
)
from src.scheduler import configurar, iniciar


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


def executar(pdf_path_override: str = ""):
    data_str = datetime.now().strftime("%Y_%m_%d")
    pdf_path = pdf_path_override or os.path.join(DOWNLOAD_DIR, f"secao1_{data_str}.pdf")
    url_pdf = ""

    print("=" * 50)
    print(f"  ROBÔ DOU - Execucao de {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50)

    if pdf_path_override:
        print(f"\n  Modo offline: processando PDF existente")
        print(f"  Arquivo: {pdf_path_override}")
    else:
        print("\n[1/4] Verificando site do DOU...")
        sucesso, mensagem = acessar_dou()
        if not sucesso:
            registrar_execucao(status="FALHA", erro=mensagem, dsv_encontrado=False, retificacoes_encontradas=0)
            print(f"  ERRO: {mensagem}")
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
            return
        print(f"  PDF salvo em: {resultado}")

    print("\n[3/5] Procurando por ATOS do DSV/CGAA no PDF...")
    sucesso, atos, mensagem_atos = extrair_atos_do_pdf(pdf_path)
    if not sucesso:
        atos = []
        mensagem_atos = "Nenhum ATO do DSV/CGAA encontrado."
    print(f"  {mensagem_atos}")

    print("\n[4/5] Procurando por RETIFICACOES no PDF...")
    sucesso_ret, retificacoes, mensagem_retificacoes = extrair_retificacoes_do_pdf(pdf_path)
    if not sucesso_ret:
        retificacoes = []
        mensagem_retificacoes = "Nenhuma retificacao encontrada."
    print(f"  {mensagem_retificacoes}")

    dsv_encontrado = len(atos) > 0
    retificacoes_encontradas = len(retificacoes)
    cabecalho_ato = atos[0].get("cabecalho", "") if atos else ""

    info_parts = []
    info_parts.append("✅ DOU acessado com sucesso")
    if dsv_encontrado:
        info_parts.append(f"✅ DSV/CGAA encontrado ({len(atos)} ATO)")
        for ato in atos[:3]:
            cab = ato.get("cabecalho", "")[:120]
            info_parts.append(f"   📄 ATO: Pag {ato['pagina_inicio']} - {cab}")
        if len(atos) > 3:
            info_parts.append(f"   ... +{len(atos)-3} ATO(s)")
    else:
        info_parts.append("❌ DSV/CGAA NAO encontrado nesta edicao")
    if retificacoes_encontradas > 0:
        info_parts.append(f"✅ Retificacoes encontradas ({retificacoes_encontradas})")
        for ret in retificacoes[:5]:
            desc = ret.get("descricao", "")[:150]
            info_parts.append(f"   🔧 Pag {ret['pagina']} ({ret['tipo']}): {desc}")
        if retificacoes_encontradas > 5:
            info_parts.append(f"   ... +{retificacoes_encontradas-5} retificacao(oes)")
    else:
        info_parts.append("❌ Nenhuma retificacao encontrada")

    info_str = " | ".join(info_parts)

    if not atos and not retificacoes:
        registrar_execucao(
            status="PARCIAL",
            erro="Nenhum ATO nem retificacao encontrados",
            info=info_str,
            pdf_baixado=not pdf_path_override,
            atos_encontrados=0,
            dsv_encontrado=False,
            retificacoes_encontradas=0,
        )
        print("\n" + "=" * 50)
        print("  Execucao finalizada (sem ATOS nem retificacoes hoje)")
        print("=" * 50)
        return

    caminho_json, caminho_txt = salvar_atos_json(atos, retificacoes, pdf_path)
    print(f"  {mensagem_atos}")
    if retificacoes:
        print(f"  {mensagem_retificacoes}")
    print(f"\n[5/5] Registrando execucao...")
    registrar_execucao(
        status="SUCESSO",
        info=info_str,
        pdf_baixado=not pdf_path_override,
        atos_encontrados=len(atos),
        atos_info=mensagem_atos,
        dsv_encontrado=dsv_encontrado,
        retificacoes_encontradas=retificacoes_encontradas,
        retificacoes_info=mensagem_retificacoes,
        cabecalho_ato=cabecalho_ato,
    )
    print("\n" + "-" * 40)
    print(f"Arquivos gerados:")
    print(f"  JSON: {caminho_json}")
    print(f"  TXT:  {caminho_txt}")
    print("\nResumo:")
    print(f"  {len(atos)} ATO(s) do DSV/CGAA")
    if retificacoes:
        print(f"  {len(retificacoes)} Retificacao(oes)")
    for ato in atos[:10]:
        print(f"  Pag {ato['pagina_inicio']}: {ato['cabecalho']}")
    if len(atos) > 10:
        print(f"  ... e mais {len(atos) - 10} ATO(s)")
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
