import asyncio
import logging
from typing import Optional, Set, Tuple

from telethon import TelegramClient, events

from classifier import JevClassifier
from cli_dashboard import CliDashboard, KeyboardController

logger = logging.getLogger("telegram_user")


class TelegramUserListener:
    """Ouvinte de mensagens de grupos, canais e testes do Telegram usando Telethon."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        classifier: JevClassifier,
        session_name: str = "jev_user_session",
        dashboard: Optional[CliDashboard] = None,
        preload_recent: int = 2,
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.classifier = classifier
        self.session_name = session_name
        self.dashboard = dashboard
        self.preload_recent = preload_recent
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)

        self.my_id: Optional[int] = None
        self.seen_messages: Set[Tuple[int, int]] = set()

    async def _process_message(self, chat_id: int, group_name: str, sender_name: str, text: str, msg_id: int) -> None:
        """Classifica a mensagem no JEV AI e envia ao dashboard (com deduplicação)."""
        key = (chat_id, msg_id)
        if key in self.seen_messages:
            return
        self.seen_messages.add(key)

        clean_text = text.strip()
        if not clean_text:
            return

        try:
            result = await self.classifier.classify(clean_text)
            category = result["category"]
            conf = result["confidence"]
            sim_flag = result.get("is_simulation", False)

            if self.dashboard:
                self.dashboard.add_message(
                    group=group_name,
                    sender=sender_name,
                    category=category,
                    confidence=conf,
                    text=clean_text,
                    is_simulation=sim_flag,
                )
            else:
                conf_pct = conf * 100
                sim_tag = " [SIM]" if sim_flag else ""
                print(
                    f"[JEV{sim_tag}] [{category}] ({conf_pct:.0f}%) | "
                    f"SRC: {group_name} | USER: {sender_name} | MSG: {clean_text[:90]}"
                )
        except Exception as e:
            logger.error(f"Erro ao classificar mensagem: {e}", exc_info=True)

    async def _preload_channels(self) -> None:
        """Carrega e cataloga todos os canais/grupos e pré-classifica as mensagens mais recentes."""
        try:
            dialogs = await self.client.get_dialogs(limit=50)
            target_dialogs = [d for d in dialogs if not d.is_user]
            logger.info(f"Monitorando {len(target_dialogs)} grupos/canais.")

            if self.preload_recent <= 0:
                return

            for d in target_dialogs:
                try:
                    msgs = await self.client.get_messages(d, limit=self.preload_recent)
                    for m in reversed(msgs):
                        txt = (m.raw_text or "").strip()
                        if not txt:
                            continue

                        sender = await m.get_sender()
                        sender_name = (
                            getattr(sender, "username", None)
                            and f"@{sender.username}"
                            or getattr(sender, "first_name", None)
                            or d.title
                        )
                        await self._process_message(d.id, d.title, sender_name, txt, m.id)
                except Exception as e:
                    logger.debug(f"Falha ao pré-carregar canal {d.title}: {e}")
        except Exception as e:
            logger.error(f"Erro ao pré-carregar canais: {e}")

    async def _setup_handlers(self) -> None:
        """Registra o manipulador de eventos em tempo real."""

        @self.client.on(events.NewMessage)
        async def on_new_message(event):
            # Permite: Grupos, Supergrupos, Canais de transmissão E 'Mensagens Salvas' (para teste imediato)
            is_saved_messages = bool(self.my_id and event.chat_id == self.my_id)
            if event.is_private and not is_saved_messages:
                return

            text = event.raw_text
            if not text or not text.strip():
                return

            try:
                chat = await event.get_chat()
                if is_saved_messages:
                    group_name = "MENSAGENS SALVAS (TESTE)"
                    sender_name = "Você"
                else:
                    group_name = getattr(chat, "title", f"Chat_{event.chat_id}")
                    sender = await event.get_sender()
                    if sender:
                        sender_name = (
                            getattr(sender, "username", None)
                            and f"@{sender.username}"
                            or getattr(sender, "first_name", None)
                            or group_name
                        )
                    else:
                        sender_name = group_name

                await self._process_message(event.chat_id, group_name, sender_name, text, event.id)
            except Exception as e:
                logger.error(f"Erro ao processar evento de mensagem: {e}", exc_info=True)

    async def _sync_loop(self, stop_event: asyncio.Event) -> None:
        """Sincronizador em background que garante a captura mesmo se o push do Telegram atrasar."""
        while not stop_event.is_set():
            try:
                await asyncio.sleep(8)
                if stop_event.is_set():
                    break
                dialogs = await self.client.get_dialogs(limit=25)
                for d in dialogs:
                    if d.is_user and d.id != self.my_id:
                        continue
                    msgs = await self.client.get_messages(d, limit=1)
                    if msgs:
                        m = msgs[0]
                        txt = (m.raw_text or "").strip()
                        if txt and (d.id, m.id) not in self.seen_messages:
                            sender = await m.get_sender()
                            sender_name = (
                                getattr(sender, "username", None)
                                and f"@{sender.username}"
                                or getattr(sender, "first_name", None)
                                or d.title
                            )
                            title = "MENSAGENS SALVAS (TESTE)" if d.id == self.my_id else d.title
                            await self._process_message(d.id, title, sender_name, txt, m.id)
            except Exception as e:
                logger.debug(f"Erro no sync loop: {e}")

    def run(self) -> None:
        """Inicia o ouvinte com suporte a abas, eventos em tempo real e sincronização contínua."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _main():
            await self.client.start()
            me = await self.client.get_me()
            self.my_id = me.id if me else None

            print("Conectado! Carregando canais e ofertas recentes...")
            await self._preload_channels()
            await self._setup_handlers()

            if self.dashboard:
                from rich.live import Live

                stop_event = asyncio.Event()

                def _on_shutdown():
                    stop_event.set()

                kb = KeyboardController(self.dashboard, shutdown_callback=_on_shutdown)
                kb.start()

                sync_task = asyncio.create_task(self._sync_loop(stop_event))

                try:
                    with Live(self.dashboard.render(), refresh_per_second=4, screen=True) as live:
                        self.dashboard.live = live
                        disconnect_task = asyncio.create_task(self.client.run_until_disconnected())
                        stop_task = asyncio.create_task(stop_event.wait())

                        await asyncio.wait(
                            [disconnect_task, stop_task],
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                finally:
                    stop_event.set()
                    sync_task.cancel()
                    kb.stop()
                    if self.client.is_connected():
                        await self.client.disconnect()
            else:
                print("STATUS: Telegram User Listener conectado.")
                await self.client.run_until_disconnected()

        try:
            loop.run_until_complete(_main())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
