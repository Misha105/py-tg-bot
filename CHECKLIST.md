# Pre-Launch & Pre-Commit Checklist

- [ ] `.env` скопирован из `.env.example`, секреты (`BOT_TOKEN`, `OPENROUTER_API_KEY`) не закоммичены в репозиторий
- [ ] OpenRouter API key валиден, модель доступна
- [ ] `ALLOWED_USER_IDS` корректен: пусто = тестовый/открытый режим, иначе указаны только ваши Telegram ID
- [ ] Выполнено `make setup && make test` — все тесты проходят без ошибок и предупреждений
- [ ] Выполнено `make verify` — статус: ✅ Setup verification complete
- [ ] Проверены логи (stdout в консоли или панели) — отсутствуют `WARNING`/`ERROR` при старте и обработке сообщений
- [ ] Код отформатирован (`make lint`), нет `print()` в продакшен-ветке, используется только `logging`
