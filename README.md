# Railway Visa Monitor (YATRI_SESSION only)

Минимальный монитор слотов (Vancouver) без HAR. Авторизация — через переменную `YATRI_SESSION` (значение после `_yatri_session=`).

## Переменные (Railway → Variables)
- `APPOINTMENTS_URL` = `https://ais.usvisa-info.com/en-ca/niv/schedule/69597284/appointment/days/95.json?appointments[expedite]=false`
- `YATRI_SESSION`    = **вставь ТОЛЬКО значение после `_yatri_session=`**
- `TG_BOT_TOKEN`     = токен бота из BotFather
- `TG_CHAT_ID`       = кому слать уведомления (например `394276302`)
- `POLL_SECONDS`     = 300 (по желанию)
- `MODE`             = `once` (для теста) или `loop` (боевой режим)

## Запуск на Railway
1. Залей файлы в приватный GitHub.
2. Railway → New Project → Deploy from GitHub repo.
3. Добавь Variables (см. выше).
4. Start Command не нужен (Procfile уже есть).
5. Нажми Redeploy и смотри Logs.
