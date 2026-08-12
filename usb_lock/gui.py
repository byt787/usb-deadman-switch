"""usb_lock/gui.py

Kleines randloses, schwarzes quadratisches Fenster mit einem On/Off-Switch
in der Mitte. Der Switch steuert, ob eine erkannte USB-Entfernung tatsaechlich
den Bildschirm sperrt (ON) oder ignoriert wird (OFF). Der USB-Watcher laeuft
dabei durchgehend im Hintergrund-Thread; der Switch schaltet nur, ob die
Sperr-Aktion ausgefuehrt wird.

Start:
    python -m usb_lock.gui
"""
from __future__ import annotations

import platform
import sys
import threading
import time

import pygame

from usb_lock.config import Config
from usb_lock.lock import lock_screen

# ---------------------------------------------------------------- Layout ---
WINDOW_SIZE = 300

BG_COLOR = (0, 0, 0)
ON_COLOR = (60, 200, 90)
OFF_COLOR = (95, 95, 95)
KNOB_COLOR = (235, 235, 235)
LABEL_ON_COLOR = (60, 200, 90)
LABEL_OFF_COLOR = (150, 150, 150)
WATERMARK_COLOR = (48, 48, 48)
CLOSE_COLOR = (90, 90, 90)
CLOSE_HOVER_COLOR = (200, 60, 60)

SWITCH_W, SWITCH_H = 140, 60
SWITCH_X = (WINDOW_SIZE - SWITCH_W) // 2
SWITCH_Y = (WINDOW_SIZE - SWITCH_H) // 2
SWITCH_RECT = pygame.Rect(SWITCH_X, SWITCH_Y, SWITCH_W, SWITCH_H)

CLOSE_RADIUS = 8
CLOSE_CENTER = (WINDOW_SIZE - 16, 16)


# --------------------------------------------------------------- Zustand ---
class SwitchState:
    """Thread-sicherer An/Aus-Zustand, von GUI-Thread und Watcher-Thread genutzt."""

    def __init__(self, enabled: bool = True) -> None:
        self._lock = threading.Lock()
        self._enabled = enabled

    def toggle(self) -> bool:
        with self._lock:
            self._enabled = not self._enabled
            return self._enabled

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ------------------------------------------------------------ USB-Watcher --
def _start_watcher_thread(cfg: Config, state: SwitchState) -> None:
    system = platform.system()
    if system == "Windows":
        from usb_lock import watcher_windows as watcher
    elif system == "Linux":
        from usb_lock import watcher_linux as watcher
    else:
        _log(f"Betriebssystem '{system}' wird nicht unterstuetzt.")
        return

    def on_remove(info) -> None:
        if not state.is_enabled():
            _log(f"USB entfernt ({info}) - Schalter ist AUS, ignoriert.")
            return
        _log(f"USB entfernt ({info}) - sperre Bildschirm.")
        if cfg.lock_delay > 0:
            time.sleep(cfg.lock_delay)
        lock_screen()

    def run() -> None:
        try:
            watcher.watch(
                on_remove=on_remove,
                mode=cfg.mode,
                specific_devices=cfg.specific_devices,
                poll_interval=cfg.poll_interval,
            )
        except Exception as exc:  # Watcher soll die GUI nie mitreissen
            _log(f"Watcher-Fehler: {exc}")

    threading.Thread(target=run, daemon=True).start()


# -------------------------------------------------------------- Zeichnen ---
def draw(surface: "pygame.Surface", fonts, state: SwitchState, mouse_pos) -> None:
    surface.fill(BG_COLOR)

    is_on = state.is_enabled()

    # Switch-Track
    track_color = ON_COLOR if is_on else OFF_COLOR
    pygame.draw.rect(surface, track_color, SWITCH_RECT, border_radius=SWITCH_H // 2)

    # Switch-Knopf
    knob_radius = SWITCH_H // 2 - 6
    knob_y = SWITCH_Y + SWITCH_H // 2
    knob_x = (
        SWITCH_X + SWITCH_W - SWITCH_H // 2
        if is_on
        else SWITCH_X + SWITCH_H // 2
    )
    pygame.draw.circle(surface, KNOB_COLOR, (knob_x, knob_y), knob_radius)

    # Status-Label ueber dem Switch
    label_font, small_font = fonts
    label_text = "ON" if is_on else "OFF"
    label_color = LABEL_ON_COLOR if is_on else LABEL_OFF_COLOR
    label_surf = label_font.render(label_text, True, label_color)
    label_rect = label_surf.get_rect(center=(WINDOW_SIZE // 2, SWITCH_Y - 28))
    surface.blit(label_surf, label_rect)

    # Schliessen-Button (kleiner Punkt oben rechts, da kein Fensterrahmen)
    hovered = (
        (mouse_pos[0] - CLOSE_CENTER[0]) ** 2 + (mouse_pos[1] - CLOSE_CENTER[1]) ** 2
        <= (CLOSE_RADIUS + 4) ** 2
    )
    close_color = CLOSE_HOVER_COLOR if hovered else CLOSE_COLOR
    pygame.draw.circle(surface, close_color, CLOSE_CENTER, CLOSE_RADIUS)

    # Wasserzeichen unten rechts
    watermark_surf = small_font.render("milka161", True, WATERMARK_COLOR)
    watermark_rect = watermark_surf.get_rect(
        bottomright=(WINDOW_SIZE - 10, WINDOW_SIZE - 8)
    )
    surface.blit(watermark_surf, watermark_rect)


# ------------------------------------------------------------------ Main ---
def main() -> None:
    import os

    # Fenster beim Start auf dem Bildschirm zentrieren.
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

    pygame.init()
    pygame.display.set_caption("usb-lock")

    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE), pygame.NOFRAME)

    label_font = pygame.font.SysFont("arial", 22, bold=True)
    small_font = pygame.font.SysFont("arial", 13)
    fonts = (label_font, small_font)

    cfg = Config.load()
    state = SwitchState(enabled=True)
    _start_watcher_thread(cfg, state)
    _log(f"GUI gestartet (OS={platform.system()}, mode={cfg.mode}).")

    # Bestes-Bemuehen-Drag: haelt man die linke Maustaste auf dem Hintergrund
    # gedrueckt (nicht auf Switch/Close), kann man das Fenster verschieben.
    try:
        from pygame._sdl2.video import Window

        sdl_window = Window.from_display_module()
    except Exception:
        sdl_window = None

    dragging = False
    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dx = event.pos[0] - CLOSE_CENTER[0]
                dy = event.pos[1] - CLOSE_CENTER[1]
                if dx * dx + dy * dy <= (CLOSE_RADIUS + 4) ** 2:
                    running = False
                elif SWITCH_RECT.collidepoint(event.pos):
                    new_state = state.toggle()
                    _log(f"Schalter -> {'ON' if new_state else 'OFF'}")
                elif sdl_window is not None:
                    dragging = True
                    pygame.mouse.get_rel()  # Delta-Puffer zuruecksetzen

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging and sdl_window is not None:
                rel_x, rel_y = event.rel
                x, y = sdl_window.position
                sdl_window.position = (x + rel_x, y + rel_y)

        draw(screen, fonts, state, mouse_pos)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
