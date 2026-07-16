# Sprint 3 — Filtros, Retificações e Relatório

## Período
- Início: 22/06/2026
- Término: 16/07/2026 (estendida por bloqueio no acesso ao Veeva)

## Objetivo da Sprint
Aplicar filtros nos ATOS do DSV/CGAA para identificar mudanças relevantes, tratar retificações diretas e indiretas, gerar relatório PDF e enviar por e-mail.

---

## Entregas

### 1. Filtros nos ATOS (`aplicar_filtros_atos`)
- Parseia cada item numerado do ATO com padrão `"N. De Acordo com o Art."`
- Classifica cada item por categoria (Fabricantes, Formuladores, Marca comercial, etc.)
- Classifica por tipo de mudança (Inclusão, Alteração, Exclusão)
- Extrai registro, processo, produto e artigo/inciso
- Verifica se o item passa pela `MATRIZ_FILTROS`
- Testado com dados reais: **150 itens encontrados, 44 passaram pelo filtro**

**MATRIZ_FILTROS implementada:**

| Categoria | Inclusão | Alteração | Exclusão |
|-----------|:--------:|:---------:|:--------:|
| Fabricantes | ✅ | ✅ | ✅ |
| Formuladores | ✅ | ✅ | ✅ |
| Manipuladores | ✅ | ✅ | ✅ |
| Marca comercial | ✅ | ✅ | ✅ |
| Razão social | ✅ | ✅ | ✅ |
| Produto técnico no formulado | ✅ | ✅ | ✅ |
| Formulação | ✅ | ✅ | ✅ |
| Endereço | — | ✅ | — |
| Transferência de titularidade | — | ✅ | — |
| Retificações no DOU | — | ✅ | — |

### 2. Retificações Diretas (`tratar_retificacoes_diretas`)
- Classifica retificação por categoria e tipo de mudança
- Extrai número de registro, processo e produto
- Aplica correção (ONDE SE LÊ → LEIA-SE) no texto do ATO
- Detecta referência a edições anteriores via "NO DOU DE dd/mm/aaaa"
- Testado: 8 retificações, 5 aplicadas no ATO atual, 3 referenciam edições anteriores

### 3. Retificações Referenciadas (`processar_retificacoes_referenciadas`)
- Baixa PDF de edições anteriores do DOU via Playwright
- Extrai o ATO do DSV/CGAA da edição original
- Aplica a correção ONDE SE LÊ → LEIA-SE no texto da edição original
- Armazena `texto_original` e `texto_corrigido` no JSON de saída

### 4. Retificações Indiretas (`extrair_retificacoes_indiretas_do_pdf`)
- Segunda passada independente em todas as páginas do PDF
- Busca seções "RETIFICAÇÕES" / "ERRATA" independente da posição no PDF
- Detecta padrões: "Retifica-se o Ato nº X do DSV", "Errata: No Ato nº Y do CGAA", etc.
- Filtra para mencionar apenas DSV ou CGAA
- Ignora falsos positivos: CANCELAMOS, TORNAMOS SEM EFEITO, REVOGAMOS
- Output com `tipo: "indireta"`, `ato_original`, `data_original`, `texto`, `pagina`

### 5. Armazenamento (`salvar_dados_estruturados`, `salvar_atos_json`)
- Excel com `openpyxl`: abas "Passaram" (filtro ativo) e "Todos" (completo)
- JSON estruturado com ATOS + retificações
- TXT legível com separadores visuais
- Todos salvos em `downloads/` com data no nome do arquivo

### 6. Relatório PDF (`src/relatorio.py`)
- Gerado com `fpdf2`
- Página 1: cabeçalho, status colorido (verde/amarelo/vermelho), resumo, contagem por categoria
- Páginas seguintes: detalhamento DE/PARA de cada mudança relevante
- Seção de retificações com ONDE SE LÊ / LEIA-SE formatados
- Salvo em `downloads/DD_MM_AAAA Relatorio da execucao da DOU.pdf`

### 7. Envio por E-mail (`src/email_sender.py`)
- Suporte a Gmail e Outlook (auto-detecta pelo domínio do SMTP_USER)
- 3 tipos de e-mail: `sucesso` (com anexos), `sem_atos`, `sem_dou`
- Anexos: relatório PDF, PDF original do DOU, Excel de filtragem
- Tratamento de e-mail muito grande: remove o maior anexo e reenvia
- Credenciais via `.env`: `SMTP_USER` e `SMTP_PASS`

