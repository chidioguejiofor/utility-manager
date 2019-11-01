import pytest
from api.schemas import UnitSchema
from api.utils.error_messages import model_operations, serialization_error
from api.models import Unit
from api.utils.exceptions import UniqueConstraintException, ModelOperationException


class TestUnitSerializer:
    def test_convert_unit_model_to_json(self, init_db):
        unit = Unit(name='Ampere', letter_symbol='A')
        unit.save()
        json_data = UnitSchema().dump_success_data(unit)
        assert json_data['data']['id'] == unit.id
        assert json_data['data']['name'] == unit.name
        assert json_data['data']['letterSymbol'] == unit.letter_symbol
        assert json_data['data']['greekSymbol'] is None
        assert json_data['data']['organisationId'] is None

    def test_loading_json_to_model_when_data_is_valid_should_succeed(
            self, init_db):
        unit_dict = {
            'name': 'Voltage',
            'letterSymbol': 'V',
            'organisationId': 'som_id',
        }

        unit = UnitSchema().load(unit_dict)
        assert unit.name == unit_dict['name']
        assert unit.letter_symbol == unit_dict['letterSymbol']


class TestUnitModel:
    def test_should_save_user_to_db_successfully_when_data_is_valid(
            self, init_db):
        Unit(name='Meters', letter_symbol='m').save()

        unit = Unit.query.filter_by(name='Meters', letter_symbol='m').first()
        assert unit.name == 'Meters'
        assert unit.letter_symbol == 'm'

    def test_should_not_save_unit_and_symbol_pair_twice(self, init_db):
        Unit(name='Hertz', letter_symbol='Hz').save()
        with pytest.raises(UniqueConstraintException) as e:
            Unit(name='Hertz', letter_symbol='Hz').save()
        assert e.value.message == serialization_error['exists_in_org'].format(
            'Unit')

    def test_should_not_save_model_with_greek_symbol_and_letter_symbol(
            self, init_db):
        with pytest.raises(ModelOperationException) as e:
            Unit(name='Hertz', letter_symbol='Hz', greek_symbol_num=20).save()

        assert e.value.message == model_operations[
            'both_greek_and_letter_are_provided'][0]
        assert e.value.api_message == model_operations[
            'both_greek_and_letter_are_provided'][1]

    def test_should_not_save_model_when_both_greek_symbol_and_letter_symbol_are_null(
            self, init_db):
        with pytest.raises(ModelOperationException) as e:
            Unit(name='Hertz', letter_symbol=None,
                 greek_symbol_num=None).save()

        assert e.value.message == model_operations[
            'both_greek_and_letter_are_none'][0]
        assert e.value.api_message == model_operations[
            'both_greek_and_letter_are_none'][1]
