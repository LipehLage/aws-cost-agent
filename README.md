# aws-cost-agent

[![CI](https://github.com/LipehLage/aws-cost-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/LipehLage/aws-cost-agent/actions/workflows/ci.yml)

Agente de FinOps que lê os custos da sua conta AWS pelo Cost Explorer,
detecta anomalias de crescimento e usa um LLM (Google Gemini) para gerar um
relatório executivo com recomendações de otimização.

É a versão open source de um problema que já resolvi em produção: herdei uma
conta AWS com fatura alta e liderei a redução de custos migrando a operação
de EKS para ECS. A lição que ficou — custo de nuvem precisa de vigilância
contínua, não de força-tarefa anual — virou este agente.

**Você não precisa de conta AWS (nem de chave de API) para experimentar:**
o modo demo roda com um dataset realista que inclui uma anomalia plantada,
e sem `GEMINI_API_KEY` o agente entrega um relatório básico determinístico.

---

## Stack utilizada

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Custos AWS | Cost Explorer API via boto3 |
| IA | [Google Gemini API](https://ai.google.dev/) (Gemini Flash) |
| Deploy opcional | AWS Lambda agendada (EventBridge) + SNS |
| Infra como código | Terraform |
| CI | GitHub Actions (testes + smoke test do modo demo) |

---

## Como funciona

```
                    ┌──────────────────────────────────────────┐
                    │              cost_agent                  │
   AWS Cost         │                                          │
   Explorer ───────▶│  collector ──▶ analyzer ──▶ reporter     │──▶ relatório
   (boto3)          │  (ou demo_data)   │            │         │    Markdown
                    │                   │            │         │
                    └───────────────────┼────────────┼─────────┘
                                        │            │
                              ranking + anomalias   Gemini API
                              (semana vs. semana)   (ou fallback sem LLM)
```

1. **collector** busca os custos diários por serviço dos últimos N dias
   (`ce:GetCostAndUsage`). No modo demo, `demo_data` gera o mesmo formato.
2. **analyzer** agrega o período: custo total, ranking de serviços com
   percentual e anomalias — serviços que cresceram ≥ 25% semana contra
   semana com custo relevante.
3. **reporter** entrega o resumo a um LLM, que escreve o relatório executivo
   com recomendações acionáveis. Sem chave de API, um fallback monta o
   relatório básico com os mesmos dados.

---

## Rodando

```bash
git clone https://github.com/LipehLage/aws-cost-agent.git
cd aws-cost-agent

python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# Modo demo — não precisa de AWS nem de chave
python -m cost_agent --demo

# Com IA: chave gratuita em https://aistudio.google.com/apikey
export GEMINI_API_KEY=sua-chave        # Windows: $env:GEMINI_API_KEY="sua-chave"
python -m cost_agent --demo

# Conta AWS real (credenciais via env/perfil com permissão ce:GetCostAndUsage)
python -m cost_agent --days 30
python -m cost_agent --profile producao -o relatorio.md
```

Testes: `pip install pytest && pytest -v`

---

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GEMINI_API_KEY` | Não | Chave da Gemini API; sem ela, relatório básico sem LLM |
| `GEMINI_MODEL` | Não | Modelo do Gemini (padrão: `gemini-flash-latest`) |
| `ANALYSIS_DAYS` | Não | Janela de análise na Lambda (padrão: 30) |
| `SNS_TOPIC_ARN` | Não | Na Lambda: tópico que recebe o relatório |

---

## Deploy como Lambda agendada (opcional)

O diretório `terraform/` provisiona a versão "piloto automático": uma Lambda
que roda toda segunda-feira, analisa os últimos 30 dias e publica o relatório
em um tópico SNS (assine com seu e-mail e receba a análise na caixa de
entrada).

```bash
./scripts/package.sh                      # gera build/lambda.zip
cd terraform
terraform init
terraform apply -var "report_email=voce@exemplo.com" -var "gemini_api_key=..."
```

A role da Lambda recebe apenas o mínimo: `ce:GetCostAndUsage`, publish no
tópico do relatório e logs no CloudWatch.

---

## O que este projeto exercitou

- Consumo da API do Cost Explorer com boto3, incluindo paginação
- Detecção de anomalias simples e explicável (crescimento semana contra
  semana com piso de materialidade) — sem caixa preta
- Prompt engineering para relatório executivo: o LLM recebe dados já
  estruturados e é instruído a não inventar números
- Degradação graciosa: sem chave de API o pipeline segue útil
- Infraestrutura como código com Terraform: Lambda, EventBridge, SNS e IAM
  com permissões mínimas
- CI no GitHub Actions com testes e smoke test do fluxo completo

---

## Licença

[MIT](LICENSE) — use, estude e adapte à vontade.
