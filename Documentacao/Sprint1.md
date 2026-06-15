# Sprint 1 — Base do Robô DOU

## Período
- **Início:** 14/06/2026
- **Término:** 14/06/2026

## Objetivo da Sprint
Construir a base estrutural do robô de monitoramento do DOU, incluindo agendamento, acesso ao site, registro de logs e deploy automatizado via GitHub Actions.

---

## Entregas

### 1. Estrutura do Projeto

```
MFO/
├── .github/workflows/dou_automation.yml   # Workflow CI/CD
├── Documentacao/                           # Documentação do projeto
│   └── Planejamento_da_automação.md
├── logs/                                   # Logs de execução
│   └── execucao.jsonl
├── src/
│   ├── __init__.py
│   ├── main.py                             # Ponto de entrada
│   ├── dou_scraper.py                      # Acesso ao DOU
│   ├── scheduler.py                        # Agendador local
│   └── logger.py                           # Sistema de logs
├── ToDo/                                   # Planejamento futuro
├── requirements.txt
└── .gitignore
```

### 2. Módulo de Acesso ao DOU (`src/dou_scraper.py`)

- Requisição HTTP ao site `https://www.in.gov.br/leiturajornal`
- Headers personalizados para evitar bloqueios
- Parsing HTML com BeautifulSoup + lxml
- Extração da **data da edição**
- Identificação das **seções disponíveis** (DO1, DO2, DO3)
- Contagem de **artigos por seção**
- Timeout configurável de 60 segundos
- Tratamento de erros de rede e HTTP

### 3. Agendador Local (`src/scheduler.py`)

- Agendamento para **08:00 e 16:00**
- Loop infinito com verificação a cada 30 segundos
- Útil para execução contínua em servidor local

### 4. Sistema de Logs (`src/logger.py`)

- Formato **JSONL** (JSON Lines)
- Registro por linha com: data_hora, status, erro, info
- Arquivo: `logs/execucao.jsonl`
- Modo append — acumula execuções sem sobrescrever

### 5. Ponto de Entrada (`src/main.py`)

Dois modos de execução:

| Modo | Comando | Comportamento |
|------|---------|---------------|
| Manual | `python src/main.py --manual` | Executa scraper uma vez e encerra |
| Agendado | `python src/main.py` | Entra em loop aguardando horário |

### 6. Deploy Automatizado (GitHub Actions)

- **Workflow:** `.github/workflows/dou_automation.yml`
- **Trigger:** Agendado (cron) e manual (`workflow_dispatch`)
- **Horários:** 08:00 e 16:00 BRT (11:00 e 19:00 UTC)
- **Passos:**
  1. Checkout do repositório
  2. Configuração do Python 3.12
  3. Instalação de dependências
  4. Execução do scraper (`python src/main.py --manual`)
  5. Upload do log como artefato

### 7. Versionamento (Git)

- Repositório criado no GitHub: `ViniciusCamargo10/MFO`
- Branch: `main`
- Commit inicial: `feat: Sprint 1 - base do robo DOU`

---

## Dependências

| Pacote | Versão | Finalidade |
|--------|--------|------------|
| requests | 2.32.3 | Requisições HTTP |
| schedule | 1.2.2 | Agendamento local |
| python-dateutil | 2.9.0.post0 | Manipulação de datas |
| beautifulsoup4 | 4.13.3 | Parsing HTML |
| lxml | 5.4.0 | Parser XML/HTML |

---

## Como Executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Modo manual (uma execução)
python src/main.py --manual

# Modo agendado (loop contínuo)
python src/main.py
```

---

## Estrutura do Log

```json
{"data_hora": "2026-06-14 23:49:38", "status": "SUCESSO", "erro": "", "info": "DOU acessado com sucesso | Edicao: 14/06/2026 | Seção 1 - DO1: 45 artigos"}
```

---

## Próximos Passos (Sprint 2)

- [ ] Extrair títulos e links individuais dos artigos
- [ ] Filtrar publicações por palavra-chave (AGRO/MFO)
- [ ] Identificar retificações diretas e indiretas
- [ ] Comparar publicações com cadastros existentes
- [ ] Gerar relatório estruturado
- [ ] Notificação por e-mail
