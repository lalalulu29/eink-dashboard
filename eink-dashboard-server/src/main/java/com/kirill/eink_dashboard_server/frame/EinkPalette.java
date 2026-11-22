package com.kirill.eink_dashboard_server.frame;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UncheckedIOException;

import javax.imageio.ImageIO;

/**
 * Переводит картинку в палитру дисплея: чёрный, белый, красный.
 *
 * Chromium сглаживает края, и у тонкого текста почти все пиксели полупрозрачные.
 * Поэтому пороги подобраны так, чтобы край, закрашенный примерно на треть, ещё считался цветом:
 * - красный — по оттенку (R заметно больше G и B), а не по яркости: розовые края красного текста остаются красными;
 * - чёрный — по яркости, с порогом выше середины: тонкие штрихи не пропадают.
 */
public final class EinkPalette {

    public static final int BLACK = 0x000000;
    public static final int WHITE = 0xFFFFFF;
    public static final int RED = 0xFF0000;

    /** Минимум R - max(G, B), чтобы пиксель считался красным. */
    static final int RED_MIN_DOMINANCE = 50;
    /** Яркость (0..255) ниже этого порога считается чёрным. */
    static final int BLACK_MAX_LUMA = 160;

    private EinkPalette() {
    }

    public static byte[] quantizePng(byte[] png) {
        try {
            BufferedImage src = ImageIO.read(new ByteArrayInputStream(png));
            var out = new ByteArrayOutputStream();
            ImageIO.write(quantize(src), "png", out);
            return out.toByteArray();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public static BufferedImage quantize(BufferedImage src) {
        int w = src.getWidth();
        int h = src.getHeight();
        var out = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                out.setRGB(x, y, toPalette(src.getRGB(x, y)));
            }
        }
        return out;
    }

    static int toPalette(int rgb) {
        int r = (rgb >> 16) & 0xFF;
        int g = (rgb >> 8) & 0xFF;
        int b = rgb & 0xFF;
        if (r - Math.max(g, b) >= RED_MIN_DOMINANCE) {
            return RED;
        }
        int luma = (r * 299 + g * 587 + b * 114) / 1000;
        return luma < BLACK_MAX_LUMA ? BLACK : WHITE;
    }
}
