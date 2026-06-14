## Sprint 3 — 22/06 a 26/06

### Meta
Fazer o robô verificar mudanças nos cadastros, aplicar filtros e tratar os dois tipos de retificação: direta e indireta.

---

## To Clarify

### 1. Confirmar quais campos serão usados para comparação
Definir quais campos do Veeva serão utilizados para comparação entre dados do DOU e cadastro interno.

### 2. Confirmar quais mudanças são relevantes
Definir quais tipos de alteração devem ser consideradas como impacto no processo.

### 3. Confirmar filtros usados anteriormente (GIAGRO)
Levantar quais filtros já são utilizados no fluxo atual e devem ser replicados ou adaptados.

### 4. Confirmar comportamento quando não houver mudança em cadastro
Definir se o robô deve:
- Encerrar o fluxo  
- Apenas registrar no log  

### 5. Confirmar exemplos de retificação direta
Definir cenários reais onde a retificação altera diretamente o cadastro.

### 6. Confirmar exemplos de retificação indireta
Definir cenários onde a retificação exige consulta adicional a outro ato ou publicação.

---

## To Do

### 1. Criar regra DOU x Cadastro
Desenvolver a lógica para comparar os dados publicados no DOU com os dados existentes no cadastro.

### 2. Criar cenário de mudança e não mudança
Definir o comportamento do robô para:
- Quando há mudança relevante  
- Quando não há mudança  

### 3. Criar lógica de aplicação dos filtros
Implementar a aplicação dos filtros definidos para identificar somente mudanças relevantes.

### 4. Criar tratamento para retificação direta
Implementar o tratamento quando a retificação altera diretamente o cadastro.

### 5. Criar tratamento para retificação indireta
Implementar o fluxo onde o robô precisa acessar outro ato para identificar a mudança.

### 6. Criar acesso ao DOU referenciado pela retificação
Permitir que o robô navegue até a publicação original mencionada.

### 7. Criar leitura do Ato, Seção e itens indicados
Extrair corretamente as informações da publicação referenciada.

### 8. Criar verificação se a retificação indireta afeta o cadastro
Validar se a mudança identificada impacta o cadastro atual.

### 9. Criar armazenamento dos dados identificados
Salvar todas as mudanças e informações identificadas para uso posterior.

### 10. Registrar resultado no log
Registrar detalhadamente:
- Tipo de alteração  
- Se houve impacto  
- Resultado da análise  

---

## In Progress

- (Preencher conforme evolução da sprint)
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

- (Preencher conforme evolução da sprint)