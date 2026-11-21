# eink-dashboard

Приложение для вывода информации на e-ink дисплей.

Это монорепозиторий: здесь собраны все части проекта.

## Структура

| Каталог | Описание |
|---|---|
| [`eink-dashboard-server`](eink-dashboard-server) | Сервер на Java (Spring Boot) |

Позже появятся клиент на Python и другие компоненты.

## Сервер

Нужен JDK 27. Maven ставить не нужно: используется Maven Wrapper.

```sh
cd eink-dashboard-server
./mvnw spring-boot:run
```
