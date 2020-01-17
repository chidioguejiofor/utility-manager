class RedisMock:
    cache = {}
    expired_cache = {}

    @classmethod
    def set(cls, key, value):
        cls.cache[key] = value

    @classmethod
    def delete(cls, key):
        if key in cls.cache:
            del cls.cache[key]

    @classmethod
    def get(cls, key):
        return cls.cache.get(key)

    @classmethod
    def expire(cls, key, exp_time):
        cls.expired_cache[key] = exp_time

    @classmethod
    def flush_all(cls):
        cls.cache = {}
        cls.expired_cache = {}
