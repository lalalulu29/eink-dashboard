package com.kirill.eink_dashboard_server.frame;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserContext;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;
import com.microsoft.playwright.options.WaitUntilState;
import org.springframework.stereotype.Component;

/**
 * Рендерит HTML в PNG 800x480 через headless Chromium (Playwright).
 * Браузер запускается один раз при старте и закрывается вместе с приложением.
 */
@Component
public class HtmlRenderer implements AutoCloseable {

    public static final int WIDTH = 800;
    public static final int HEIGHT = 480;

    private final Playwright playwright = Playwright.create();
    private final Browser browser = playwright.chromium().launch();

    /** Playwright не потокобезопасен, поэтому рендерим по одному кадру за раз. */
    public synchronized byte[] render(String html) {
        var options = new Browser.NewContextOptions()
                .setViewportSize(WIDTH, HEIGHT)
                .setDeviceScaleFactor(1);
        try (BrowserContext context = browser.newContext(options);
             Page page = context.newPage()) {
            // NETWORKIDLE: дождаться загрузки шрифтов Google Fonts
            page.setContent(html, new Page.SetContentOptions().setWaitUntil(WaitUntilState.NETWORKIDLE));
            page.evaluate("document.fonts.ready");
            return page.screenshot();
        }
    }

    @Override
    public void close() {
        browser.close();
        playwright.close();
    }
}
