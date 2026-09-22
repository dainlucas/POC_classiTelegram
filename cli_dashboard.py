import asyncio
import os
import sys
from collections import Counter, deque
from datetime import datetime
from typing import Callable, Dict, List, Optional

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Paleta estilo Arch Linux / Omarchy: tons de ciano (#1793d1), cinzas, branco e acentos neons
ARCH_CYAN = "#1793d1"
BORDER_COLOR = "bright_black"

CATEGORY_PALETTE = [
    "bright_cyan",
    "bright_green",
    "bright_yellow",
    "bright_magenta",
    "bright_blue",
    "bright_red",
    "cyan",
    "green",
    "yellow",
    "magenta",
    "blue",
    "white",
]


class CliDashboard:
    """Dashboard de terminal interativo com abas no estilo Arch Linux / Omarchy (sem emojis)."""

    def __init__(
        self,
        categories: Dict[str, str],
        mode_label: str = "TELETHON",
        max_messages: int = 100,
        page_size: int = 15,
    ):
        self.categories = list(categories.keys())
        self.mode_label = mode_label.upper()
        self.max_messages = max_messages
        self.page_size = page_size

        # Lista de abas: [ "ALL", cat_1, cat_2, ... ]
        self.tabs: List[str] = ["ALL"] + self.categories
        self.active_tab_idx: int = 0

        self.messages: deque = deque(maxlen=max_messages)
        self.category_counts: Counter = Counter()
        self.total_received: int = 0
        self.start_time: datetime = datetime.now()

        # Mapeamento de cores
        self.color_map: Dict[str, str] = {}
        for idx, cat in enumerate(self.categories):
            if cat.upper() in ("OUTROS", "OTHER", "OUTRO"):
                self.color_map[cat] = "dim white"
            else:
                self.color_map[cat] = CATEGORY_PALETTE[idx % len(CATEGORY_PALETTE)]

        self.live: Optional[Live] = None
        self.keyboard_controller: Optional["KeyboardController"] = None

    def get_color(self, category: str) -> str:
        return self.color_map.get(category, "white")

    def next_tab(self) -> None:
        self.active_tab_idx = (self.active_tab_idx + 1) % len(self.tabs)
        self.refresh()

    def prev_tab(self) -> None:
        self.active_tab_idx = (self.active_tab_idx - 1) % len(self.tabs)
        self.refresh()

    def set_tab_index(self, idx: int) -> None:
        if 0 <= idx < len(self.tabs):
            self.active_tab_idx = idx
            self.refresh()

    def clear_messages(self) -> None:
        self.messages.clear()
        self.category_counts.clear()
        self.total_received = 0
        self.refresh()

    def refresh(self) -> None:
        if self.live:
            self.live.update(self.render())

    def add_message(
        self,
        group: str,
        sender: str,
        category: str,
        confidence: float,
        text: str,
        is_simulation: bool = False,
    ) -> None:
        self.total_received += 1
        self.category_counts[category] += 1

        self.messages.append(
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "group": group,
                "sender": sender,
                "category": category,
                "confidence": confidence,
                "text": text.replace("\n", " ").strip(),
                "is_simulation": is_simulation,
            }
        )

        self.refresh()

    def _get_filtered_messages(self) -> List[dict]:
        active_name = self.tabs[self.active_tab_idx]
        if active_name == "ALL":
            return list(self.messages)
        return [m for m in self.messages if m["category"] == active_name]

    def render(self) -> Group:
        # 1. Header estilo Arch Linux / Omarchy
        elapsed = max(1, int((datetime.now() - self.start_time).total_seconds()))
        uptime_str = f"{elapsed // 3600:02d}:{(elapsed % 3600) // 60:02d}:{elapsed % 60:02d}"

        header_table = Table(
            expand=True,
            box=None,
            show_header=False,
            padding=(0, 1),
        )
        header_table.add_column("Left", justify="left")
        header_table.add_column("Right", justify="right")

        left_text = Text()
        left_text.append("ARCH // JEV-CLASSIFIER ", style=f"bold {ARCH_CYAN}")
        left_text.append("[", style="dim white")
        left_text.append(f"MODE: {self.mode_label}", style="bold white")
        left_text.append(" | ", style="dim white")
        left_text.append("STATUS: ONLINE", style="bold green")
        left_text.append("]", style="dim white")

        right_text = Text()
        right_text.append(f"UPTIME: {uptime_str} ", style="dim cyan")
        right_text.append("│ ", style="bright_black")
        right_text.append(f"TOTAL: {self.total_received}", style="bold white")

        header_table.add_row(left_text, right_text)
        header_panel = Panel(
            header_table,
            border_style=ARCH_CYAN,
            box=box.ROUNDED,
            padding=(0, 1),
        )

        # 2. Navegador de Abas
        tabs_text = Text()
        for idx, tab_name in enumerate(self.tabs):
            count = self.total_received if tab_name == "ALL" else self.category_counts.get(tab_name, 0)
            is_active = idx == self.active_tab_idx
            shortcut = str(idx) if idx < 10 else ""

            prefix = f"{shortcut}:" if shortcut else ""
            label = f" {prefix}{tab_name} ({count}) "

            if is_active:
                tabs_text.append(label, style=f"bold black on {ARCH_CYAN}")
            else:
                style = "bold white" if count > 0 else "dim white"
                tabs_text.append(f"[{label.strip()}]", style=style)

            if idx < len(self.tabs) - 1:
                tabs_text.append(" ", style="dim")

        tabs_panel = Panel(
            tabs_text,
            title=f"[bold {ARCH_CYAN}]CATEGORIES // TABS[/bold {ARCH_CYAN}]",
            border_style="bright_black",
            box=box.ROUNDED,
            padding=(0, 1),
        )

        # 3. Tabela de Mensagens Filtrada
        active_tab_name = self.tabs[self.active_tab_idx]
        filtered = self._get_filtered_messages()
        page_items = list(reversed(filtered))[: self.page_size]

        table = Table(
            expand=True,
            box=box.MINIMAL_DOUBLE_HEAD,
            show_edge=True,
            header_style=f"bold {ARCH_CYAN}",
            border_style="bright_black",
            row_styles=["none", "dim"],
        )
        table.add_column("TIME", style="dim cyan", width=10, no_wrap=True)
        table.add_column("SOURCE", style="bold bright_blue", width=22, overflow="ellipsis", no_wrap=True)
        table.add_column("USER", style="yellow", width=16, overflow="ellipsis", no_wrap=True)
        table.add_column("CATEGORY", width=20, no_wrap=True)
        table.add_column("CONF", justify="right", width=7, no_wrap=True)
        table.add_column("PAYLOAD", style="white", overflow="ellipsis")

        if not page_items:
            table.add_row(
                datetime.now().strftime("%H:%M:%S"),
                "-",
                "-",
                "[dim]NO DATA[/dim]",
                "-",
                f"[dim]Awaiting messages in tab [{active_tab_name}]...[/dim]",
            )
        else:
            for msg in page_items:
                color = self.get_color(msg["category"])
                conf_val = msg["confidence"] * 100
                if conf_val >= 90:
                    conf_style = "bold bright_green"
                elif conf_val >= 70:
                    conf_style = "bold bright_yellow"
                else:
                    conf_style = "bold bright_red"

                sim_tag = " [sim]" if msg.get("is_simulation") else ""
                cat_badge = f"[{color}][{msg['category']}]{sim_tag}[/{color}]"

                table.add_row(
                    msg["time"],
                    msg["group"],
                    msg["sender"],
                    cat_badge,
                    f"[{conf_style}]{conf_val:.0f}%[/{conf_style}]",
                    msg["text"],
                )

        feed_title = f"[bold green]LIVE FEED[/bold green] [dim]-- viewing [{active_tab_name}] ({len(filtered)} msgs)[/dim]"
        table_panel = Panel(
            table,
            title=feed_title,
            border_style="bright_black",
            box=box.ROUNDED,
        )

        # 4. Rodapé com Atalhos de Teclado
        footer_text = Text()
        footer_text.append("NAVIGATE: ", style="bold bright_black")
        footer_text.append("[TAB / ->] ", style=f"bold {ARCH_CYAN}")
        footer_text.append("NEXT  ", style="dim white")
        footer_text.append("[S-TAB / <-] ", style=f"bold {ARCH_CYAN}")
        footer_text.append("PREV  ", style="dim white")
        footer_text.append("[0-9] ", style=f"bold {ARCH_CYAN}")
        footer_text.append("TAB NUM  ", style="dim white")
        footer_text.append("[A] ", style=f"bold {ARCH_CYAN}")
        footer_text.append("ALL  ", style="dim white")
        footer_text.append("[C] ", style=f"bold {ARCH_CYAN}")
        footer_text.append("CLEAR  ", style="dim white")
        footer_text.append("[Q] ", style="bold red")
        footer_text.append("QUIT", style="dim white")

        footer_panel = Panel(
            footer_text,
            border_style="bright_black",
            box=box.ROUNDED,
            padding=(0, 1),
        )

        return Group(header_panel, tabs_panel, table_panel, footer_panel)


