# eink-dashboard-python-client

Клиент для e-ink дисплея на Raspberry Pi.

Клиент ничего не решает сам. Он скачивает с сервера готовую картинку, выводит её на дисплей и ждёт.
Вся логика (какой экран показать, layout, данные) живёт на сервере ([`eink-dashboard-server`](../eink-dashboard-server)).

## Оборудование

| Компонент | Модель |
|---|---|
| Плата | Raspberry Pi Zero 2W |
| Дисплей | Waveshare 7.5" e-Paper (B), 800×480, три цвета: чёрный, белый, красный |
| Адаптер | Waveshare Universal e-Paper Driver HAT |
| Интерфейс | SPI |

Особенности трёхцветного дисплея:

- Полное обновление занимает около 20–25 секунд, частичного обновления нет.
  Поэтому перерисовываем экран только тогда, когда картинка изменилась.
- Картинка передаётся двумя слоями: чёрный и красный.
- Между обновлениями дисплей переводится в режим сна (`epd.sleep()`). Если долго держать его под напряжением, он может испортиться.

## Подключение

Driver HAT подключается к Pi через шлейф (или напрямую на GPIO). Переключатели на HAT:

- **Interface Config**: `0` (4-wire SPI).
- **Display Config**: значение для 7.5" модели смотри в [вики Waveshare](https://www.waveshare.com/wiki/E-Paper_Driver_HAT).

Распиновка (BCM):

| Пин HAT | GPIO Raspberry Pi |
|---|---|
| VCC | 3.3V |
| GND | GND |
| DIN | GPIO10 (MOSI) |
| CLK | GPIO11 (SCLK) |
| CS | GPIO8 (CE0) |
| DC | GPIO25 |
| RST | GPIO17 |
| BUSY | GPIO24 |
| PWR | GPIO18 (есть только на новых ревизиях HAT) |

## Библиотека дисплея

Официальная библиотека: <https://github.com/waveshare/e-Paper>

Из неё нужны только два файла из `RaspberryPi_JetsonNano/python/lib/waveshare_epd/`:

