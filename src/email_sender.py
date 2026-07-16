import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

DESTINATARIOS = ["vinicius.camargo@syngenta.com"]


def _detectar_smtp(email: str):
    dominio = email.split("@")[-1].lower()
    if dominio in ("gmail.com", "googlemail.com"):
        return "smtp.gmail.com", 587
    return "smtp.office365.com", 587


def _listar_anexos(pdf_relatorio, pdf_original, caminho_excel):
    anexos = [
        ("Relatorio PDF (mudancas)", pdf_relatorio),
        ("PDF original do DOU", pdf_original),
        ("Excel - Filtragem dos itens", caminho_excel),
    ]
    return [(nome, path) for nome, path in anexos if os.path.exists(path)]


def _montar_msg(usuario, destino, assunto, corpo, anexos):
    msg = MIMEMultipart()
    msg["From"] = usuario
    msg["To"] = destino
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain", "utf-8"))
    for nome, path in anexos:
        with open(path, "rb") as f:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(f.read())
        encoders.encode_base64(parte)
        nome_arq = os.path.basename(path)
        parte.add_header("Content-Disposition", f'attachment; filename="{nome_arq}"')
        msg.attach(parte)
    return msg


def _enviar(usuario, senha, destino, msg):
    smtp_host, smtp_port = _detectar_smtp(usuario)
    serv = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
    serv.ehlo()
    serv.starttls()
    serv.ehlo()
    serv.login(usuario, senha)
    serv.sendmail(usuario, [destino], msg.as_string())
    serv.quit()


def _corpo_email(data_display, status, anexos, pdf_original_excluido=False):
    if status == "sem_atos":
        lines = [
            f"ROBO DOU - Execucao de {data_display}\n",
            "=" * 50 + "\n\n",
            "O Ato relacionado ao MFO nao esta presente na DOU.\n\n",
        ]
    elif status == "sem_dou":
        lines = [
            f"ROBO DOU - Execucao de {data_display}\n",
            "=" * 50 + "\n\n",
            "Nao houve DOU publicada no dia de hoje.\n\n",
        ]
    else:
        lines = [
            f"ROBO DOU - Relatorio de Execucao de {data_display}\n",
            "=" * 50 + "\n\n",
            "A automacao foi executada com sucesso.\n",
            "Segue em anexo o relatorio com as mudancas identificadas.\n\n",
        ]

    if anexos:
        lines.append("Anexos deste email:\n")
        for i, (nome, _) in enumerate(anexos, 1):
            lines.append(f"  {i}. {nome}\n")

    if pdf_original_excluido:
        lines.append(
            "\n  * O PDF original do DOU nao foi anexado por exceder o limite de tamanho do email.\n"
            f"    Para consulta-lo, acesse https://www.in.gov.br/leitura-do-diario-oficial\n"
            f"    e busque pela Secao 1 da data {data_display}.\n"
        )

    if status == "sem_atos" or status == "sem_dou":
        lines.append(
            "\nProxima execucao agendada para o proximo horário.\n"
        )

    lines.append("\nAtt,\nROBO DOU")
    return "".join(lines)


def enviar_email_texto(data_display: str, status: str):
    usuario = os.environ.get("SMTP_USER")
    senha = os.environ.get("SMTP_PASS")
    if not usuario or not senha:
        print("  [ERR] SMTP_USER e SMTP_PASS nao definidos no .env")
        return False

    destino = DESTINATARIOS[0]
    prefixo_map = {"sem_atos": " [SEM DADOS]", "sem_dou": " [SEM DOU]"}
    prefixo = prefixo_map.get(status, "")
    assunto = f"ROBO DOU - Relatorio de Execucao{prefixo} - {data_display}"
    corpo = _corpo_email(data_display, status, [])
    msg = _montar_msg(usuario, destino, assunto, corpo, [])
    try:
        _enviar(usuario, senha, destino, msg)
        print("  [OK] Email enviado (somente texto)")
        return True
    except Exception as e:
        print(f"  [ERR] Falha ao enviar email: {e}")
        return False


def enviar_relatorio(pdf_relatorio: str, pdf_original: str, caminho_excel: str,
                     data_display: str):
    usuario = os.environ.get("SMTP_USER")
    senha = os.environ.get("SMTP_PASS")
    if not usuario or not senha:
        print("  [ERR] SMTP_USER e SMTP_PASS nao definidos no .env")
        return False

    destino = DESTINATARIOS[0]
    assunto = f"ROBO DOU - Relatorio de Execucao - {data_display}"

    anexos = _listar_anexos(pdf_relatorio, pdf_original, caminho_excel)
    corpo = _corpo_email(data_display, "sucesso", anexos)
    msg = _montar_msg(usuario, destino, assunto, corpo, anexos)

    try:
        _enviar(usuario, senha, destino, msg)
        print("  [OK] Email enviado com todos os anexos")
        return True
    except Exception as e:
        erro_str = str(e)
        if "size limits" in erro_str.lower() or "552" in erro_str or "message too large" in erro_str.lower():
            print(f"  [AVISO] Anexos excedem limite de tamanho ({len(anexos)} arquivos). Removendo maiores...")
            anexos_ordenados = sorted(anexos, key=lambda x: os.path.getsize(x[1]), reverse=True)
            for i in range(1, len(anexos_ordenados)):
                anexos_reduzidos = anexos_ordenados[i:]
                excluiu_pdf = any("PDF original" in a[0] for a in anexos_ordenados[:i])
                corpo2 = _corpo_email(data_display, "sucesso", anexos_reduzidos, pdf_original_excluido=excluiu_pdf)
                msg2 = _montar_msg(usuario, destino, assunto, corpo2, anexos_reduzidos)
                try:
                    _enviar(usuario, senha, destino, msg2)
                except:
                    continue
                excluidos = [a[0] for a in anexos_ordenados[:i]]
                for nome_excl in excluidos:
                    print(f"    (excluido: {nome_excl} - mantido localmente em downloads/)")
                print(f"  [OK] Email enviado com {len(anexos_reduzidos)} anexos")
                return True
            print(f"  [ERR] Nao foi possivel enviar email mesmo apos remover anexos: {e}")
        else:
            print(f"  [ERR] Falha ao enviar email: {e}")
        return False
