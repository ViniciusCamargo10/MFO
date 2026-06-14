import requests

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


def acessar_dou() -> tuple[bool, str]:
    try:
        response = requests.get(DOU_URL, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return True, "DOU acessado com sucesso"
        else:
            return False, f"DOU retornou status {response.status_code}"
    except requests.RequestException as e:
        return False, f"Erro ao acessar DOU: {e}"
