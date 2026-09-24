# JEV Telegram Classifier

Real-time Telegram message classifier powered by JEV AI (TypeSafe AI), featuring an interactive tabbed terminal interface.

## Requirements

- Python 3.10+
- Telegram API credentials (`api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org))
- TypeSafe AI API Key ([console.typesafe.ai](https://console.typesafe.ai))

## Quick Start

1. **Configure credentials:**
   ```bash
   cp .env.example .env
   ```
   Set the following variables in `.env`:
   ```ini
   TYPESAFE_API_KEY=your_typesafe_key
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```

2. **Run setup and launch:**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
   *(Automatically sets up the virtual environment and installs dependencies.)*

## Run Modes

### 1. User Mode (Telethon)
Monitors joined groups, channels, and Saved Messages.
```bash
./run.sh --mode user
```
*Prompts for phone number and Telegram verification code on first run.*

### 2. Simulation Mode
Runs UI with mock data for testing (offline).
```bash
./run.sh --mode simulate
```

### 3. Bot Mode
Monitors chats via the official Telegram Bot API.
```bash
./run.sh --mode bot
```

## Terminal Navigation

| Key | Action |
| :--- | :--- |
| `Tab` / `→` / `L` | Next category tab |
| `Shift + Tab` / `←` / `H` | Previous category tab |
| `0` - `9` | Jump directly to tab index |
| `A` | Go to `ALL` messages tab |
| `C` | Clear visible messages |
| `Q` | Exit and restore terminal |

## Custom Categories

Define your classification criteria in `categories.json`:

```json
{
  "GRAPHICS_CARDS": "Nvidia GeForce or AMD Radeon GPUs and graphics cards",
  "PROCESSORS": "AMD Ryzen or Intel Core CPUs and processors",
  "SMARTPHONES": "Apple, Samsung, Xiaomi, or Motorola smartphones",
  "DISCOUNT_COUPONS": "Store coupon codes and promotions",
  "OTHER": "Messages that do not fit into the categories above"
}
```
