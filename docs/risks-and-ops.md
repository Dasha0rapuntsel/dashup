# Риски и эксплуатация

## Highload и надёжность

- Синхронный путь ограничен redaction, classification и routing с p95 ≤ 500 мс; генерация вынесена из него.
- Очередь и отдельные worker pools поглощают пики 10–20 тысяч тикетов; high-risk и incident получают приоритет.
- Идемпотентность, bounded retries, DLQ и reconciliation защищают от дублей и потерь.
- При проблемах LLM включается retrieval-only или operator-only режим — приём тикетов не останавливается.

## Privacy, safety и risk

- Raw PII хранится отдельно и шифруется; внешнему LLM доступны только masked text и минимальный approved context.
- Payment, takeover, legal/security, обнаруженный PII и low-confidence нельзя закрывать автоматически — нужен оператор.
- Текст пользователя недоверенный: он отделён от инструкций, retrieval ограничен approved KB, а injection/output checks могут заблокировать ответ.
- Audit хранит версии и причины без текста; критическая утечка или unsafe ответ немедленно включает kill switch.

