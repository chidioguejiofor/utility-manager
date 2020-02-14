import os
import redis
from api.utils.id_generator import IDGenerator

from tests.mocks.redis import RedisMock


class RedisUtil:
    REDIS = RedisMock
    if os.getenv('FLASK_ENV') != 'testing':
        REDIS = redis.from_url(os.getenv('REDIS_SERVER_URL'))

    @classmethod
    def set(cls, key, value, expiry_time=None):
        cls.REDIS.set(key, value)
        cls.REDIS.expire(key, int(expiry_time.total_seconds()))

    @classmethod
    def set_value(cls, value, expiry_time):
        """Caches a value to redis.

        It generates a unique key for the new redis value.
        This value would be removed once the expiry time is reached

        Args:
            value (str): The value to be cached. Must be a string
            expiry_time  (datetime.timedelta): When the value should be auto deleted from redis

        Returns:
            str: a the unique key that was generated for the value
        """
        unique_key = IDGenerator.generate_id()
        success = cls.REDIS.set(unique_key, value)
        cls.REDIS.expire(unique_key, int(expiry_time.total_seconds()))
        return unique_key, success

    @classmethod
    def set_key(cls, key, value, expiry_time=None):
        cls.REDIS.set(key, value)
        if expiry_time:
            cls.REDIS.expire(key, int(expiry_time.total_seconds()))

    @classmethod
    def hset(cls, hash_name, key, value, expiry_time=None):
        custom_key = f'{hash_name}_{key}'
        cls.REDIS.set(custom_key, value)
        if expiry_time:
            cls.REDIS.expire(custom_key, int(expiry_time.total_seconds()))

    @classmethod
    def hget(cls, hash_name, key):
        value = cls.REDIS.get(f'{hash_name}_{key}')
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    @classmethod
    def find_keys(cls, regex):
        final_list = []
        for key in cls.REDIS.keys(regex):
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            final_list.append(key)
        return final_list

    @classmethod
    def delete_hash(cls, hash_name):
        hash_keys = cls.find_keys(f'{hash_name}*')
        for key in hash_keys:
            cls.REDIS.delete(key)

    @classmethod
    def get_key(cls, key):
        """Retrieves the value of a redis key

        Args:
            key str: An id that was previously generated by this class

        Returns:

        """
        return cls.REDIS.get(key)

    @classmethod
    def delete_key(cls, key):
        """Removes a key from redis.

        This is called to free up memory.

        Args:
            key:

        """
        return cls.REDIS.delete(key)

    @classmethod
    def get_role_id(cls, role_name):
        from api.models.role import Role
        role_key = f'ROLE_{role_name}'
        role_id = cls.get_key(role_key)

        if not role_id:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                cls.set_key(role_key, role.id)
                role_id = role.id
        if isinstance(role_id, bytes):
            return role_id.decode('utf-8')
        return role_id
