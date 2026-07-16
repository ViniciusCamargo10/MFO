# Plano para Identificação de Retificações

## Status

### Retificações Diretas — IMPLEMENTADO ✅
- Padrão "Onde se lê... Leia-se..." detectado com sucesso
- Função: `extrair_retificacoes_do_pdf()` em `src/dou_scraper.py:256`
- Filtra apenas para a seção DSV/CGAA (páginas entre título DSV e próximo ministério)
- Testado com PDF 09/03/2026: 8 retificações diretas encontradas

### Retificações Indiretas — IMPLEMENTADO ✅ (16/07/2026)
- Função: `extrair_retificacoes_indiretas_do_pdf()` em `src/dou_scraper.py`
- Segunda passada independente em todas as páginas do PDF
- Detecta seções "RETIFICAÇÕES" / "ERRATA" onde quer que apareçam no PDF
- Filtra apenas retificações que mencionam DSV ou CGAA
- Ignora falsos positivos: "CANCELAMOS O REGISTRO", "TORNAMOS SEM EFEITO", "REVOGAMOS"
- Integrada ao fluxo do `main.py` como sub-etapa da etapa [5/8]
- Campo `retificacoes_indiretas` adicionado ao log (`logger.py`)

---

## Como funciona cada tipo

### Retificação Direta
Encontrada **dentro** do bloco do DSV/CGAA. Traz explicitamente o par:
```
ONDE SE LÊ: <texto errado>
LEIA-SE: <texto correto>
```
O robô aplica a correção diretamente no texto do ATO.

### Retificação Indireta
Encontrada **fora** do bloco do DSV/CGAA, tipicamente na seção "RETIFICAÇÕES" no final do PDF. Referencia um ato anterior sem trazer o par ONDE SE LÊ / LEIA-SE.

**O que é retificação indireta:**
- "Retifica-se o Ato nº X do DSV publicado no DOU de..."
- "Errata: No Ato nº Y do CGAA..."
- "Correção: Na publicação do Ato nº Z..."
- "Corrigir a publicação do Ato do DSV..."

**O que NÃO é retificação indireta:**
- "Cancelamos o registro do produto X" → é ATO de cancelamento
- "Tornamos sem efeito o item Y" → é ATO de revogação
- "Revogamos a autorização Z" → é ATO de revogação

---

## Onde entra no fluxo

```
Etapa [5/8] — Procurando por RETIFICAÇÕES no PDF
  ├── extrair_retificacoes_do_pdf()         → retificações diretas (ONDE SE LÊ / LEIA-SE)
  └── extrair_retificacoes_indiretas_do_pdf() → retificações indiretas (referência a ato anterior)

Etapa [6/8] — Tratando retificações diretas
  └── tratar_retificacoes_diretas()         → classifica, extrai dados, aplica correção

Etapa [7/8] — Processando retificações referenciadas
  └── processar_retificacoes_referenciadas() → baixa edições antigas e aplica correções
```

---

## Output no JSON

```json
{
  "atos_dsv": [...],
  "retificacoes": [
    {
      "tipo": "direta",
      "onde_se_le": "...",
      "leia_se": "...",
      "pagina": 12,
      "descricao": "Onde se lê: \"...\" -> Leia-se: \"...\""
    },
    {
      "tipo": "indireta",
      "ato_original": "ATO Nº 39",
      "data_original": "09/03/2026",
      "texto": "Retifica-se o Ato nº 39 do DSV publicado no DOU de...",
      "pagina": 45,
      "em_secao_retificacoes": true,
      "descricao": "Retificacao indireta: ..."
    }
  ]
}
```

---

## Padrões para detectar retificações indiretas do DSV/CGAA

| Padrão | Exemplo | Regex |
|--------|---------|-------|
| "Retifica-se o Ato nº X" | "Retifica-se o Ato nº 39 do DSV publicado no DOU de..." | `RETIFICA-SE O ATO Nº \d+.*DSV\|CGAA` |
| "Errata" | "Errata: No Ato nº 49 do CGAA..." | `ERRATA: NO ATO Nº \d+.*DSV\|CGAA` |
| "Correção de publicação" | "Correção: Na publicação do Ato nº 45..." | `CORREÇÃO: NA PUBLICAÇÃO DO ATO Nº \d+.*DSV\|CGAA` |
| "Corrigir" | "Corrigir a publicação do Ato do DSV..." | `CORRIGIR A PUBLICAÇÃO DO ATO.*DSV\|CGAA` |

