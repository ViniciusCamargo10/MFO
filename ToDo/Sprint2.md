## Sprint 2 — 15/06 a 19/06

### Meta
Realizar a leitura do DOU e identificar publicações relevantes (AGRO/MFO) ou a seção de Retificações.

---

## To Clarify

### 1. Confirmar: o que caracteriza uma publicação AGRO/MFO
Definir claramente os critérios que indicam se uma publicação do DOU é relevante para o processo MFO.

### 2. Confirmar: palavras-chave ou critérios de busca
Listar os termos que o robô deverá procurar na publicação do DOU (ex: AGRO, MFO, etc.).

### 3. Confirmar como identificar a seção de Retificações
Definir padrões, termos ou seções que indicam que a publicação contém uma retificação.

### 4. Confirmar campos que devem ser extraídos da publicação
Definir quais informações precisam ser capturadas para as próximas etapas:
- Título
- Conteúdo
- Data
- Seção

### 5. Confirmar comportamento quando não houver publicação relevante
Definir se o robô:
- Apenas registra no log  
- Ou também envia algum tipo de comunicação  

---

## To Do

### 1. Criar função para carregar publicação do dia
Desenvolver a lógica para acessar e carregar o conteúdo publicado no DOU na data da execução.

### 2. Criar lógica para buscar termos AGRO/MFO
Desenvolver o processo que identifica automaticamente os termos definidos dentro da publicação.

### 3. Criar identificação da seção de Retificações
Implementar a verificação para identificar se a publicação pertence à seção de retificações.

### 4. Criar identificação de publicação relevante
Definir a lógica para classificar se a publicação encontrada deve seguir no fluxo.

### 5. Criar cenário sem publicação relevante
Definir e implementar o comportamento quando nenhuma publicação relevante for encontrada.

### 6. Registrar resultado da leitura no log
Salvar no log:
- Se encontrou ou não publicação relevante  
- Resultado da execução  

---

## In Progress

- (Preencher conforme evolução da sprint)

---

## Review

### 1. Testar leitura com publicação real
Validar se o robô consegue acessar e ler corretamente uma publicação real do DOU.

### 2. Testar cenário com publicação AGRO/MFO
Confirmar que o robô identifica corretamente uma publicação relevante.

### 3. Testar cenário sem publicação relevante
Confirmar que o robô encerra corretamente quando não encontra conteúdo relevante.

### 4. Validar campos capturados
Verificar se os dados extraídos fazem sentido para as próximas etapas.

### 5. Organizar exemplos de teste
Preparar exemplos reais com e sem conteúdo relevante para validação.

---

## Done

- (Preencher conforme evolução da sprint)
