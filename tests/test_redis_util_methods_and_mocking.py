from unittest.mock import Mock, patch
from .mocks.redis import RedisMock
from api.services.redis_util import RedisUtil
from api.models import Role


class TestRedisUtil:
    def test_get_role_id_should_make_db_call_when_the_role_is_not_in_redis_and_set_the_key(
            self, init_db, client):
        RedisMock.flush_all()
        RedisMock.delete('ROLE_OWNER')

        assert RedisMock.get('ROLE_OWNER') == None
        owner_role = RedisUtil.get_role_id('OWNER')
        assert Role.query.filter_by(name='OWNER').one().id == owner_role
        assert RedisMock.get('ROLE_OWNER') == owner_role

    #
    # def test_set_method_should_not_be_called_when_id_exists_in_redis(
    #         self, mock_redis_set, mock_redis_get, init_db, client):
    #     RedisMock.flush_all()
    #     mock_redis_get.side_effect = RedisMock.get
    #     mock_redis_set.side_effect = RedisMock.set
    #     owner_role = RedisUtil.get_role_id('OWNER')
    #     assert Role.query.filter_by(name='OWNER').one().id == owner_role
    #     assert mock_redis_get.called
    #     assert mock_redis_set.called
    #     assert mock_redis_set.call_args[0] == ('ROLE_OWNER', owner_role)
    #     assert mock_redis_get.call_args[0] == ('ROLE_OWNER', )
    #     assert RedisMock.get('ROLE_OWNER') == owner_role
