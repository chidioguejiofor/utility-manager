from datetime import datetime, timezone


class TimeUtil:
    @classmethod
    def now(cls):
        return datetime.now(timezone.utc)

    @classmethod
    def generate_time_before_update(cls, mapper, connection, target):
        target.updated_at = cls.now()