- `epd7in5b_V2.py` (драйвер дисплея 7.5" B, 800×480)
- `epdconfig.py` (работа с GPIO и SPI)

Они лежат в [`vendor/waveshare_epd/`](vendor/waveshare_epd) без изменений и коммитятся в репозиторий (vendoring). Ставить библиотеку целиком не нужно.
Лицензия MIT, её текст есть в шапке каждого файла. Источник, коммит и инструкция по обновлению описаны в [`vendor/waveshare_epd/README.md`](vendor/waveshare_epd/README.md).

## Настройка с нуля

Код редактируем на своём компьютере, а запускаем на Raspberry Pi: дисплей подключён к Pi.
Связь между ними идёт по SSH.

В примерах ниже `<user>` — пользователь на Pi, `<pi>` — IP-адрес или hostname Pi.

Проверено на Raspberry Pi Zero 2W, Debian 13 (trixie), Python 3.13.

### 1. SSH-доступ по ключу

Делается на своём компьютере. Команды интерактивные: SSH спросит про fingerprint и пароль.
Поэтому запускать их нужно в обычном терминале, не из IDE и не из AI-агента.

```sh
# Создать ключ, если его ещё нет (ls ~/.ssh/*.pub)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "eink-pi"

# Подтвердить fingerprint хоста (ответить yes) и скопировать ключ на Pi (ввести пароль)
ssh-copy-id -i ~/.ssh/id_ed25519.pub <user>@<pi>

# Проверка: должно пустить без пароля
ssh <user>@<pi> hostname
```

Чтобы не писать адрес каждый раз, можно добавить в `~/.ssh/config`:

```
Host eink-pi
    HostName <pi>
    User <user>
    IdentityFile ~/.ssh/id_ed25519
```

Дальше все команды на Pi выполняются по SSH.

### 2. Включить SPI

```sh
sudo raspi-config
# Interface Options → SPI → Enable
sudo reboot
```

Проверка: `ls /dev/spidev*` должен показать `/dev/spidev0.0`.

### 3. Права на SPI и GPIO

Пользователь должен быть в группах `spi` и `gpio`, тогда `sudo` для работы с дисплеем не нужен.

```sh
groups                          # должны быть spi и gpio
sudo usermod -aG spi,gpio $USER # если групп нет; потом перелогиниться
```

### 4. Системные пакеты

```sh
sudo apt update
sudo apt install -y python3-pil python3-numpy python3-spidev python3-gpiozero python3-lgpio python3-venv rsync fonts-dejavu-core
```

Пакеты ставим из apt, а не через pip: собирать numpy и Pillow на Zero 2W очень долго.
Шрифты DejaVu нужны для текста на тестовой картинке.

### 5. Скопировать клиент на Pi

С своего компьютера, из папки `eink-dashboard-python-client`:

```sh
rsync -av --exclude .venv --exclude __pycache__ ./ <user>@<pi>:~/eink-dashboard-python-client/
```

### 6. Тестовая картинка

```sh
ssh <user>@<pi> 'cd ~/eink-dashboard-python-client && python3 test_display.py'
```

Скрипт [`test_display.py`](test_display.py) работает без сервера. Макет этой картинки — фрейм `test-display` в [`design/screens.figcraft`](../design/screens.figcraft), превью: [`design/preview/test-display.png`](../design/preview/test-display.png). Нормальный вывод:

```
INFO init
INFO display
INFO done in 21.7 s
INFO sleep
```

На экране должно появиться:

- красная рамка по краю;
- **eink-dashboard** крупно, чёрным;
- **red layer OK** красным, **black layer OK** чёрным;
- дата и время внизу;
- справа три квадрата: чёрный, красный, белый с рамкой.

Если что-то не так:

| Симптом | Что проверить |
|---|---|
| Экран не меняется, скрипт висит на `display` | Подключение шлейфа, переключатели на HAT. Если не помогло, попробовать драйвер `epd7in5b_V2_old.py` для старых ревизий панели |
| Красное и чёрное перепутаны | Порядок слоёв в `epd.display(black, red)` |
| Шум или полосы на экране | Переключатель Display Config на HAT |
| `Permission denied` на `/dev/spidev0.0` или GPIO | Шаг 3: группы `spi` и `gpio` |
| `No such file or directory: /dev/spidev0.0` | Шаг 2: SPI не включён |

## Как работает клиент

Цикл:

1. `GET /frame` на сервере, с заголовком `If-None-Match: <последний ETag>`.
2. Если ответ `304 Not Modified`, ничего не делаем.
3. Если `200 OK`, берём PNG 800×480, делим на чёрный и красный слои, выводим на дисплей, отправляем дисплей в сон.
4. Ждём столько секунд, сколько сервер указал в `X-Refresh-After`.

Если сервер недоступен, на экране остаётся последняя картинка, клиент пробует снова через минуту.

Детали:

- ETag хранится только в памяти. После перезапуска клиент один раз перерисовывает экран: он не знает, что на нём сейчас.
- Если сервер ответил `200`, но картинка совпадает с выведенной (например, сервер не поддерживает `If-None-Match`), экран не перерисовывается.
- Цвета PNG раскладываются по слоям с порогом 128: красный — `R ≥ 128, G < 128, B < 128`, чёрный — тёмные пиксели, всё остальное белое. Сглаженные края в превью из figcraft округляются до ближайшего цвета.
- `X-Refresh-After` ограничивается диапазоном 5–60 секунд. Если заголовка нет или он некорректный, берётся 60.
- Кадр не 800×480 считается ошибкой: экран не трогаем, пробуем снова через минуту.
- `SIGTERM` и `Ctrl+C` не прерывают обновление дисплея: клиент дорисовывает кадр, переводит дисплей в сон и только потом выходит.

### Контракт с сервером

| Что | Значение |
|---|---|
| Endpoint | `GET /frame` |
| Ответ | PNG 800×480 из трёх цветов: чёрный, белый, красный |
| `ETag` | Хеш картинки. Если она не изменилась, сервер отвечает `304` |
| `X-Refresh-After` | Через сколько секунд спросить снова (не больше 60) |

## Настройки

Через переменные окружения:

| Переменная | Описание | Пример |
|---|---|---|
| `EINK_SERVER_URL` | Адрес сервера | `http://192.168.1.10:8080` |

## Запуск

Клиент — [`client.py`](client.py), зависимости только из apt (шаг 4).

```sh
ssh <user>@<pi> 'cd ~/eink-dashboard-python-client && EINK_SERVER_URL=http://<server>:8080 python3 client.py'
```

Флаги для отладки:

| Флаг | Что делает |
|---|---|
| `--once` | Один запрос к серверу, вывод кадра и выход |
| `--dry-run <file.png>` | Дисплей не трогается, кадр после разбора на слои сохраняется в PNG. Так видно, что именно попадёт на экран |

Нормальный вывод:

```
INFO server http://192.168.1.10:8080
INFO 200, new frame (etag "df8efba16294d026")
INFO displayed in 27.9 s
INFO next check in 60 s
INFO 304 not modified
```

План: клиент запускается как systemd-сервис (`eink-client.service`). Если понадобятся pip-зависимости, будет venv с `--system-site-packages`, чтобы он видел пакеты из apt.

## Деплой

С машины разработчика или из GitHub Actions:

```sh
rsync -av --exclude .venv --exclude __pycache__ ./ <user>@<pi>:~/eink-dashboard-python-client/
ssh <user>@<pi> sudo systemctl restart eink-client
```

## Статус

- [x] Vendoring драйвера Waveshare
- [x] Вывод тестовой картинки без сервера (`test_display.py`)
- [x] Получение кадра с сервера (`/frame`, `ETag`, `X-Refresh-After`), `client.py`
- [ ] systemd-сервис
- [ ] Деплой через rsync