**NÃO detectar:**
- "Cancelamos o registro" → é ATO
- "Tornamos sem efeito" → é ATO
- "Revogamos" → é ATO

## Status

### Retificações Diretas — IMPLEMENTADO ✅
- Padrão "Onde se lê... Leia-se..." detectado com sucesso
- Função: `extrair_retificacoes_do_pdf()` em `src/dou_scraper.py:245`
- Filtra apenas para a seção DSV/CGAA (páginas entre título DSV e próximo ministério)
- Testado com PDF 09/03/2026: 8 retificações diretas encontradas

### Retificações Indiretas — NÃO IMPLEMENTADO ❌
**Problema atual:** A detecção pega "cancelamos o registro" e "tornamos sem efeito" que são ATOS normais do DSV, não retificações.

**O que é retificação indireta:**
Correção de erro em ato anterior do próprio DSV/CGAA. Exemplos:
- "Retifica-se o Ato nº X do DSV publicado no DOU de..."
- "Errata: No Ato nº Y do CGAA..."
- "Correção: Na publicação do Ato nº Z..."

**O que NÃO é retificação indireta:**
- "Cancelamos o registro do produto X" → é ATO de cancelamento
- "Tornamos sem efeito o item Y" → é ATO de revogação
- "Revogamos a autorização Z" → é ATO de revogação

---

## O que precisa ser feito (Retificações Indiretas)

### 1. Detectar se a seção "RETIFICAÇÕES" existe no PDF
- Procurar pelo título **"RETIFICAÇÕES"** no texto extraído (similar à lógica do DSV)
- Se encontrar, extrair o bloco de retificações

### 2. Diferenciar os tipos
- **Retificação Direta**: a correção está explícita no texto (ex: "Onde se lê..., leia-se...")
- **Retificação Indireta**: referencia outro ato/publicação anterior do DSV/CGAA para CORRIGIR erro

### 3. Extrair os dados da retificação
- Qual ato está sendo retificado
- O que mudou
- Data da publicação original

---

## Onde entra no fluxo atual

Atualmente nosso `extrair_atos_do_pdf()` busca o DSV/CGAA e para no próximo ministério. As retificações ficam **depois de todos os ministérios**, no final do PDF. Ou seja, com a lógica atual, nunca alcançamos a seção de retificações porque paramos no ministério seguinte ao DSV.

---

## Estratégia proposta

```
extrair_atos_do_pdf()
  ├── Buscar DSV/CGAA → extrair ATOS (já implementado)
  └── Buscar RETIFICAÇÕES → extrair retificações (novo)
```

Seria uma **segunda passada** no PDF, independente da primeira — procurando pelo título "RETIFICAÇÕES" em todas as páginas e extraindo o conteúdo daquela seção.

---

## Output esperado no JSON

```json
{
  "atos_dsv": [...],
  "retificacoes": [
    {
      "tipo": "direta",
      "onde_se_le": "...",
      "leia_se": "...",
      "pagina": 12,
      "descricao": "Onde se lê: \"...\" -> Leia-se: \"...\""
    },
    {
      "tipo": "indireta",
      "ato_original": "ATO Nº XXX",
      "data_original": "dd/mm/aaaa",
      "descricao": "Retifica-se o Ato nº X do DSV publicado no DOU de..."
    }
  ]
}
```

---

## Padrões para detectar retificações indiretas do DSV/CGAA

| Padrão | Exemplo |
|--------|---------|
| "Retifica-se o Ato nº X" | "Retifica-se o Ato nº 39 do DSV publicado no DOU de..." |
| "Errata" | "Errata: No Ato nº 49 do CGAA..." |
| "Correção de publicação" | "Correção: Na publicação do Ato nº 45..." |
| "Corrigir" | "Corrigir a publicação do Ato do DSV..." |

**NÃO detectar:**
- "Cancelamos o registro" → é ATO
- "Tornamos sem efeito" → é ATO
- "Revogamos" → é ATO
