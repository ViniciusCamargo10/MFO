# Agendamento com cron-job.org

## Objetivo
O robô DOU precisa executar automaticamente nos dias úteis, nos horários **08:00** e **16:00**. Como o robô roda via GitHub Actions, o cron-job.org é usado como trigger externo para disparar o workflow nesses horários.

## Pré-requisitos
- Conta no [cron-job.org](https://cron-job.org)
- Workflow `dou_automation.yml` configurado com `workflow_dispatch`

## Passo a Passo

### 1. Obter a URL de Trigger do GitHub Actions
1. No repositório do GitHub, vá em **Settings > Actions > General**
2. Em **Workflow permissions**, marque **Allow GitHub Actions to create and approve pull requests**
3. Para gerar um token de acesso:
   - Vá em **Settings > Developer settings > Personal access tokens > Fine-grained tokens**
   - Crie um token com permissão `actions:write` para o repositório
4. A URL de trigger será:
   ```
   POST /repos/{owner}/{repo}/actions/workflows/dou_automation.yml/dispatches
   ```
   Exemplo:
   ```
   https://api.github.com/repos/seu-usuario/seu-repo/actions/workflows/dou_automation.yml/dispatches
   ```

### 2. Configurar no cron-job.org

Para cada horário, crie um cron job:

#### Job 1 — 08:00 (dias úteis)
| Campo | Valor |
|-------|-------|
| Title | DOU Automation - 08:00 |
| URL | `https://api.github.com/repos/{owner}/{repo}/actions/workflows/dou_automation.yml/dispatches` |
| Method | `POST` |
| Content-Type | `application/json` |
| Body | `{"ref":"main"}` |
| Headers | `Authorization: Bearer {seu_token}` |
| Cron Expression | `0 8 * * 1-5` (seg-sex 08:00) |

#### Job 2 — 16:00 (dias úteis)
| Campo | Valor |
|-------|-------|
| Title | DOU Automation - 16:00 |
| URL | `https://api.github.com/repos/{owner}/{repo}/actions/workflows/dou_automation.yml/dispatches` |
| Method | `POST` |
| Content-Type | `application/json` |
| Body | `{"ref":"main"}` |
| Headers | `Authorization: Bearer {seu_token}` |
| Cron Expression | `0 16 * * 1-5` (seg-sex 16:00) |

### 3. Formato do Body
```json
{
  "ref": "main"
}
```
Isso indica qual branch deve ser usada na execução.

### 4. Testando a Configuração
1. No cron-job.org, clique em **Run** para testar manualmente
2. Verifique no GitHub Actions se o workflow foi disparado
3. Confira o log gerado em `logs/execucao.jsonl`

## Observações
- O GitHub Actions gratuito tem limite de minutos de execução mensal
- O workflow atual (`dou_automation.yml`) está configurado apenas com `workflow_dispatch` (disparo manual/API)
- Se a URL de trigger mudar (ex: mudança de token), atualize os jobs no cron-job.org

## Fluxo Completo
```
cron-job.org (08:00 / 16:00)
  → POST /dispatches (GitHub API)
    → GitHub Actions executa dou_automation.yml
      → python src/main.py --manual
        → Baixa PDF Seção 1
        → Extrai ATOS do DSV/CGAA
        → Extrai Retificações
        → Gera JSON/TXT
        → Registra log
```
