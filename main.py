#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from classifier import JevClassifier

# Configuração de logging limpa para não sujar a interface TUI
logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("app")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Classificador de mensagens do Telegram com JEV AI (Estilo Arch Linux / Omarchy)."
    )
    parser.add_argument(
        "--mode",
        choices=["bot", "user", "simulate"],
        default=None,
        help="Modo: 'user' (Telethon), 'bot' (Bot API) ou 'simulate' (teste).",
    )
    parser.add_argument(
        "--categories",
        default="categories.json",
        help="Caminho para o arquivo JSON de categorias (padrao: categories.json).",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Forca modo de simulacao sem chamar API externa.",
    )
    parser.add_argument(
        "--reply",
        action="store_true",
        help="Habilita respostas automaticas no grupo.",
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()

    typesafe_api_key = os.getenv("TYPESAFE_API_KEY")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    reply_in_group = args.reply or os.getenv("REPLY_IN_GROUP", "false").lower() in ("true", "1", "yes")

    simulate = args.simulate or not bool(typesafe_api_key)

    # Auto-detecta o modo de operacao
    mode = args.mode
    if not mode:
        if api_id and api_hash:
            mode = "user"
        elif bot_token:
            mode = "bot"
        else:
            mode = "simulate"

    classifier = JevClassifier(
        api_key=typesafe_api_key,
        categories_path=args.categories,
        simulate=simulate,
    )

    from cli_dashboard import CliDashboard, KeyboardController

    dashboard = CliDashboard(
        categories=classifier.categories,
        mode_label=f"{mode.upper()} // {'SIM' if simulate else 'LIVE'}",
    )

    if mode == "user":
        if not api_id or not api_hash:
            print("[ERROR] TELEGRAM_API_ID e TELEGRAM_API_HASH necessarios no arquivo .env.")
            sys.exit(1)

        from user_listener import TelegramUserListener

        listener = TelegramUserListener(
            api_id=int(api_id),
            api_hash=api_hash,
            classifier=classifier,
            dashboard=dashboard,
        )
        listener.run()

    elif mode == "bot":
        if not bot_token:
            print("[ERROR] TELEGRAM_BOT_TOKEN nao encontrado no arquivo .env.")
            sys.exit(1)

        from bot_listener import TelegramBotListener

        listener = TelegramBotListener(
            token=bot_token,
            classifier=classifier,
            reply_in_group=reply_in_group,
            dashboard=dashboard,
        )
        listener.run()

    elif mode == "simulate":
        import asyncio
        from rich.live import Live

        # Mensagens de exemplo variadas cobrindo as categorias
        sim_data = [
            ("Canaltech Ofertas", "PromoBot", "Placa de Video Galax GeForce RTX 4070 Super 12GB por R$ 3.899"),
            ("Pelando Promocoes", "ofertas_adm", "Processador AMD Ryzen 7 7800X3D 8-Core 16-Thread por R$ 2.450"),
            ("Promobit Hardware", "pedro_sp", "SSD Kingston Fury Renegade 1TB M.2 NVMe 7300MB/s por R$ 489"),
            ("TopTech PROMO", "deals_bot", "Monitor Gamer LG UltraGear 27 144Hz IPS 1ms por R$ 899 em 10x"),
            ("Ofertas Adrenaline", "bot_adrena", "Teclado Mecanico Redragon Kumara Switch Outemu Brown por R$ 149"),
            ("Promocoes do Guiga", "guiga_user", "Notebook Gamer Lenovo LOQ RTX 3050 i5-12450H por R$ 3.599"),
            ("EscolhaSegura Ofertas", "rafa_tech", "iPhone 15 128GB Preto por R$ 4.399 a vista ou 10x sem juros"),
            ("Pelando Games", "gamer_pro", "Console PlayStation 5 Slim com 2 Jogos por R$ 3.399 na Amazon"),
            ("Canaltech Ofertas", "audio_bot", "Fone Bluetooth Galaxy Buds 2 Pro com ANC por R$ 629"),
            ("Promobit Cupons", "cupom_master", "CUPOM 25% OFF no Mercado Livre: VEMPRAFESTA25 acima de R$ 199"),
            ("Grupo Hardware BR", "marcelo_duvida", "Alguem sabe se uma fonte de 650W segura o Ryzen 7 com a RTX 4070?"),
        ]

        async def _run_sim():
            stop_event = asyncio.Event()

            def _on_shutdown():
                stop_event.set()

            kb = KeyboardController(dashboard, shutdown_callback=_on_shutdown)
            kb.start()

            try:
                with Live(dashboard.render(), refresh_per_second=4, screen=True) as live:
                    dashboard.live = live

                    async def _feed():
                        for group, user, text in sim_data:
                            if stop_event.is_set():
                                break
                            await asyncio.sleep(1.2)
                            res = await classifier.classify(text)
                            dashboard.add_message(
                                group=group,
                                sender=user,
                                category=res["category"],
                                confidence=res["confidence"],
                                text=text,
                                is_simulation=res.get("is_simulation", False),
                            )
                        # Continua rodando para navegacao de abas
                        while not stop_event.is_set():
                            await asyncio.sleep(0.5)

                    feed_task = asyncio.create_task(_feed())
                    stop_task = asyncio.create_task(stop_event.wait())
                    await asyncio.wait([feed_task, stop_task], return_when=asyncio.FIRST_COMPLETED)
            finally:
                kb.stop()

        try:
            asyncio.run(_run_sim())
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
