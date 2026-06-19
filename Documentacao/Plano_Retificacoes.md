# Plano para Identificação de Retificações

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
