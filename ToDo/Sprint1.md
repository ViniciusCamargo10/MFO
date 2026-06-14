## Sprint 1 — 08/06 a 12/06

### Meta
Criar a base inicial do robô para acessar o DOU nos horários definidos e registrar a execução.

---

## To Clarify

### 1. Confirmar: fonte/URL oficial da DOU
Definir qual página ou fonte oficial do DOU será usada pelo robô para iniciar a consulta.

### 2. Confirmar: regra de calendário da execução
Determinar se o robô será executado todos os dias, apenas em dias úteis ou em datas específicas.

### 3. Confirmar: horários oficiais de execução (08:00 e 16:00)
Definir claramente os horários em que o robô deve iniciar automaticamente.

### 4. Confirmar: onde o log será armazenado
Definir se o log será salvo em arquivo local, SharePoint, Microsoft Lists ou banco de dados.

### 5. Confirmar quais informações precisam aparecer no log
Definir quais campos o log deve conter:
- Data
- Horário
- Status
- Erro (se houver)
- Informações da execução

---

## To Do

### 1. Criar estrutura inicial do script
Montar a base do código da automação para organizar as próximas etapas do desenvolvimento.

### 2. Criar função de acesso ao site da DOU
Desenvolver a primeira função responsável por abrir e consultar a fonte oficial do DOU.

### 3. Criar lógica de agendamento
Programar o robô para iniciar automaticamente a consulta nos horários definidos.

### 4. Criar log de execução e tratamento de erro
Implementar o registro básico de execução contendo:
- Data
- Horário
- Status (sucesso/falha)
- Mensagem de erro (se ocorrer)

---

## In Progress

- Execução inicial do script e validação básica do fluxo

---

## Review

### 1. Testar acesso da automação ao DOU
Validar se o robô consegue acessar corretamente a fonte definida.

### 2. Testar execução simulada às 08:00
Verificar se a lógica de agendamento funciona para o primeiro horário.

### 3. Testar execução simulada às 16:00
Verificar se a lógica de agendamento funciona para o segundo horário.

### 4. Validar log de execução
Conferir se o log registra corretamente:
- Data
- Horário
- Status
- Resultado da execução

---

## Done

- (Preencher conforme evolução da sprint)