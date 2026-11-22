"""Клиент e-ink дисплея: скачивает кадр с сервера и выводит его на экран.

Цикл: GET /frame с If-None-Match -> 304 ничего не делаем / 200 выводим PNG -> ждём X-Refresh-After.
Запуск на Raspberry Pi: EINK_SERVER_URL=http://host:8080 python3 client.py
"""

import argparse
import io
import logging
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

WIDTH, HEIGHT = 800, 480
DEFAULT_REFRESH = 60  # секунд: если сервер не прислал X-Refresh-After или недоступен
MIN_REFRESH, MAX_REFRESH = 5, 60
HTTP_TIMEOUT = 30

log = logging.getLogger("eink-client")


class Shutdown:
    """SIGTERM (systemctl stop) и Ctrl+C не прерывают обновление дисплея.

    Вне обновления выходим сразу. Во время обновления запоминаем запрос,
    дорисовываем, усыпляем дисплей и выходим после этого.
    """

    def __init__(self):
        self.busy = False
        self.requested = False
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle)

    def _handle(self, signum, _frame):
        self.requested = True
        if not self.busy:
            raise SystemExit(0)
        log.info("signal %d: finishing display update first", signum)

    def __enter__(self):
        self.busy = True

    def __exit__(self, *exc):
        self.busy = False
        if self.requested:
            raise SystemExit(0)


@dataclass
class Frame:
    image: Image.Image | None  # None, если 304 Not Modified
    etag: str | None
    refresh_after: int


def parse_refresh(value):
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return DEFAULT_REFRESH
    return max(MIN_REFRESH, min(MAX_REFRESH, seconds))


def fetch_frame(url, etag):
    request = urllib.request.Request(url)
    if etag:
        request.add_header("If-None-Match", etag)
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            body = response.read()
            headers = response.headers
    except urllib.error.HTTPError as e:
        if e.code != 304:
            raise
        return Frame(None, e.headers.get("ETag") or etag, parse_refresh(e.headers.get("X-Refresh-After")))

    image = Image.open(io.BytesIO(body))
    image.load()
    return Frame(image, headers.get("ETag"), parse_refresh(headers.get("X-Refresh-After")))


def split_layers(image):
    """PNG -> (black, red), оба в режиме "1": 0 там, где пиксель этого цвета, 255 — белый."""
    if image.size != (WIDTH, HEIGHT):
        raise ValueError(f"frame is {image.size[0]}x{image.size[1]}, expected {WIDTH}x{HEIGHT}")
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, "white")
    rgb = np.asarray(Image.alpha_composite(background, rgba).convert("RGB"), dtype=np.int16)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    red = (r >= 128) & (g < 128) & (b < 128)
    black = ~red & (r + g + b < 3 * 128)
    # Из bool-массива Pillow делает картинку "1": True = белый, False = цвет слоя
    return Image.fromarray(~black), Image.fromarray(~red)


class Display:
    """Обёртка над драйвером: init -> display -> sleep на каждый кадр."""

    def __init__(self):
        sys.path.insert(0, str(Path(__file__).parent / "vendor"))
        from waveshare_epd import epd7in5b_V2

        self.epd = epd7in5b_V2.EPD()

    def show(self, black, red):
        if self.epd.init() != 0:
            raise RuntimeError("display init failed")
        try:
            started = time.monotonic()
            self.epd.display(self.epd.getbuffer(black), self.epd.getbuffer(red))
            log.info("displayed in %.1f s", time.monotonic() - started)
        finally:
            self.epd.sleep()


class DryRunDisplay:
    """Вместо дисплея сохраняет кадр в PNG: для отладки без железа."""

    def __init__(self, path):
        self.path = path

    def show(self, black, red):
        out = Image.new("RGB", (WIDTH, HEIGHT), "white")
        out.paste((0, 0, 0), mask=black.point(lambda v: 255 - v))
        out.paste((255, 0, 0), mask=red.point(lambda v: 255 - v))
        out.save(self.path)
        log.info("dry run: saved %s", self.path)


def run(server_url, display, shutdown, once=False):
    url = server_url.rstrip("/") + "/frame"
    etag = None
    shown = None  # байты последних выведенных слоёв, чтобы не перерисовывать одно и то же
    while True:
        try:
            frame = fetch_frame(url, etag)
            if frame.image is None:
                log.info("304 not modified")
            else:
                black, red = split_layers(frame.image)
                layers = (black.tobytes(), red.tobytes())
                if layers == shown:
                    log.info("200, image unchanged, skip redraw")
                else:
                    log.info("200, new frame (etag %s)", frame.etag)
                    with shutdown:
                        display.show(black, red)
                    shown = layers
            etag = frame.etag
            wait = frame.refresh_after
        except Exception as e:  # сервер недоступен, битый PNG и т.п.: картинка остаётся, пробуем позже
            log.error("frame update failed: %s", e)
            wait = DEFAULT_REFRESH
        if once:
            break
        log.info("next check in %d s", wait)
        time.sleep(wait)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--once", action="store_true", help="один запрос к серверу и выход")
    parser.add_argument("--dry-run", metavar="PNG", help="не трогать дисплей, сохранить кадр в файл")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server_url = os.environ.get("EINK_SERVER_URL")
    if not server_url:
        log.error("EINK_SERVER_URL is not set")
        return 2

    shutdown = Shutdown()
    display = DryRunDisplay(args.dry_run) if args.dry_run else Display()
    log.info("server %s", server_url)
    try:
        run(server_url, display, shutdown, once=args.once)
    finally:
        log.info("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
