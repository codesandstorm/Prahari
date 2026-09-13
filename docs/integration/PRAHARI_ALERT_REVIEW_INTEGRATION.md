# PRAHARI Alert and Review Integration

Unified Project Intelligence exposes a read-only workflow summary: active alert count and IDs, latest alert/review states, priority, update and next-review dates, and the history endpoint. It does not create an alert merely by being read.

Alert evaluation reconstructs Unified Project Intelligence server-side, then applies the versioned policy. This prevents clients from directly supplying probabilities or raw signals as alert triggers. Real and sandbox evaluation use separate endpoints and origins.

The Assistant receives only the read-only workflow summary as additional project evidence. It cannot acknowledge, assign, resolve, dismiss or reopen an alert. It also cannot reinterpret an administrative priority as model risk.

Frontend consumers should treat the API contract as authoritative and keep these labels distinct: prediction status, reliability, Data Trust, Watch status, Officer Decision, alert severity/status and review priority/status.

Migration `20260913_02` extends alert episodes and creates append-only history, officer review, note and action tables. Run the normal Alembic upgrade before starting the API.

