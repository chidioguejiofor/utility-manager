import pytest
from api.models import User


class TestFirstTest:
    def test_start(self, app, init_db):
        assert User.query.all() != None
