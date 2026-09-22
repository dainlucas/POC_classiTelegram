# JEV AI Telegram Classifier (Arch Linux / Omarchy Style)

Classificador em tempo real de mensagens de grupos e canais do Telegram alimentado pelo **JEV AI** (modelo *System One* da TypeSafe AI), com interface interativa de terminal (TUI) por abas, estilo minimalista Unix / Arch Linux, sem emojis.

```text
╭──────────────────────────────────────────────────────────────────────────────╮
│  ARCH // JEV-CLASSIFIER [MODE: TELETHON // LIVE | STATUS: ONLINE]            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────── CATEGORIES // TABS ─────────────────────────────╮
│  0:ALL (28)  [1:PLACAS_DE_VIDEO (6)] [2:PROCESSADORES (3)] [3:MEMORIA_E_SSD  │
│ (2)] [4:MONITORES (2)] [5:PERIFERICOS (1)] [6:NOTEBOOKS (2)] [7:SMARTPHONES  │
│ (4)] [8:CONSOLES_E_GAMES (2)] [9:FONES_E_AUDIO (2)] ...                      │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─────────────────── LIVE FEED -- viewing [ALL] (28 msgs) ─────────────────────╮
│   TIME     SOURCE              USER          CATEGORY         CONF   PAYLOAD │
│  08:42:04  Pelando Promocoes   @deals_adm    [PLACAS_DE_VI...  99%   RTX 40… │
│  08:36:07  Canaltech Ofertas   bot_canal     [SMARTPHONES]     95%   Samsung │
╰──────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────────────────────╮
│ NAVIGATE: [TAB / ->] NEXT  [S-TAB / <-] PREV  [0-9] TAB NUM  [A] ALL  [Q] QUIT│
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## ⚡ Destaques

* **JEV AI (System One):** Decisões estruturadas em 200–350ms usando a primitiva `Choice` da TypeSafe AI.
* **TUI com Navegação por Abas:** Alterne entre categorias para filtrar mensagens em tempo real com `Tab`, setas ou teclas numéricas `0` a `9`.
* **Zero Emojis & Estilo Arch Linux:** Visual monocromático e ciano (`#1793d1`) com buffer de tela alternativo (`screen=True`, idêntico a `htop` e `btop`).
* **Suporte Completo a Grupos e Canais de Ofertas:** Escuta grupos comuns, supergrupos e canais de transmissão (Pelando, Promobit, Canaltech, etc.).
* **Teste Imediato via Mensagens Salvas:** Permite mandar qualquer mensagem no seu próprio chat de "Mensagens Salvas" para ver a classificação na hora.
* **Categorias 100% Personalizáveis:** Adicione, edite ou remova categorias no [`categories.json`](categories.json).

---

## 📦 Estrutura do Projeto

```text
POC_classiTelegram/
├── categories.json       # Definição e critérios das categorias no JEV AI
├── classifier.py         # Módulo de integração com o JEV AI (AsyncTypeSafeClient)
├── cli_dashboard.py      # TUI de terminal com abas e captura de teclado (Rich)
├── user_listener.py      # Ouvinte via conta de usuário (Telethon / MTProto)
├── bot_listener.py       # Ouvinte alternativo via Bot API (python-telegram-bot)
├── test_simulation.py    # Teste de simulação e terminal interativo
├── main.py               # Ponto de entrada unificado da aplicação
├── run.sh                # Script de execução rápida em 1 comando
├── pyproject.toml        # Configuração de empacotamento padrão Python
├── requirements.txt      # Dependências pip
├── .env.example          # Modelo de variáveis de ambiente
└── .gitignore            # Ignora credenciais, sessões e caches
```

---

## 🚀 Instalação e Inicialização Rápida

### Opção 1: Via Script Automatizado (Recomendado)

Clone o repositório e execute:

```bash
chmod +x run.sh
./run.sh
```

O script criará o ambiente virtual `.venv`, instalará todas as dependências e preparará o `.env` automaticamente.

---

### Opção 2: Manual com `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ou instalar como pacote editável:
```bash
pip install -e .
jev-classifier --help
```

---

## ⚙️ Configuração das Credenciais (`.env`)

Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

Preencha no `.env`:

```ini
# 1. Chave da API JEV AI (TypeSafe AI): https://console.typesafe.ai/settings/keys
TYPESAFE_API_KEY=sua_chave_typesafe_aqui

# 2. Credenciais do Telegram (Telethon - Modo Conta de Usuário):
# Obtenha em: https://my.telegram.org ("API development tools")
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890

# 3. (Opcional) Token de Bot do @BotFather se for rodar em modo Bot
TELEGRAM_BOT_TOKEN=
```

---

## 🎮 Modos de Execução

### 1. Modo Conta de Usuário (Telethon) — Recomendado para canais de promoções
Ouve todos os canais de ofertas, grupos que você participa e mensagens salvas:

```bash
./run.sh --mode user
# ou
.venv/bin/python main.py --mode user
```
*(Na primeira execução, o Telethon solicitará seu número de telefone e o código enviado no app do Telegram para gerar a sessão local `jev_user_session.session`).*

---

### 2. Modo Simulação Offline (Sem Telegram)
Ideal para testar visualmente o dashboard e as categorias com dados de exemplo:

```bash
./run.sh --mode simulate
# ou
.venv/bin/python main.py --mode simulate
```

---

### 3. Modo Bot Oficial (Telegram Bot API)
Ideal para grupos próprios onde você adiciona seu bot:

```bash
./run.sh --mode bot
# ou
.venv/bin/python main.py --mode bot
```

---

## ⌨️ Atalhos de Navegação no Dashboard

| Tecla | Ação |
| :--- | :--- |
| **`TAB`** ou **`->`** ou **`l`** | Avança para a próxima aba de categoria |
| **`Shift + TAB`** ou **`<-`** ou **`h`** | Volta para a aba anterior |
| **`0` a `9`** | Pula diretamente para o número da aba |
| **`A`** | Volta para a aba geral `[ALL]` (todas as mensagens) |
| **`C`** | Limpa o histórico de mensagens da tela |
| **`Q`** | Encerra a aplicação e restaura o terminal |

---

## 🛠️ Personalização das Categorias

Edite o arquivo [`categories.json`](categories.json) para incluir ou alterar qualquer categoria e seu critério:

```json
{
  "PLACAS_DE_VIDEO": "Placas de vídeo e GPUs Nvidia GeForce ou AMD Radeon",
  "PROCESSADORES": "Processadores e CPUs AMD Ryzen ou Intel Core",
  "SMARTPHONES": "Celulares e smartphones (Apple, Samsung, Xiaomi)",
  "CUPOM_DESCONTO": "Códigos de cupons de lojas (Mercado Livre, Shopee, Amazon)"
}
```

O JEV AI lê esses critérios dinamicamente e classifica com base neles.

---

## 📄 Licença

Distribuído sob a licença MIT.
