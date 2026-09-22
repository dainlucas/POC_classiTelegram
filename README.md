# JEV Telegram Classifier

Classificador em tempo real de mensagens de grupos e canais do Telegram utilizando JEV AI (TypeSafe AI), com interface de terminal interativa organizada por abas.

## Requisitos

* Python 3.10 ou superior
* Conta no Telegram com credenciais de API (my.telegram.org)
* Chave de API da TypeSafe AI (console.typesafe.ai)

## Instalacao Rapida

Execute o script de inicializacao automatica:

```bash
chmod +x run.sh
./run.sh
```

O script cria o ambiente virtual, instala as dependencias e prepara o arquivo de configuracao.

## Configuracao

Copie o modelo de ambiente para criar o seu arquivo local:

```bash
cp .env.example .env
```

Preencha as variaveis no arquivo `.env`:

```ini
TYPESAFE_API_KEY=sua_chave_typesafe
TELEGRAM_API_ID=seu_api_id
TELEGRAM_API_HASH=seu_api_hash
```

## Modos de Execucao

### 1. Modo Usuario (Telethon)
Escuta todos os canais de ofertas, grupos em que sua conta participa e o chat de Mensagens Salvas.

```bash
./run.sh --mode user
```

Na primeira execucao, informe o numero de telefone e o codigo enviado pelo aplicativo do Telegram para salvar a sessao local.

### 2. Modo Simulacao
Executa o painel com mensagens de exemplo para demonstracao visual, sem conexao de rede.

```bash
./run.sh --mode simulate
```

### 3. Modo Bot
Utiliza a API oficial de bots para monitorar grupos onde o bot foi adicionado.

```bash
./run.sh --mode bot
```

## Navegacao no Terminal

| Tecla | Funcao |
| :--- | :--- |
| TAB ou Seta Direita ou L | Avanca para a proxima aba de categoria |
| Shift + TAB ou Seta Esquerda ou H | Retorna para a aba anterior |
| 0 a 9 | Seleciona diretamente a aba pelo numero |
| A | Retorna para a aba ALL com todas as mensagens |
| C | Limpa as mensagens da tela |
| Q | Encerra a aplicacao e restaura o terminal |

## Personalizacao de Categorias

As categorias e seus criterios de classificacao ficam no arquivo `categories.json`.
Para alterar ou criar novas categorias, edite o arquivo com a chave desejada e a descricao do criterio correspondente:

```json
{
  "PLACAS_DE_VIDEO": "Placas de video e GPUs Nvidia GeForce ou AMD Radeon",
  "PROCESSADORES": "Processadores e CPUs AMD Ryzen ou Intel Core",
  "SMARTPHONES": "Celulares e smartphones Apple, Samsung, Xiaomi ou Motorola",
  "CUPOM_DESCONTO": "Codigos de cupom de lojas como Mercado Livre, Shopee ou Amazon",

  "OUTROS": "Mensagens que nao se enquadram nas categorias acima"
}
```
O classificador utiliza esses criterios diretamente na tomada de decisao.
