# VagaCheck

VagaCheck e uma ferramenta para ajudar pessoas em busca de emprego a identificar sinais de golpe em anuncios de vaga recebidos por WhatsApp, e-mail, redes sociais, LinkedIn ou sites de recrutamento.

Este projeto foi desenvolvido para fins academicos durante os estudos do curso **IA Generativa - Pos-Graduacao em IA Aplicada UniSenai (SC)**.

## Objetivo da ferramenta

O objetivo do VagaCheck e transformar uma vaga recebida em um veredito claro de risco. O usuario cola o texto da oferta, informa alguns campos estruturados e recebe:

- um score de risco de 0 a 100;
- um veredito: `provavel_golpe`, `atencao` ou `provavel_legitima`;
- uma lista de red flags explicando quais sinais foram encontrados;
- um historico das analises feitas;
- uma area para registrar denuncias colaborativas;
- um dashboard simples com indicadores do prototipo.

A ferramenta nao decide juridicamente se uma vaga e fraude. Ela funciona como uma triagem preventiva para ajudar o candidato a perceber sinais suspeitos antes de enviar dados pessoais, pagar taxas ou continuar em um processo seletivo duvidoso.

Esta entrega nao integra nenhum LLM ou modelo de IA real. Onde a IA entraria no futuro, o projeto usa um motor de regras deterministico e transparente.

## Problema e solucao

Golpes de vaga exploram urgencia, promessa de renda e pedidos de pagamento ou dados pessoais. O VagaCheck organiza esses sinais em um fluxo de analise:

1. Entrada do texto bruto e campos da vaga.
2. Extracao mockada de salario e contato quando possivel.
3. Motor de regras baseado nas especificacoes do projeto e inspirado no dataset EMSCAD / Real or Fake Job Posting Prediction.
4. Persistencia local em SQLite.
5. Historico, denuncia colaborativa e dashboard.

## Como rodar

Requisito: Python 3.11 ou superior.

```bash
python app.py --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`.

## Deploy no Hugging Face Spaces

Este repositorio ja inclui `Dockerfile` para publicar o prototipo como Space.

1. Crie um novo Space em `https://huggingface.co/spaces`.
2. Escolha **SDK: Docker**.
3. Suba os arquivos deste repositorio para o Space.
4. O Hugging Face executara automaticamente:

```bash
python scripts/start_hf.py
```

O Space usa a porta padrao `7860`, exigida pela plataforma. O script tambem cria dados de exemplo quando o banco SQLite ainda esta vazio.

Para popular exemplos:

```bash
python scripts/seed_demo.py
```

Para rodar os testes:

```bash
python -m unittest discover -s tests
```

## Estrutura

```text
app/
  database.py   SQLite, tabelas e repositorios
  extractor.py  extracao mockada de campos
  scoring.py    motor de regras e score
  server.py     API HTTP e arquivos estaticos
static/
  index.html    interface principal
  styles.css    layout responsivo
  app.js        integracao com API
seed/
  vagas_demo.csv
tests/
  test_scoring.py
files/
  especificacoes originais e PDF da avaliacao
```

## Escolhas de design

- Usei Python padrao, `http.server` e `sqlite3` porque o ambiente local nao tinha FastAPI, Flask, Uvicorn ou Pytest instalados. Isso deixa o prototipo executavel sem baixar dependencias.
- A UI tem cinco areas navegaveis: analise, historico, denuncias, dashboard e roadmap de IA. Isso atende melhor ao criterio de complexidade do que uma tela unica.
- O motor de regras fica isolado em `app/scoring.py`, preparando a substituicao futura por classificador, embeddings ou orquestracao com LangGraph.
- O banco usa UUID em `TEXT` e datas ISO-8601, seguindo o modelo de dominio especificado.

## Motor de regras

O score soma pesos de red flags como ausencia de logo, ausencia de perfil da empresa, descricao curta, salario incompatível, canal generico, urgencia excessiva e cobranca antecipada. O veredito segue:

- `>= 60`: provavel golpe
- `>= 30`: atencao
- `< 30`: provavel legitima

Os pesos sao heuristicas inspiradas por tendencias publicadas em analises do dataset EMSCAD, mas nao sao coeficientes treinados.

## Referencias

- Dataset base usado como referencia estrutural e conceitual: [Real or Fake? Fake Job Posting Prediction - Kaggle](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction).
- Especificacoes locais do projeto em `files/`, incluindo modelo de dominio, regras de score e roadmap de integracao futura com IA.

## Roadmap de IA

Na proxima fase, a arquitetura pode evoluir para:

- embeddings para busca semantica de vagas parecidas;
- classificador Transformer treinado no EMSCAD e em exemplos brasileiros;
- modelo local via Ollama para explicacoes em linguagem natural;
- LangGraph para orquestrar extracao, verificacao de empresa e consolidacao do veredito.

## O que funcionou com o agente

- A leitura incremental dos specs ajudou a transformar documentos soltos em uma arquitetura concreta.
- O agente gerou bem a separacao entre dominio, persistencia, score e UI.
- Os casos de teste do motor de regras foram derivados diretamente das especificacoes, especialmente o golpe brasileiro com PIX e e-mail generico.

## O que nao funcionou ou exigiu ajuste

- Algumas especificacoes citadas no indice nao estavam presentes na pasta. Foi necessario inferir fluxos, telas, arquitetura e observabilidade a partir dos arquivos disponiveis e do PDF.
- A stack recomendada no PDF era FastAPI + React + SQLite, mas as dependencias web nao estavam instaladas. A alternativa com biblioteca padrao foi escolhida para garantir que o projeto rode imediatamente.
- O projeto ainda nao publica um endpoint publico por conta propria. Para a entrega, exponha a porta local com ngrok ou hospede o repositorio em uma plataforma gratuita.

## Endpoint publico

Para um link estavel, use o Hugging Face Spaces com SDK Docker. Para um link temporario durante a avaliacao, uma opcao simples e rodar:

```bash
python app.py --host 127.0.0.1 --port 8000
ngrok http 8000
```

Use a URL HTTPS gerada pelo ngrok como endpoint funcional.

No Windows, tambem ha scripts prontos:

```powershell
.\scripts\start_local.ps1
```

Em outro terminal:

```powershell
.\scripts\start_ngrok.ps1
```

Se o ngrok ainda nao estiver configurado, instale em `https://ngrok.com/download` e rode uma vez:

```powershell
ngrok config add-authtoken SEU_TOKEN
```
