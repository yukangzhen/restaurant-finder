import unittest

from src.infrastructure.observability import ObservabilityManager


class _Metric:
    def __init__(self):
        self.values = []

    def add(self, value, attributes):
        self.values.append((value, attributes))

    def record(self, value, attributes):
        self.values.append((value, attributes))


class _OtelLogger:
    def __init__(self):
        self.records = []

    def emit(self, record):
        self.records.append(record)


class ObservabilityTests(unittest.TestCase):
    def test_memory_metrics_and_logs_use_only_low_cardinality_attributes(self):
        manager = ObservabilityManager(enabled=False)
        counter = _Metric()
        duration = _Metric()
        otel_logger = _OtelLogger()
        manager._memory_save_counter = counter
        manager._memory_duration = duration
        manager._otel_logger = otel_logger

        manager.record_memory_operation(
            "save", success=True, duration_ms=12.5, category="preferences"
        )

        self.assertEqual(counter.values[0][0], 1)
        self.assertEqual(
            counter.values[0][1],
            {"operation": "save", "status": "success", "category": "preferences"},
        )
        attributes = otel_logger.records[0].attributes
        self.assertEqual(
            set(attributes), {"operation", "status", "category"}
        )
        self.assertNotIn("actor.id", attributes)
        self.assertNotIn("user.input", attributes)
        self.assertEqual(duration.values[0][0], 12.5)


if __name__ == "__main__":
    unittest.main()