class KeyboardController:
    """Captura teclas de atalho do teclado sem bloquear o loop assíncrono."""

    def __init__(self, dashboard: CliDashboard, shutdown_callback: Optional[Callable[[], None]] = None):
        self.dashboard = dashboard
        self.shutdown_callback = shutdown_callback
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.old_settings = None

    def start(self) -> None:
        if not sys.stdin.isatty():
            return
        try:
            import termios
            import tty

            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            self.running = True
            self._task = asyncio.create_task(self._listen())
        except Exception:
            pass

    async def _listen(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            while self.running:
                ch = await loop.run_in_executor(None, sys.stdin.read, 1)
                if not ch:
                    break

                if ch == "\x1b":  # Sequência ANSI de escape
                    seq = await loop.run_in_executor(None, sys.stdin.read, 2)
                    if seq == "[C":  # Seta direita
                        self.dashboard.next_tab()
                    elif seq == "[D":  # Seta esquerda
                        self.dashboard.prev_tab()
                    elif seq == "[Z":  # Shift + Tab
                        self.dashboard.prev_tab()
                elif ch == "\t":  # Tab
                    self.dashboard.next_tab()
                elif ch in ("q", "Q", "\x03"):  # q ou Ctrl+C
                    if self.shutdown_callback:
                        self.shutdown_callback()
                    break
                elif ch in ("a", "A"):
                    self.dashboard.set_tab_index(0)
                elif ch in ("c", "C"):
                    self.dashboard.clear_messages()
                elif ch.isdigit():
                    self.dashboard.set_tab_index(int(ch))
                elif ch == "h":
                    self.dashboard.prev_tab()
                elif ch == "l":
                    self.dashboard.next_tab()
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def stop(self) -> None:
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
        if self.old_settings and sys.stdin.isatty():
            try:
                import termios

                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except Exception:
                pass