### 8. Log Estruturado (`src/logger.py`)
17 campos no JSONL de log:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `data_hora` | str | Timestamp da execução |
| `status` | str | SUCESSO / FALHA / PARCIAL |
| `erro` | str | Mensagem de erro se houver |
| `info` | str | Resumo textual da execução |
| `pdf_baixado` | bool | Se o PDF foi baixado nesta execução |
| `atos_encontrados` | int | Quantidade de ATOs do DSV/CGAA |
| `dsv_encontrado` | bool | Se o DSV foi encontrado no PDF |
| `retificacoes_encontradas` | int | Total de retificações diretas |
| `retificacoes_indiretas` | int | Total de retificações indiretas |
| `retificacoes_tratadas` | int | Retificações processadas |
| `retificacoes_aplicadas` | int | Correções aplicadas no ATO atual |
| `retificacoes_referenciadas` | int | Retificações que referenciam DOU anterior |
| `cabecalho_ato` | str | Título do ATO encontrado |
| `itens_por_categoria` | dict | Contagem de itens por categoria (filtro ativo) |
| `itens_filtrados` | int | Itens que passaram pelo filtro |
| `itens_total` | int | Total de itens no ATO |
| `atos_info` | str | Mensagem da extração de ATOs |

---

## Fluxo Completo do Robô (8 etapas)

```
[1/8] Verificar site do DOU           → acessar_dou()
[2/8] Baixar PDF da Seção 1           → extrair_url_pdf_secao1()
[3/8] Procurar ATOS do DSV/CGAA       → extrair_atos_do_pdf()
[4/8] Aplicar filtros nos itens        → aplicar_filtros_atos()
[5/8] Procurar retificações no PDF     → extrair_retificacoes_do_pdf()
                                         extrair_retificacoes_indiretas_do_pdf()
[6/8] Tratar retificações diretas      → tratar_retificacoes_diretas()
[7/8] Processar retificações referenciadas → processar_retificacoes_referenciadas()
[8/8] Gerar relatório e enviar e-mail  → gerar_relatorio() + enviar_relatorio()
```

---

## Novas Dependências

| Pacote | Versão | Finalidade |
|--------|--------|------------|
| `fpdf2` | 2.8.1 | Geração do relatório PDF |
| `openpyxl` | 3.1.2 | Geração do Excel de filtragem |
| `python-dotenv` | 1.0.1 | Carrega `.env` com credenciais SMTP |

---

## Arquivos de Saída

| Arquivo | Conteúdo |
|---------|---------|
| `downloads/secao1_YYYY_MM_DD.pdf` | PDF original do DOU |
| `downloads/secao1_YYYY_MM_DD.json` | ATOS + retificações (estruturado) |
| `downloads/secao1_YYYY_MM_DD.txt` | ATOS + retificações (legível) |
| `downloads/filtragem_dos_itens_da_dou_DD_MM_AAAA.xlsx` | Excel com itens filtrados |
| `downloads/DD_MM_AAAA Relatorio da execucao da DOU.pdf` | Relatório PDF final |

---

## Aprendizados Técnicos

1. **Retificações ficam fora do bloco do DSV**: a seção "RETIFICAÇÕES" fica no final do PDF, após todos os ministérios. Necessário segunda passada independente.
2. **Falsos positivos**: "CANCELAMOS O REGISTRO" e "TORNAMOS SEM EFEITO" são ATOs normais do DSV, não retificações. Regex de exclusão necessária.
3. **ONDE SE LÊ multi-página**: o par pode estar dividido entre páginas — necessário concatenar texto antes de buscar o padrão.
4. **Retificações referenciadas**: o LEIA-SE pode conter "NO DOU DE dd/mm/aaaa" — indica que a correção é para uma edição anterior, necessário baixar e reprocessar aquela edição.
5. **openpyxl não estava em requirements.txt**: era importado em `dou_scraper.py` sem estar declarado na dependência — corrigido.

---

## Próximos Passos (Sprint 4)

- [ ] Mapear colunas do export do Veeva (aguarda arquivo de exemplo)
- [ ] Implementar comparação DOU x Veeva por registro/produto
- [ ] Fluxo de aprovação: e-mail com divergências para revisão humana
- [ ] Robô grava alterações aprovadas no Veeva via automação
- [ ] Log de auditoria das alterações realizadas no Veeva
- [ ] Documentação para stakeholders
