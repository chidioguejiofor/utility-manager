import pytest
from marshmallow import ValidationError
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from api.schemas import UserMembershipSchema, UserSchema
from api.utils.error_messages import serialization_error
from api.models import User, Organisation, Membership, Role
from api.utils.exceptions import UniqueConstraintException


class TestUserSerializer:
    def test_convert_user_model_to_json(self, init_db):
        valid_user_obj = UserGenerator.generate_model_obj(save=True)
        user_dump_data = UserSchema().dump(valid_user_obj)
        dict_created_at_time = ' '.join(user_dump_data['createdAt'].split('T'))
        assert user_dump_data['firstName'] == valid_user_obj.first_name
        assert user_dump_data['lastName'] == valid_user_obj.last_name
        assert user_dump_data['updatedAt'] == valid_user_obj.updated_at
        assert dict_created_at_time == ' '.join(
            str(valid_user_obj.created_at).split('T'))

    def test_load_data_from_user_to_model(self, app, init_db):
        api_sample_data = UserGenerator.generate_api_input_data()
        user_obj = UserSchema().load(api_sample_data)
        assert isinstance(user_obj, User)
        assert user_obj.first_name == api_sample_data['firstName']
        assert user_obj.last_name == api_sample_data['lastName']
        assert user_obj.password_hash is not None

    def test_load_invalid_email_should_raise_exception(self, app):
        api_sample_data = UserGenerator.generate_api_input_data()
        api_sample_data['email'] = 'Invalid Email'
        with pytest.raises(ValidationError) as e:
            assert UserSchema().load(api_sample_data)
        assert e.value.messages['email'][0] == serialization_error[
            'invalid_email']

    def test_load_first_name_containing_numbers_fails(self, app):
        api_sample_data = UserGenerator.generate_api_input_data()
        api_sample_data.update(firstName='Chizo110',
                               email='info21@test-comp.com')
        with pytest.raises(ValidationError) as e:
            assert UserSchema().load(api_sample_data)
        assert e.value.messages['firstName'][0] == serialization_error[
            'alpha_only']

    def test_load_last_name_containing_numbers_fails(self, app):
        api_sample_data = UserGenerator.generate_api_input_data()
        api_sample_data.update(lastName='Chizo110',
                               email='info21@test-comp.com')
        with pytest.raises(ValidationError) as e:
            assert UserSchema().load(api_sample_data)
        assert e.value.messages['lastName'][0] == serialization_error[
            'alpha_only']

    def test_leading_space_should_be_removed_while_loading_name_field(
            self, app):

        name_with_spaces = '    James    '
        api_sample_data = UserGenerator.generate_api_input_data()
        api_sample_data.update(firstName=name_with_spaces)
        user_obj = UserSchema().load(api_sample_data)
        assert isinstance(user_obj, User)
        assert user_obj.first_name == api_sample_data['firstName'].strip()

    def test_user_membership_serializers_should_be_able_to_get_organisations_of_a_user(
            self, init_db):
        valid_user_obj = UserGenerator.generate_model_obj(save=True)
        OrganisationGenerator.generate_model_obj(valid_user_obj.id, save=True)
        OrganisationGenerator.generate_model_obj(valid_user_obj.id, save=True)

        dumped_data = UserMembershipSchema().dump(valid_user_obj)
        assert len(dumped_data['memberships']) == 2
        assert dumped_data['firstName'] == valid_user_obj.first_name
        assert dumped_data['lastName'] == valid_user_obj.last_name
        assert dumped_data['memberships'][0]['role']['name'] == 'OWNER'


class TestUserModel:
    def test_user_model_handles_password_correctly(
            self,
            init_db,
    ):
        valid_user_one_dict = UserGenerator.generate_model_obj_dict()
        valid_user_obj = User(**valid_user_one_dict)
        valid_user_obj.save()
        assert valid_user_obj.password == valid_user_one_dict['password']
        assert valid_user_obj.password_hash is not None
        assert valid_user_obj.email == valid_user_one_dict['email']

    def test_saving_the_user_model_should_succeed(self, init_db):
        valid_user_one_dict = UserGenerator.generate_model_obj_dict()
        valid_user_obj = User(**valid_user_one_dict)
        valid_user_obj.save()
        assert valid_user_obj.password == valid_user_one_dict['password']
        assert valid_user_obj.password_hash is not None
        assert valid_user_obj.email == valid_user_one_dict['email']

    def test_trying_to_save_a_user_with_existing_email_should_fail(
            self, init_db):
        model_dict = UserGenerator.generate_model_obj_dict()
        valid_user_obj = User(**model_dict)
        valid_user_obj.save()

        user_two = User(**model_dict)
        with pytest.raises(UniqueConstraintException) as e:
            user_two.save()
        assert e.value.message == 'The `email` or `username` already exists'

    def test_user_should_be_able_to_join_an_organisation(
            self,
            init_db,
    ):
        valid_user_obj = UserGenerator.generate_model_obj(save=True)
        org = OrganisationGenerator.generate_model_obj(valid_user_obj.id,
                                                       save=True)
        membership = Membership.query.filter_by(organisation=org,
                                                member=valid_user_obj).first()

        user = User.query.filter(User.id == valid_user_obj.id).first()
        user_org = Membership.query.filter((Membership.user_id == user.id) & (
            Membership.organisation_id == org.id)).first().organisation
        owner = Role.query.filter_by(name='OWNER').first()
        assert user_org.id == org.id
        assert user_org.name == org.name
        assert user_org.website == org.website
        assert user_org.display_name == org.display_name
        assert membership.role == owner
