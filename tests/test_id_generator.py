from api.models.base.id_generator import IDGenerator
from unittest.mock import patch


@patch('time.time')
class TestIdGenerator:
    def test_should_generate_unique_id(self, mock_time):
        id_one = IDGenerator.generate_id()
        id_two = IDGenerator.generate_id()
        assert id_one != id_two

    def test_should_generate_different_id_in_the_same_time_stamp(
            self, mock_time):
        mock_time.return_value = 50001
        id_one = IDGenerator.generate_id()
        id_two = IDGenerator.generate_id()
        assert id_one != id_two
        assert mock_time.call_count == 2
