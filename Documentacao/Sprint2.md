# Sprint 2 — Extração de ATOS do DSV/CGAA

## Período
- **Início:** 15/06/2026
- **Término:** 16/06/2026

## Objetivo da Sprint
Implementar a capacidade de baixar dinamicamente o PDF da Seção 1 do DOU e extrair os ATOS do Departamento de Sanidade Vegetal e Insumos Agrícolas / Coordenação-Geral de Agrotóxicos e Afins (DSV/CGAA).

---

## Entregas

### 1. Download Dinâmico do PDF (`extrair_url_pdf_secao1`)

- Navegação com **Playwright + stealth mode** para burlar Azion WAF
- Acesso a `in.gov.br/leiturajornal`, clique no botão "DIÁRIO COMPLETO"
- Extração da URL do PDF da Seção 1 da página de resultados
- Download via `expect_download` (mantém cookies de sessão do navegador)
- Aprendizado: tokens `arg1`/`arg2` são vinculados à sessão — `requests` não funciona mesmo com cookies copiados

### 2. Extração de ATOS do DSV (`extrair_atos_do_pdf`)

- Abertura do PDF com **PyMuPDF (fitz)**
- Normalização de texto (remove quebras de linha, uppercase) para busca exata
- Busca pelo título: `"DEPARTAMENTO DE SANIDADE VEGETAL E INSUMOS AGRICOLAS COORDENACAO-GERAL DE AGROTOXICOS E AFINS"`
- Se encontrado, extrai ATOS dessa página até o próximo ministério
- Detecta mudança de ministério via regex (ex: "Ministério das Comunicações")
- **Acumula ATOS multi-página** — texto contínuo entre páginas
- Gera saída em `.json` e `.txt` ao lado do PDF

### 3. Fluxo Principal (`src/main.py`)

- 4 etapas com mensagens amigáveis em português
- Modo **offline**: `python src/main.py --pdf <caminho>` para processar PDF existente
- Modo **manual**: `python src/main.py --manual` para execução única
- Modo **agendado**: `python src/main.py` para loop contínuo

### 4. Sistema de Logs (`src/logger.py`)

Novos campos adicionados:
- `pdf_baixado` (bool) — indica se o PDF foi baixado com sucesso
- `atos_encontrados` (int) — quantidade de ATOS extraídos
- `atos_info` (str) — mensagem descritiva sobre a extração

### 5. Agendador (`src/scheduler.py`)

- Horários corrigidos para `08:00` e `16:00`

### 6. Deploy (GitHub Actions)

Workflow atualizado em `.github/workflows/dou_automation.yml`:
- Instalação do Chromium via `playwright install chromium`
- Instalação de dependências de sistema via `playwright install-deps chromium`

### 7. Dependências

Novas dependências adicionadas ao `requirements.txt`:
| Pacote | Versão | Finalidade |
|--------|--------|------------|
| playwright | 1.60.0 | Automação de navegador (burla Azion WAF) |
| PyMuPDF | 1.27.2 | Leitura e extração de texto de PDFs |

---

## Como Executar

```bash
# Instalar dependências
pip install -r requirements.txt
playwright install chromium

# Modo manual (uma execução - baixa PDF de hoje)
python src/main.py --manual

# Modo offline (processar PDF existente)
python src/main.py --pdf "downloads/secao1_2026_06_15.pdf"

# Modo agendado (loop contínuo)
python src/main.py
```

---

## Estrutura de Saída

Para cada PDF processado, são gerados dois arquivos:

| Arquivo | Formato | Conteúdo |
|---------|---------|----------|
| `downloads/secao1_YYYY_MM_DD.json` | JSON | ATOS extraídos (estruturado) |
| `downloads/secao1_YYYY_MM_DD.txt` | Texto | ATOS extraídos (legível) |

### Exemplo JSON
```json
[{
  "cabecalho": "ATO Nº 34,",
  "pagina_inicio": 4,
  "texto": "ATO Nº 34,\nDE 29 DE MAIO DE 2026..."
}]
```

### Exemplo TXT
```
============================================================
ATO Nº 34,
Pagina inicial: 4
------------------------------------------------------------
ATO Nº 34,
DE 29 DE MAIO DE 2026
O Coordenador-Geral de Agrotóxicos e Afins...
```

---

## Estrutura do Log

```json
{"data_hora": "2026-06-16 12:47:23", "status": "SUCESSO", "erro": "", "info": "Total de 1 ATO(s) encontrado(s). | PDF: ...", "pdf_baixado": false, "atos_encontrados": 1, "atos_info": "Total de 1 ATO(s) encontrado(s)."}
```

---

## Aprendizados Técnicos

1. **Azion WAF**: bloqueia `requests` e até Playwright sem stealth — necessário `add_init_script` para esconder `navigator.webdriver`
2. **Tokens do PDF**: `arg1`/`arg2` são vinculados à sessão do navegador — download precisa ser feito no mesmo contexto do Playwright
3. **Normalização de texto**: PDF pode ter `\n` no meio do título do DSV — necessário substituir `\s+` por espaço antes de buscar
4. **Encoding**: PyMuPDF extrai caracteres especiais (º, ç, ã) como U+FFFD (substituto) — necessário upper() e comparação normalizada
5. **Ministérios**: regex precisa capturar variações como "das" (ex: "Ministério das Comunicações"), não apenas "da"

---

## Próximos Passos (Sprint 3)

- [x] **Identificação de Retificações Diretas** — Detectar padrão "Onde se lê... Leia-se..." na seção DSV/CGAA (IMPLEMENTADO)
- [ ] **Identificação de Retificações Indiretas** — ATENÇÃO: NÃO implementado corretamente. A detecção atual pega "cancelamos o registro" e "tornamos sem efeito" que são ATOS normais, não retificações. Retificação indireta deve ser apenas do DSV/CGAA e referenciar correção de erro em ato anterior (ex: "Retifica-se o Ato nº X do DSV", "Errata: No Ato do CGAA...")
- [ ] Testar execução completa no GitHub Actions
- [ ] Filtrar publicações por palavra-chave (AGRO/MFO)
- [ ] Comparar publicações com cadastros existentes
- [ ] Gerar relatório estruturado
- [ ] Notificação por e-mail
