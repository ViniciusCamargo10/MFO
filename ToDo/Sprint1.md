## Sprint 1 — 10/06 a 14/06

### Meta
Criar a base inicial do robô para acessar o DOU nos horários definidos e registrar a execução.

---

## Done

### 1. Confirmar: fonte/URL oficial da DOU
✅ URL definida: `https://www.in.gov.br/leiturajornal`

### 2. Confirmar: regra de calendário da execução
✅ Execução todos os dias (agendamento via cron no GitHub Actions)

### 3. Confirmar: horários oficiais de execução (08:00 e 16:00)
✅ Horários definidos: 08:00 e 16:00 BRT (11:00 e 19:00 UTC)

### 4. Confirmar: onde o log será armazenado
✅ Log local em `logs/execucao.jsonl` + artefato no GitHub Actions

### 5. Confirmar quais informações precisam aparecer no log
✅ Campos implementados: data_hora, status, erro, info

### 6. Criar estrutura inicial do script
✅ Estrutura do projeto criada:
```
MFO/
├── .github/workflows/dou_automation.yml
├── Documentacao/
├── logs/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── dou_scraper.py
│   ├── scheduler.py
│   └── logger.py
├── ToDo/
├── requirements.txt
└── .gitignore
```

### 7. Criar função de acesso ao site da DOU
✅ `src/dou_scraper.py` — acessa DOU, extrai data, seções e quantidade de artigos

### 8. Criar lógica de agendamento
✅ `src/scheduler.py` — agendamento local para 08:00 e 16:00

### 9. Criar log de execução e tratamento de erro
✅ `src/logger.py` — registro em JSONL com data, status, erro e info

### 10. Execução inicial do script e validação básica do fluxo
✅ Script testado manualmente — acesso ao DOU com sucesso

### 11. Criar workflow do GitHub Actions
✅ `.github/workflows/dou_automation.yml` — execução automática 2x/dia + manual

---

## Review

### 1. Testar acesso da automação ao DOU
✅ Validado — DOU retorna 200 e dados são extraídos corretamente

### 2. Testar execução às 08:00 (GitHub Actions)
❌ Schedule do GitHub não funciona neste repo — contornado com cron-job.org

### 3. Testar execução às 16:00 (GitHub Actions)
✅ 08:00 funcionou via cron-job.org
✅ 16:00 configurado no cron-job.org

### 4. Validar log de execução
✅ Log testado — `logs/execucao.jsonl` registrando corretamente

---

## To Do (Próximas Sprints)

- [ ] Extrair títulos e links individuais dos artigos
- [ ] Filtrar publicações por palavra-chave (AGRO/MFO)
- [ ] Identificar retificações diretas e indiretas
- [ ] Comparar publicações com cadastros existentes
- [ ] Gerar relatório estruturado
- [ ] Notificação por e-mail