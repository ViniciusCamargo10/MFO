## Sprint 3 — 22/06 a 26/06

### Meta
Fazer o robô verificar mudanças nos cadastros comparando DOU vs Cadastro, aplicar filtros e tratar retificação direta.

---

## To Clarify

### 1. Confirmar quais campos serão usados para comparação ⏳ (postergado)
Definir quais campos do Veeva serão utilizados para comparação entre dados do DOU e cadastro interno.
*Postergado — aguardando acesso ao Veeva para definir mapeamento.*

### 2. Confirmar quais mudanças são relevantes ✅ (definido)
Definir quais tipos de alteração devem ser consideradas como impacto no processo.

**Motivos relevantes — matriz completa:**

| Categoria | Inclusão | Alteração | Exclusão | Onde pegamos | Veeva? | Ação |
|-----------|:--------:|:---------:|:--------:|-------------|:------:|------|
| Fabricantes | ✅ | ✅ | ✅ | DOU | ✅ | Compara com Veeva |
| Formuladores | ✅ | ✅ | ✅ | DOU | ✅ | Compara com Veeva |
| Manipuladores | ✅ | ✅ | ✅ | DOU | ✅ | Compara com Veeva |
| Marca comercial | ✅ | ✅ | ✅ | DOU | ✅ | Compara com Veeva |
| Razão social | ✅ | ✅ | ✅ | DOU | ✅ | Compara com Veeva |
| Produto técnico no formulado | ✅ | ✅ | ✅ | DOU | ✅ | Compara com Veeva |
| Endereço | — | ✅ | — | DOU | ❌ | Detecta no DOU e reporta |
| Qualiquanti | — | ❓ | — | DOU | ❌ | Aguardando |
| Transferência de titularidade | — | ✅ | — | DOU | ❌ | Detecta no DOU e reporta |
| Retificações no DOU | — | ✅ | — | DOU (ONDE SE LE / LEIA-SE) | ✅ | Compara com Veeva |

### 3. Confirmar se filtro por palavra-chave (AGRO/MFO) atende ou precisa de complemento ✅ (resolvido)
O robô busca pelo DSV/CGAA no PDF (`DEPARTAMENTO DE SANIDADE VEGETAL E INSUMOS AGRICOLAS / COORDENACAO-GERAL DE AGROTOXICOS E AFINS`). Filtro está correto e funciona.

### 4. Confirmar comportamento quando não houver mudança em cadastro ✅ (definido)
Decisão: **Registrar no log com status apropriado e encerrar o fluxo** — mesma abordagem dos demais pontos de "não" no fluxo.  

### 5. Confirmar exemplos de retificação direta ✅ (definido)
Retificação direta = par "ONDE SE LE / LEIA-SE" extraído do PDF. O robô aplica a alteração diretamente no cadastro. Exemplos reais já disponíveis nos PDFs baixados.

---

## To Do

### 1. Criar regra DOU x Cadastro ⏳ (dependente)
Desenvolver a lógica para comparar os dados publicados no DOU com os dados existentes no cadastro.
*Depende do To Clarify #1 (campos Veeva) — postergado até acesso ao Veeva.*

### 2. Criar cenário de mudança e não mudança ✅ (definido)
Comportamento definido:
- ✅ **Quando há mudança relevante** → segue no fluxo (armazenamento → relatório → comunicação)
- ✅ **Quando não há mudança** → registra no log e encerra (To Clarify #4)

### 3. Criar lógica de aplicação dos filtros ✅ (implementado)
Implementar a aplicação dos filtros para identificar mudanças relevantes conforme matriz definida (To Clarify #2).
- Função `aplicar_filtros_atos()` em `dou_scraper.py` — parseia cada item numerado do ATO
- Classifica por categoria (Fabricantes, Formuladores, etc.) e tipo (Inclusão, Alteração, Exclusão)
- Extrai registro, processo, produto e artigo/inciso
- Verifica se passa pelo filtro com base na `MATRIZ_FILTROS`
- Testado com dados reais: 150 itens encontrados, 44 ativos no filtro

### 4. Criar tratamento para retificação direta ✅ (implementado)
Implementar o tratamento quando a retificação (ONDE SE LE / LEIA-SE) altera diretamente o cadastro.
- Função `tratar_retificacoes_diretas()` em `dou_scraper.py` — classifica por categoria, extrai registro/produto/processo, aplica correção no texto do ATO
- Integrado ao fluxo do `main.py`

### 5. Criar armazenamento dos dados identificados
Salvar todas as mudanças e informações identificadas para uso posterior (relatório Sprint 4).

### 6. Registrar resultado no log
Registrar detalhadamente:
- Tipo de alteração  
- Se houve impacto  
- Resultado da análise  
- Qual motivo da matriz foi identificado  

---

## In Progress

- #5 Armazenamento dos dados identificados

---

## 🔍 Review

### 1. Testar caso com mudança relevante
Validar que o robô identifica corretamente uma alteração que deve seguir no fluxo.

### 2. Testar caso sem mudança relevante
Confirmar que o robô encerra corretamente quando não há diferença relevante.

### 3. Validar motivos de alteração
Confirmar se o robô consegue justificar corretamente a mudança identificada.

---

## Done

- #3 Aplicação dos filtros — implementado, testado com dados reais (150 itens, 44 ativos)
  - `aplicar_filtros_atos()` em `dou_scraper.py` — parseia ATO em itens, classifica por categoria/tipo, extrai dados, aplica matriz de filtros
- #4 Retificação direta — implementado, testado com dados reais (8 retificações, 5 correções no ATO atual + 3 referenciando edições anteriores)
  - `tratar_retificacoes_diretas()` — classifica por categoria, extrai dados, aplica correção
  - `extrair_data_dou_referenciada()` — detecta "NO DOU DE" no LEIA-SE
  - `extrair_url_pdf_secao1_por_data()` — baixa PDF de edição específica
  - `processar_retificacoes_referenciadas()` — aplica correção na edição original

---

## 📦 Retificação Indireta — AGUARDANDO EXEMPLO REAL para "Retifica-se o Ato nº X"

Aguardando exemplos reais de "Retifica-se o Ato nº X do DSV" ou "Errata: No Ato nº Y do CGAA" **sem** ONDE SE LE / LEIA-SE.

---

## ✅ Retificação Referenciada — IMPLEMENTADO (23/06)

Três retificações diretas encontradas que referenciam edições anteriores do DOU:

| # | Edição referenciada | Categoria | Registro |
|---|-------------------|-----------|----------|
| 1 | DOU de 23/10/2025 | Marca comercial | 34223 |
| 2 | DOU de 30/12/2025 | Recomendações de uso | 8499 |
| 3 | DOU de 18/02/2026 | Marca comercial | — |

**Funcionalidades implementadas:**
- ✅ Detecção automática de "NO DOU DE dd/mm/aaaa" no LEIA-SE
- ✅ Download da edição referenciada do DOU
- ✅ Extração do ATO do DSV/CGAA da edição original
- ✅ Aplicação da correção (ONDE SE LE → LEIA-SE) no texto original
- ✅ Armazenamento de `texto_original` (pré-correção) e `texto_corrigido` (pós-correção) da edição referenciada