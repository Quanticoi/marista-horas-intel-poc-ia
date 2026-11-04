-- Durable enqueue claim prevents duplicate-delivery storms while retaining recovery.
ALTER TABLE planning.operation_jobs ADD COLUMN enqueued_at_utc timestamptz;
