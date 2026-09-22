import logging
import os
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from classifier import JevClassifier
from cli_dashboard import CliDashboard

logger = logging.getLogger("telegram_bot")


class TelegramBotListener:
    """Ouvinte de mensagens de grupos do Telegram via Telegram Bot API."""

    def __init__(
        self,
        token: str,
        classifier: JevClassifier,
        reply_in_group: bool = False,
        dashboard: Optional[CliDashboard] = None,
    ):
        self.token = token
        self.classifier = classifier
        self.reply_in_group = reply_in_group
        self.dashboard = dashboard
        self.app: Optional[Application] = None

    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        cats = "\n".join([f"- **{k}**: {v}" for k, v in self.classifier.categories.items()])
        text = (
            "**JEV AI Telegram Classifier**\n\n"
            "Classificador de mensagens em tempo real via JEV AI.\n\n"
            f"**Categorias ativas:**\n{cats}\n\n"
            "**Comandos:**\n"
            "/categorias - Lista categorias\n"
            "/reload - Recarrega categories.json\n"
            "/test <texto> - Testa classificacao"
        )
        if update.effective_message:
            await update.effective_message.reply_text(text, parse_mode="Markdown")

    async def _on_categorias(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        cats = "\n".join([f"- **{k}**: {v}" for k, v in self.classifier.categories.items()])
        msg = f"**Categorias ativas ({len(self.classifier.categories)}):**\n\n{cats}"
        if update.effective_message:
            await update.effective_message.reply_text(msg, parse_mode="Markdown")

    async def _on_reload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        cats = self.classifier.reload_categories()
        msg = f"Categorias recarregadas. Total: {len(cats)} categorias ativas."
        logger.info(msg)
        if update.effective_message:
            await update.effective_message.reply_text(msg)

    async def _on_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            if update.effective_message:
                await update.effective_message.reply_text("Uso: `/test Vendo RTX 3080 seminova`", parse_mode="Markdown")
            return

        text = " ".join(context.args)
        result = await self.classifier.classify(text)
        conf_pct = result["confidence"] * 100
        sim_tag = " [SIMULADO]" if result.get("is_simulation") else ""

        reply = (
            f"**Classificacao JEV AI{sim_tag}:**\n"
            f"• Categoria: `{result['category']}`\n"
            f"• Confianca: `{conf_pct:.1f}%`\n"
            f"• Texto: _{text}_"
        )
        if update.effective_message:
            await update.effective_message.reply_text(reply, parse_mode="Markdown")

    async def _on_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        if not message:
            return

        text = message.text or message.caption
        if not text:
            return

        chat = update.effective_chat
        user = update.effective_user

        group_name = chat.title if chat else "Desconhecido"
        user_name = (user.username and f"@{user.username}") or (user.full_name if user else "Anonimo")

        try:
            result = await self.classifier.classify(text)
            category = result["category"]
            conf = result["confidence"]
            sim_flag = result.get("is_simulation", False)

            if self.dashboard:
                self.dashboard.add_message(
                    group=group_name,
                    sender=user_name,
                    category=category,
                    confidence=conf,
                    text=text,
                    is_simulation=sim_flag,
                )
            else:
                conf_pct = conf * 100
                sim_tag = " [SIM]" if sim_flag else ""
                print(
                    f"[JEV{sim_tag}] [{category}] ({conf_pct:.0f}%) | "
                    f"SRC: {group_name} | USER: {user_name} | MSG: {text.strip()[:100]}"
                )

            if self.reply_in_group:
                reply_text = f"[JEV AI] Categoria: `{category}` ({conf*100:.1f}%)"
                await message.reply_text(reply_text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Erro ao processar mensagem do grupo '{group_name}': {e}", exc_info=True)

    def run(self) -> None:
        self.app = ApplicationBuilder().token(self.token).build()

        self.app.add_handler(CommandHandler(["start", "help"], self._on_start))
        self.app.add_handler(CommandHandler("categorias", self._on_categorias))
        self.app.add_handler(CommandHandler("reload", self._on_reload))
        self.app.add_handler(CommandHandler("test", self._on_test))

        group_filter = (filters.TEXT | filters.CAPTION) & (filters.ChatType.GROUPS | filters.ChatType.CHANNEL)
        self.app.add_handler(MessageHandler(group_filter, self._on_group_message))

        if self.dashboard:
            from rich.live import Live
            with Live(self.dashboard.render(), refresh_per_second=4, screen=True) as live:
                self.dashboard.live = live
                self.app.run_polling()
        else:
            print("=" * 60)
            print("Telegram Bot Listener iniciado.")
            print(f"Categorias ({len(self.classifier.categories)}): {list(self.classifier.categories.keys())}")
            print("=" * 60)
            self.app.run_polling()
