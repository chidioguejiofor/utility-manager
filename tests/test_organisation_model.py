import pytest
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from api.utils.error_messages import serialization_error
from api.models import Organisation, Membership, RoleEnum
from api.schemas import OrganisationSchema as Schema, OrganisationMembershipSchema
from marshmallow import ValidationError
from api.utils.exceptions import UniqueConstraintException


class TestOrganisationSerializer:
    def test_convert_org_model_to_json(self, init_db):
        org = OrganisationGenerator.generate_model_obj(save=True)
        org_dict = Schema().dump(org)
        dict_created_at_time = ' '.join(org_dict['createdAt'].split('T'))
        assert org_dict['name'] == org.name
        assert org_dict['displayName'] == org.display_name
        assert org_dict['updatedAt'] == org.updated_at
        assert dict_created_at_time == ' '.join(str(org.created_at).split('T'))
        assert org_dict['subscriptionType'] == org.subscription_type.value

    def test_load_user_input_to_model(self, init_db):
        api_dict = OrganisationGenerator.generate_api_input_data()
        org_obj = Schema().load(api_dict)
        assert isinstance(org_obj, Organisation)
        assert org_obj.display_name == api_dict['displayName']
        assert org_obj.name == api_dict['name']
        assert org_obj.website == api_dict['website']

    def test_load_invalid_email_should_raise_exception(self, app):
        api_dict = OrganisationGenerator.generate_api_input_data()
        api_dict['email'] = 'Invalid Email'
        with pytest.raises(ValidationError) as e:
            assert Schema().load(api_dict)
        assert e.value.messages['email'][0] == 'Not a valid email address.'

    def test_load_name_containing_symbols_fails(self, app):
        api_dict = OrganisationGenerator.generate_api_input_data()
        api_dict.update(name='Comp#$%^&**&^%$', email='info21@test-comp.com')

        with pytest.raises(ValidationError) as e:
            assert Schema().load(api_dict)
        assert e.value.messages['name'][0] == serialization_error[
            'alpha_numeric']

    def test_leading_space_should_be_removed_while_loading_name_field(
            self, app):
        api_dict = OrganisationGenerator.generate_api_input_data()
        name_with_spaces = '    James    '
        api_dict.update(name=name_with_spaces)
        org_obj = Schema().load(api_dict)
        assert isinstance(org_obj, Organisation)
        assert org_obj.name == api_dict['name'].strip()

    def test_organisation_membership_is_properly_serialized(self, init_db):
        valid_org = OrganisationGenerator.generate_model_obj(save=True)
        valid_user_obj = UserGenerator.generate_model_obj(save=True)
        membership = Membership(organisation=valid_org, member=valid_user_obj)
        membership.save()

        valid_org = Organisation.query.filter(
            Organisation.id == valid_org.id).first()
        dumped_data = OrganisationMembershipSchema().dump(valid_org)

        assert len(dumped_data['memberships']) == 1
        assert dumped_data['name'] == valid_org.name
        assert dumped_data['website'] == valid_org.website
        assert dumped_data['memberships'][0]['role'] == 'REGULAR_USER'
        assert dumped_data['memberships'][0]['id'] == membership.id


class TestOrganisationModel:
    def test_save_valid_model_succeeds(self, init_db):
        valid_organisation = OrganisationGenerator.generate_model_obj(
            save=True)
        org_query = Organisation.query.filter(
            Organisation.id == valid_organisation.id)
        org = org_query.first()
        assert org.name == valid_organisation.name
        assert org.id == valid_organisation.id
        assert org.website == valid_organisation.website

    def test_attempt_to_save_organisation_with_existing_email_fails(
            self, init_db):
        valid_dict = OrganisationGenerator.generate_model_obj_dict()
        Organisation(**valid_dict).save()
        # This creates  the organisation as above but with a different  name and same email
        valid_dict.update(name='Test Comp')
        with pytest.raises(UniqueConstraintException) as e:
            assert Organisation(**valid_dict).save()
        assert e.value.message == 'The name or email already exists'

    def test_attempt_to_save_organisation_with_existing_name_fails(
            self, init_db):
        valid_dict = OrganisationGenerator.generate_model_obj_dict()
        Organisation(**valid_dict).save()
        # This creates  the organisation as above but with a different  name and same email
        valid_dict.update(email='TestComp@email.com')
        with pytest.raises(UniqueConstraintException) as e:
            assert Organisation(**valid_dict).save()
        assert e.value.message == 'The name or email already exists'

    def test_load_memberships_for_organisation_succeeds(self, init_db):
        org = OrganisationGenerator.generate_model_obj(save=True)
        valid_user_obj = UserGenerator.generate_model_obj(save=True)
        membership = Membership(organisation=org, member=valid_user_obj)
        membership.save()

        org = Organisation.query.filter(Organisation.id == org.id).first()
        member = org.memberships[0].member
        assert member.id == valid_user_obj.id
        assert member.first_name == valid_user_obj.first_name
        assert member.last_name == valid_user_obj.last_name
        assert member.password_hash == valid_user_obj.password_hash
        assert membership.role == RoleEnum.REGULAR_USER
