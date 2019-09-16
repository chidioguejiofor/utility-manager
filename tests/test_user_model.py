import pytest
import sqlalchemy
from .mocks.user import valid_user_one_dict
from .mocks.organisation import valid_org_dict
from api.models import User, Organisation, Membership, RoleEnum


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
        org = Organisation(**valid_org_dict)
        org.save()
        valid_user_obj.save()
        membership = Membership(organisation=org, member=valid_user_obj)
        membership.save()

        user = User.query.filter(User.id == valid_user_obj.id).first()
        user_org = user.memberships[0].organisation
        assert user_org.id == org.id
        assert user_org.name == org.name
        assert user_org.website == org.website
        assert user_org.display_name == org.display_name
        assert membership.role == RoleEnum.REGULAR_USERS
