import pytest
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from api.utils.error_messages import serialization_error
from api.models import Parameter, ValueTypeEnum, Unit
from api.schemas import ParameterSchema as Schema
from api.utils.exceptions import UniqueConstraintException


class TestParameterSerializer:
    def test_convert_parameter_model_to_json(self, init_db,
                                             bulk_create_unit_objects):
        valid_user_obj = UserGenerator.generate_model_obj(save=True)
        org = OrganisationGenerator.generate_model_obj(valid_user_obj.id,
                                                       save=True)
        voltage_unit = Unit.query.filter_by(letter_symbol='V').first()
        parameter = Parameter(
            name='V1',
            unit_id=voltage_unit.id,
            created_by_id=valid_user_obj.id,
            value_type=ValueTypeEnum.NUMERIC,
            organisation_id=org.id,
        )
        parameter.save()
        parameter_dict = Schema().dump(parameter)
        assert parameter_dict['name'] == 'V1'
        assert parameter_dict['unit']['id'] == voltage_unit.id
        assert parameter_dict['updatedAt'] is None
        assert parameter_dict['valueType'] == ValueTypeEnum.NUMERIC.name
        assert parameter_dict['createdBy']['id'] == valid_user_obj.id

    def test_load_parameter_model_from_dictionary(
            self, init_db, bulk_create_unit_objects,
            saved_org_and_user_generator):
        user, org = saved_org_and_user_generator
        voltage_unit = Unit.query.filter_by(letter_symbol='V').first()
        api_dict = dict(
            name='V1',
            unitId=voltage_unit.id,
            createdById=user.id,
            valueType='NUMERIC',
            organisationId=org.id,
        )
        parameter_model = Schema().load(api_dict)
        assert parameter_model.name == 'V1'
        assert parameter_model.unit_id == voltage_unit.id
        assert parameter_model.created_by_id == user.id
        assert parameter_model.organisation_id == org.id


class TestParameterModel:
    def test_save_valid_parameter_with_no_organisation_nor_user_successfully(
            self, init_db, bulk_create_unit_objects):
        voltage_unit = Unit.query.filter_by(letter_symbol='V').first()
        parameter = Parameter(
            name='V1',
            unit_id=voltage_unit.id,
            value_type=ValueTypeEnum.NUMERIC,
        )
        parameter.save()
        assert parameter.name == 'V1'
        assert parameter.value_type == ValueTypeEnum.NUMERIC
        assert parameter.unit_id == voltage_unit.id
        assert parameter.organisation_id is None
        assert parameter.created_by_id is None

    def test_saving_parameter_should_store_created_by_details(
            self, init_db, bulk_create_unit_objects,
            saved_org_and_user_generator):
        voltage_unit = Unit.query.filter_by(letter_symbol='V').first()
        user, _ = saved_org_and_user_generator
        parameter = Parameter(name='V3',
                              unit_id=voltage_unit.id,
                              value_type=ValueTypeEnum.NUMERIC,
                              created_by_id=user.id)
        parameter.save()
        assert parameter.name == 'V3'
        assert parameter.value_type == ValueTypeEnum.NUMERIC
        assert parameter.unit_id == voltage_unit.id
        assert parameter.organisation_id is None
        assert parameter.created_by_id == user.id

    def test_save_org_id_in_parameter(self, init_db, bulk_create_unit_objects,
                                      saved_org_and_user_generator):
        voltage_unit = Unit.query.filter_by(letter_symbol='V').first()
        user, org = saved_org_and_user_generator
        parameter = Parameter(
            name='V1',
            unit_id=voltage_unit.id,
            value_type=ValueTypeEnum.NUMERIC,
            created_by_id=user.id,
            organisation_id=org.id,
        )
        parameter.save()

        assert parameter.name == 'V1'
        assert parameter.value_type == ValueTypeEnum.NUMERIC
        assert parameter.unit_id == voltage_unit.id
        assert parameter.created_by_id == user.id
        assert parameter.organisation_id == org.id

    def test_save_parameter_info_twice_should_fail(
            self, init_db, bulk_create_unit_objects,
            saved_org_and_user_generator):
        voltage_unit = Unit.query.filter_by(letter_symbol='V').first()
        user, org = saved_org_and_user_generator
        parameter_one = Parameter(
            name='V1',
            unit_id=voltage_unit.id,
            value_type=ValueTypeEnum.NUMERIC,
            created_by_id=user.id,
            organisation_id=org.id,
        )
        parameter_two = Parameter(
            name='V1',
            unit_id=voltage_unit.id,
            value_type=ValueTypeEnum.NUMERIC,
            created_by_id=user.id,
            organisation_id=org.id,
        )

        parameter_one.save()
        with pytest.raises(UniqueConstraintException) as e:
            assert parameter_two.save()

        assert e.value.message == serialization_error['exists_in_org'].format(
            'Parameter')
