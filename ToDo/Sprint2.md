# Sprint 2 - Extração de ATOS do DSV/CGAA

## Objetivo
Baixar o PDF da Seção 1 do DOU dinamicamente e extrair os ATOS do Departamento de Sanidade Vegetal e Insumos Agrícolas / Coordenação-Geral de Agrotóxicos e Afins.

## Implementado

### `src/dou_scraper.py`
- **`extrair_url_pdf_secao1(destino_pdf)`** (linha 90)
  - Usa Playwright com stealth mode para burlar o Azion WAF
  - Navega ate `in.gov.br/leiturajornal`, clica "DIARIO COMPLETO"
  - Extrai URL do PDF da Secao 1 da pagina de resultados
  - Faz o download do PDF via `expect_download` (mantem cookies de sessao)
  - Retorna `(sucesso, caminho_ou_erro, url_do_pdf)`

- **`extrair_atos_do_pdf(caminho_pdf)`** (linha 168)
  - Abre PDF com PyMuPDF (fitz)
  - Normaliza texto (remove \n, uppercase) para busca exata
  - Procura o titulo: "DEPARTAMENTO DE SANIDADE VEGETAL E INSUMOS AGRICOLAS COORDENACAO-GERAL DE AGROTOXICOS E AFINS"
  - Se encontrar, extrai ATOS dessa pagina ate o proximo ministerio
  - Para ao detectar mudanca de ministerio (ex: "Ministerio da Ciencia...")
  - Acumula ATOS multi-pagina (texto continuo entre paginas)
  - Retorna `(sucesso, lista_de_atos, mensagem_amigavel)`

### `src/main.py`
- Fluxo em 4 etapas com mensagens amigaveis em portugues
- `executar()`: acesso DOU -> download PDF -> extracao ATOS -> log
- Modo offline: `--pdf <caminho>` para processar PDF existente
- Salva ATOS em `.json` e `.txt` ao lado do PDF

### `src/logger.py`
- Novos campos: `pdf_baixado` (bool), `atos_encontrados` (int), `atos_info` (str)

### Aprendizados
- `download.in.gov.br` exige tokens `arg1`/`arg2` vinculados a sessao do browser
- `requests` nao consegue baixar mesmo com cookies copiados
- Playwright `expect_download` + `page.goto` funciona para capturar o PDF
- Titulo do DSV pode ter \n entre linhas no PDF - necessario normalizar
- PyMuPDF extrai caracteres especiais como U+FFFD (substituto)
- Regex de ministerio precisa capturar "das" (ex: "Ministerio das Comunicacoes")

## Pendente / Proxima Sprint

### Identificacao de Retificacoes

**Implementado (parcial):**
- **Retificações Diretas**: DETECTADAS com sucesso. Padrão "Onde se lê... Leia-se..." na seção DSV/CGAA. Função `extrair_retificacoes_do_pdf()` em `src/dou_scraper.py:245`.

**NÃO implementado corretamente:**
- **Retificações Indiretas**: A detecção atual pega "cancelamos o registro" e "tornamos sem efeito" que são ATOS normais do DSV, não retificações. 
- **O que é retificação indireta**: Correção de erro em ato anterior do próprio DSV/CGAA (ex: "Retifica-se o Ato nº X do DSV publicado no DOU de...", "Errata: No Ato do CGAA...").
- **Problema**: Qualquer "cancelamos" ou "tornamos sem efeito" no PDF está sendo classificado como retificação indireta, mas são apenas ATOS administrativos de cancelamento de registro.

**Output atual:**
```json
{
  "atos_dsv": [...],
  "retificacoes": [
    {
      "tipo": "direta",
      "onde_se_le": "...",
      "leia_se": "...",
      "pagina": 12,
      "descricao": "..."
    },
    {
      "tipo": "indireta",
      "subtipo": "cancelar registro",
      "ato_original": "DECRETO Nº 4074",
      "texto": "cancelamos o registro do produto...",
      "pagina": 9,
      "descricao": "..."
    }
  ]
}
```

**O que falta para retificações indiretas:**
1. Filtrar apenas para a seção DSV/CGAA
2. Detectar padrões como: "Retifica-se o Ato", "Errata", "Correção de publicação"
3. NÃO detectar: "cancelamos o registro", "tornamos sem efeito" (são ATOS, não retificações)

**Detalhes:** ver `Documentacao/Plano_Retificacoes.md`

---

- [ ] Testar em GitHub Actions (Playwright + Chromium precisa ser instalado)
- [x] Documentar cron-job.org em `Documentacao/CronJob.md`
