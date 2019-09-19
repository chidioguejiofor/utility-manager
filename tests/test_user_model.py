import pytest
import sqlalchemy
from marshmallow import ValidationError
from .mocks.user import valid_user_one_dict, user_input_dict
from .mocks.organisation import valid_org_dict, valid_org_two_dict

from api.schemas import UserMembershipSchema, UserSchema
from api.utils.error_messages import serialization_error
from api.models import User, Organisation, Membership, RoleEnum


class TestUserSerializer:
    def test_convert_user_model_to_json(self, init_db, valid_user_obj):
        valid_user_obj.save()
        user_dump_data = UserSchema().dump(valid_user_obj)
        dict_created_at_time = ' '.join(user_dump_data['createdAt'].split('T'))
        assert user_dump_data['firstName'] == valid_user_obj.first_name
        assert user_dump_data['lastName'] == valid_user_obj.last_name
        assert user_dump_data['updatedAt'] == valid_user_obj.updated_at
        assert dict_created_at_time == ' '.join(
            str(valid_user_obj.created_at).split('T'))

    def test_load_data_from_user_to_model(self, app, init_db):
        user_obj = UserSchema().load(user_input_dict)
        assert isinstance(user_obj, User)
        assert user_obj.first_name == user_input_dict['firstName']
        assert user_obj.last_name == user_input_dict['lastName']
        assert user_obj.password_hash is not None

    def test_load_invalid_email_should_raise_exception(self, app):
        valid_user_input = dict(**user_input_dict)
        valid_user_input['email'] = 'Invalid Email'
        with pytest.raises(ValidationError) as e:
            assert UserSchema().load(valid_user_input)
        assert e.value.messages['email'][0] == serialization_error[
            'invalid_email']

    def test_load_first_name_containing_numbers_fails(self, app):
        invalid_dict = dict(**user_input_dict)
        invalid_dict.update(firstName='Chizo110', email='info21@test-comp.com')

        with pytest.raises(ValidationError) as e:
            assert UserSchema().load(invalid_dict)
        assert e.value.messages['firstName'][0] == serialization_error[
            'alpha_only']

    def test_load_last_name_containing_numbers_fails(self, app):
        invalid_dict = dict(**user_input_dict)
        invalid_dict.update(lastName='Chizo110', email='info21@test-comp.com')
        with pytest.raises(ValidationError) as e:
            assert UserSchema().load(invalid_dict)
        assert e.value.messages['lastName'][0] == serialization_error[
            'alpha_only']

    def test_leading_space_should_be_removed_while_loading_name_field(
            self, app):

        name_with_spaces = '    James    '
        data_with_name_with_spaces = dict(**user_input_dict)
        data_with_name_with_spaces.update(firstName=name_with_spaces)
        user_obj = UserSchema().load(data_with_name_with_spaces)
        assert isinstance(user_obj, User)
        assert user_obj.first_name == data_with_name_with_spaces[
            'firstName'].strip()

    def test_user_membership_serializers_should_be_able_to_get_organisations_of_a_user(
            self, init_db, valid_user_obj):
        org_one = Organisation(**valid_org_dict)
        org_one.save()
        org_two = Organisation(**valid_org_two_dict)
        org_two.save()

        valid_user_obj.save()
        Membership(organisation=org_one, member=valid_user_obj).save()
        Membership(organisation=org_two, member=valid_user_obj).save()

        dumped_data = UserMembershipSchema().dump(valid_user_obj)
        assert len(dumped_data['memberships']) == 2
        assert dumped_data['firstName'] == valid_user_obj.first_name
        assert dumped_data['lastName'] == valid_user_obj.last_name
        assert dumped_data['memberships'][0]['role'] == 'REGULAR_USER'


class TestUserModel:
    def test_user_model_handles_password_correctly(self, init_db,
                                                   valid_user_obj):
        assert valid_user_obj.password == valid_user_one_dict['password']
        assert valid_user_obj.password_hash is not None
        assert valid_user_obj.email == valid_user_one_dict['email']

    def test_saving_the_user_model_should_succeed(self, init_db,
                                                  valid_user_obj):
        valid_user_obj.save()
        assert valid_user_obj.password == valid_user_one_dict['password']
        assert valid_user_obj.password_hash is not None
        assert valid_user_obj.email == valid_user_one_dict['email']

    def test_trying_to_save_a_user_with_existing_email_should_fail(
            self, init_db, valid_user_obj):
        valid_user_obj.save()

        user_two = User(**valid_user_one_dict)
        with pytest.raises(sqlalchemy.exc.IntegrityError) as e:
            user_two.save()

    def test_user_should_be_able_to_join_an_organisation(
            self, init_db, valid_user_obj):
        org_dict = dict(**valid_org_dict)
        org_dict.update(name='Valid_Org 2', email='valid_orgII@email.com')
        org = Organisation(**org_dict)
        org.save()
        valid_user_obj.save()
        membership = Membership(organisation=org, member=valid_user_obj)
        membership.save()

        user = User.query.filter(User.id == valid_user_obj.id).first()
        user_org = Membership.query.filter((Membership.user_id == user.id) & (
            Membership.organisation_id == org.id)).first().organisation
        assert user_org.id == org.id
        assert user_org.name == org.name
        assert user_org.website == org.website
        assert user_org.display_name == org.display_name
        assert membership.role == RoleEnum.REGULAR_USER
