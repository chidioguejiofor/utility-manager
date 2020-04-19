import pytest
from api.schemas import UnitSchema
from api.utils.error_messages import model_operations, serialization_error
from api.models import Unit
from api.utils.exceptions import UniqueConstraintException, ModelOperationException


def create_test_precondition(init_db):
    Unit.query.delete()
    init_db.session.commit()


class TestUnitSerializer:
    def test_convert_unit_model_to_json(self, init_db):
        create_test_precondition(init_db)
        unit = Unit(name='Ampere', symbol='A')
        unit.save()
        json_data = UnitSchema().dump_success_data(unit)
        assert json_data['data']['id'] == unit.id
        assert json_data['data']['name'] == unit.name
        assert json_data['data']['symbol'] == unit.symbol
        assert json_data['data']['organisationId'] is None

    def test_loading_json_to_model_when_data_is_valid_should_succeed(
        self, init_db):
        create_test_precondition(init_db)
        unit_dict = {
            'name': 'Voltage',
            'symbol': 'V',
            'organisationId': 'som_id',
        }

        unit = UnitSchema().load(unit_dict)
        assert unit.name == unit_dict['name']
        assert unit.symbol == unit_dict['symbol']


class TestUnitModel:
    def test_should_save_user_to_db_successfully_when_data_is_valid(
        self, init_db):
        create_test_precondition(init_db)
        Unit(name='Meters', symbol='m').save()

        unit = Unit.query.filter_by(name='Meters', symbol='m').first()
        assert unit.name == 'Meters'
        assert unit.symbol == 'm'

    def test_should_not_save_unit_and_symbol_pair_twice(self, init_db):
        create_test_precondition(init_db)
        Unit(name='Hertz', symbol='Hz').save()
        with pytest.raises(UniqueConstraintException) as e:
            Unit(name='Hertz', symbol='Hz').save()
        assert e.value.message == serialization_error['exists_in_org'].format(
            'Unit')

    def test_should_not_save_model_when__symbol_is_null(self, init_db):
        create_test_precondition(init_db)
        with pytest.raises(ModelOperationException) as e:
            Unit(
                name='Hertz',
                symbol=None,
            ).save()

        assert e.value.message == model_operations[
            'column_must_have_a_value'].format('symbol')
        assert e.value.api_message == model_operations[
            'column_must_have_a_value'].format('symbol')
