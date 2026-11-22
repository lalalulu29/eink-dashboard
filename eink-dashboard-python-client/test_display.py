"""Тестовая картинка на дисплее, без сервера.

Проверяет, что драйвер подходит к дисплею и что красный слой выводится.
Запуск на Raspberry Pi: python3 test_display.py
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent / "vendor"))
from waveshare_epd import epd7in5b_V2  # noqa: E402

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(str(FONT_DIR / name), size)
    except OSError:
        return ImageFont.load_default(size)


def draw_test(width, height):
    # Оба слоя: белый фон, рисуем цветом 0. На black-слое 0 = чёрный, на red-слое 0 = красный.
    black = Image.new("1", (width, height), 255)
    red = Image.new("1", (width, height), 255)
    b = ImageDraw.Draw(black)
    r = ImageDraw.Draw(red)

    r.rectangle((10, 10, width - 11, height - 11), outline=0, width=8)
    b.text((50, 50), "eink-dashboard", font=font(64, bold=True), fill=0)
    r.text((50, 140), "red layer OK", font=font(48, bold=True), fill=0)
    b.text((50, 220), "black layer OK", font=font(48), fill=0)
    b.text((50, 400), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), font=font(32), fill=0)

    # Полосы для проверки: чёрная, красная, белая
    b.rectangle((width - 260, 300, width - 200, 380), fill=0)
    r.rectangle((width - 180, 300, width - 120, 380), fill=0)
    b.rectangle((width - 100, 300, width - 40, 380), outline=0, width=2)
    return black, red


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    epd = epd7in5b_V2.EPD()
    try:
        logging.info("init")
        if epd.init() != 0:
            logging.error("init failed")
            return 1
        black, red = draw_test(epd.width, epd.height)
        logging.info("display")
        started = time.monotonic()
        epd.display(epd.getbuffer(black), epd.getbuffer(red))
        logging.info("done in %.1f s", time.monotonic() - started)
        return 0
    finally:
        logging.info("sleep")
        epd.sleep()


if __name__ == "__main__":
    sys.exit(main())
