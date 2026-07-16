## Sprint 4 — Integração Veeva e Ciclo Completo

### Meta
Implementar a comparação DOU x Veeva, fluxo de aprovação humana, execução automática das alterações no Veeva pelo robô e documentação para stakeholders.

---

## Contexto e Estratégia

**Acesso ao Veeva:** liberado em 16/07/2026.

**Estratégia definida:**
1. Veeva gera export nativo (Excel/CSV) com cadastro atual
2. Robô lê o arquivo e compara com os dados do DOU
3. Robô envia e-mail com divergências encontradas para aprovação humana
4. Humano revisa e aprova/rejeita cada alteração
5. **Robô executa as alterações aprovadas no Veeva via automação**
6. Robô registra log de auditoria de tudo que foi alterado

**Por que o robô faz as alterações (não humano):** volume de dados pode ser grande, tornando a atualização manual inviável.

---

## To Clarify

### 1. Mapeamento de colunas do export do Veeva ⏳
Precisamos de um arquivo de exemplo (Excel/CSV) exportado do Veeva com os campos relevantes:
- Número de registro
- Nome do produto / marca comercial
- Fabricante(s)
- Formulador(es)
- Endereço
- Razão social
- Produto técnico no formulado

*Aguarda arquivo de exemplo para definir mapeamento exato de colunas.*

### 2. Mecanismo de aprovação ⏳
Definir como o humano aprova/rejeita alterações:
- Por e-mail (botão de confirmação / resposta)?
- Por arquivo Excel (coluna de aprovação)?
- Por interface web simples?

### 3. Como o robô acessa o Veeva para gravar ⏳
Definir mecanismo de escrita no Veeva:
- API REST do Veeva Vault?
- Automação de interface (Playwright no Veeva)?
- Import de arquivo via funcionalidade nativa?

### 4. Destinatários por tipo de mudança ⏳
Definir quem recebe o e-mail de divergências de acordo com o tipo:
- Fabricantes / Formuladores → time regulatório
- Marca comercial → time de marketing / produto
- Endereço / Razão social → time jurídico / cadastro

### 5. Evidências para auditoria ⏳
Definir quais registros devem ser mantidos:
- Screenshot da publicação no DOU?
- Texto original vs. alterado?
- Aprovador e data/hora da aprovação?

---

## To Do

### 1. Ler e mapear export do Veeva
Implementar `veeva_reader.py` (novo módulo):
- Ler arquivo Excel/CSV exportado do Veeva
- Normalizar colunas (registro, produto, fabricante, etc.)
- Retornar dicionário indexado por número de registro

### 2. Implementar comparação DOU x Veeva (`veeva_comparator.py`)
- Cruzar itens filtrados do DOU com registros do Veeva por número de registro
- Identificar divergências por campo:
  - `novo_no_dou`: item presente no DOU mas não no Veeva
  - `alterado`: campo com valor diferente entre DOU e Veeva
  - `excluido_no_dou`: item presente no Veeva mas excluído no DOU
- Retornar lista de divergências estruturada

### 3. Enriquecer e-mail de resultado com divergências DOU x Veeva
Estender `email_sender.py`:
- Tabela de divergências no corpo do e-mail:
  `Registro | Campo | Valor atual (Veeva) | Novo valor (DOU) | Ação sugerida`
- Cada linha com opção de aprovação/rejeição
- Anexar Excel de divergências para revisão offline

### 4. Fluxo de aprovação
Implementar mecanismo para o humano indicar quais alterações aprovar:
- Definição final depende do To Clarify #2
- Excel com coluna "Aprovado (S/N)" como opção mais simples

### 5. Robô aplica alterações aprovadas no Veeva
Implementar `veeva_writer.py` (novo módulo):
- Ler resposta de aprovação
- Para cada alteração aprovada: executar a escrita no Veeva
- Mecanismo a definir (To Clarify #3)

### 6. Log de auditoria das alterações no Veeva
Adicionar ao `logger.py`:
- `veeva_divergencias`: total de divergências encontradas
- `veeva_aprovadas`: total de alterações aprovadas
- `veeva_aplicadas`: total de alterações efetivamente gravadas no Veeva
- `veeva_rejeitadas`: total de alterações rejeitadas pelo humano

### 7. Criar lógica de reinício do ciclo
Garantir que o robô está pronto para a próxima execução:
- Limpeza de arquivos temporários após envio
- Reset de estado para nova execução

### 8. Documentar funcionamento para stakeholders
Criar `Documentacao/Guia_Stakeholders.md` com:
- O que o robô faz e quando roda
- Como interpretar o e-mail recebido
- Como aprovar/rejeitar alterações
- Como verificar o histórico de execuções

---

## In Progress

- (Aguarda arquivo de exemplo do Veeva para iniciar itens 1 e 2)

---

## Review

### 1. Validar comparação DOU x Veeva
Confirmar que as divergências identificadas são corretas.

### 2. Validar fluxo de aprovação
Confirmar que o mecanismo de aprovação é prático para o usuário.

### 3. Validar escrita no Veeva
Confirmar que as alterações aprovadas são gravadas corretamente.

### 4. Validar log de auditoria
Confirmar que todas as alterações realizadas ficam registradas.

### 5. Testar fluxo ponta a ponta
DOU → filtro → comparação Veeva → aprovação → escrita Veeva → relatório → e-mail.

---

## Done

- (Preencher conforme evolução da sprint)
