import pytest
import sqlalchemy
from api.utils.error_messages import serialization_error
from api.models import Organisation, Membership, RoleEnum
from api.schemas import OrganisationSchema as Schema
from tests.mocks.organisation import user_input_dict, valid_org_dict


class TestOrganisationSerializer:
    def test_convert_org_model_to_json(self, init_db, valid_organisation):
        valid_organisation.save()
        org_dict = Schema().dump(valid_organisation)
        dict_created_at_time = ' '.join(org_dict['createdAt'].split('T'))
        assert org_dict['name'] == valid_organisation.name
        assert org_dict['displayName'] == valid_organisation.display_name
        assert org_dict['updatedAt'] == valid_organisation.updated_at
        assert dict_created_at_time == ' '.join(
            str(valid_organisation.created_at).split('T'))
        assert org_dict[
            'subscriptionType'] == valid_organisation.subscription_type.value

    def test_load_user_input_to_model(self, app, init_db):
        org_obj = Schema().load(user_input_dict)
        assert isinstance(org_obj, Organisation)
        assert org_obj.display_name == user_input_dict['displayName']
        assert org_obj.name == user_input_dict['name']
        assert org_obj.website == user_input_dict['website']

    def test_load_invalid_email_should_raise_exception(self, app):
        valid_user_input = dict(**user_input_dict)
        valid_user_input['email'] = 'Invalid Email'
        with pytest.raises(Exception) as e:
            assert Schema().load(valid_user_input)
        assert e.value.messages['email'][0] == 'Not a valid email address.'

    def test_load_name_containing_symbols_fails(self, app):
        invalid_dict = dict(**user_input_dict)
        invalid_dict.update(name='Comp#$%^&**&^%$',
                            email='info21@test-comp.com')

        with pytest.raises(Exception) as e:
            assert Schema().load(invalid_dict)
        assert e.value.messages['name'][0] == serialization_error[
            'alpha_numeric']

    def test_leading_space_should_be_removed_while_loading_name_field(
            self, app):

        name_with_spaces = '    James    '
        data_with_name_with_spaces = dict(**user_input_dict)
        data_with_name_with_spaces.update(name=name_with_spaces)
        org_obj = Schema().load(data_with_name_with_spaces)
        assert isinstance(org_obj, Organisation)
        assert org_obj.name == data_with_name_with_spaces['name'].strip()


class TestOrganisationModel:
    def test_save_valid_model_succeeds(self, init_db, valid_organisation):
        valid_organisation.save()
        org_query = Organisation.query.filter(
            Organisation.id == valid_organisation.id)
        org = org_query.first()
        assert org.name == valid_organisation.name
        assert org.id == valid_organisation.id
        assert org.website == valid_organisation.website

    def test_attempt_to_save_organisation_with_existing_email_fails(
            self, init_db):
        valid_dict = dict(**valid_org_dict)
        valid_dict.update(name='Test Comp3', email='info13@test-comp.com')
        valid_org = Organisation(**valid_dict)
        valid_org.save()

        # This creates  the organisation as above but with a different  name and same email
        valid_dict.update(name='Test Comp')
        org_2 = Organisation(**valid_dict)
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            assert org_2.save()

    def test_attempt_to_save_organisation_with_existing_name_fails(
            self, init_db):
        valid_dict = dict(**valid_org_dict)
        valid_dict.update(name='Test Comp22', email='info111@test-comp.com')
        valid_org = Organisation(**valid_dict)
        valid_org.save()

        # This creates  the organisation as above but with a different  email and same name
        valid_dict.update(email='info2@test-comp.com')
        org_2 = Organisation(**valid_dict)
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            assert org_2.save()

    def test_load_memberships_for_organisation_succeeds(
            self, init_db, valid_user_obj):
        org = Organisation(**valid_org_dict)
        org.name = 'Mock Name'
        org.email = 'email2@email.com'
        org.save()
        valid_user_obj.save()
        membership = Membership(organisation=org, member=valid_user_obj)
        membership.save()

        org = Organisation.query.filter(Organisation.id == org.id).first()
        member = org.memberships[0].member
        assert member.id == valid_user_obj.id
        assert member.first_name == valid_user_obj.first_name
        assert member.last_name == valid_user_obj.last_name
        assert member.password_hash == valid_user_obj.password_hash
        assert membership.role == RoleEnum.REGULAR_USERS
