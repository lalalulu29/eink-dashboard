# waveshare_epd (vendored)

Файлы драйвера скопированы без изменений из официальной библиотеки Waveshare.

| Что | Значение |
|---|---|
| Источник | <https://github.com/waveshare/e-Paper> |
| Путь в репозитории | `RaspberryPi_JetsonNano/python/lib/waveshare_epd/` |
| Коммит | [`d28b3c4cfc78eef1c6cd6e6e3013654e449d2864`](https://github.com/waveshare/e-Paper/tree/d28b3c4cfc78eef1c6cd6e6e3013654e449d2864/RaspberryPi_JetsonNano/python/lib/waveshare_epd) (2026-10-27) |
| Лицензия | MIT. Текст лицензии находится в шапке каждого файла |

## Файлы

| Файл | Назначение |
|---|---|
| `epd7in5b_V2.py` | Драйвер 7.5" e-Paper (B), 800×480, чёрный/белый/красный |
| `epdconfig.py` | Работа с GPIO (gpiozero) и SPI (spidev), выбор платформы |
| `__init__.py` | Пустой, делает папку Python-пакетом |

Файлы не редактируем. Если нужно поменять поведение, пишем обёртку в коде клиента.

## Как обновить

```sh
git clone --depth 1 https://github.com/waveshare/e-Paper.git /tmp/e-Paper
cp /tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/{__init__.py,epdconfig.py,epd7in5b_V2.py} .
git -C /tmp/e-Paper rev-parse HEAD   # записать новый коммит в таблицу выше
```

## Если дисплей не работает

В библиотеке есть `epd7in5b_V2_old.py` для старых ревизий панели. Если на `epd7in5b_V2` экран не обновляется или зависает на BUSY, попробуй его.
