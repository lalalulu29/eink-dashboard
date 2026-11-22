package com.kirill.eink_dashboard_server.frame;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

/**
 * Контракт с клиентом (см. eink-dashboard-python-client/README.md):
 * GET /frame -> PNG 800x480, ETag = хеш картинки, 304 если не изменилась, X-Refresh-After в секундах.
 */
@RestController
public class FrameController {

    private static final int REFRESH_AFTER_SECONDS = 60;

    private final HtmlRenderer renderer;
    private final String weatherHtml;

    public FrameController(HtmlRenderer renderer) throws IOException {
        this.renderer = renderer;
        this.weatherHtml = new ClassPathResource("html/weather.html").getContentAsString(StandardCharsets.UTF_8);
    }

    @GetMapping("/frame")
    public ResponseEntity<byte[]> frame(@RequestHeader(value = HttpHeaders.IF_NONE_MATCH, required = false) String ifNoneMatch) {
        byte[] png = EinkPalette.quantizePng(renderer.render(weatherHtml));
        String etag = "\"" + HexFormat.of().formatHex(sha256(png), 0, 8) + "\"";

        if (etag.equals(ifNoneMatch)) {
            return ResponseEntity.status(HttpStatus.NOT_MODIFIED)
                    .eTag(etag)
                    .header("X-Refresh-After", String.valueOf(REFRESH_AFTER_SECONDS))
                    .build();
        }
        return ResponseEntity.ok()
                .eTag(etag)
                .header("X-Refresh-After", String.valueOf(REFRESH_AFTER_SECONDS))
                .contentType(MediaType.IMAGE_PNG)
                .body(png);
    }

    private static byte[] sha256(byte[] data) {
        try {
            return MessageDigest.getInstance("SHA-256").digest(data);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
