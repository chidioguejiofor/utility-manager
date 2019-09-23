from .base import BaseView
from flask import request
from settings import router
from api.schemas import UserSchema
from api.utils.success_messages import CREATED


@router.route('/auth/register')
class Register(BaseView):
    def post(self):
        user_obj = UserSchema().load(request.get_json())
        user_obj.save()
        return UserSchema().dump_success_data(user_obj,
                                              CREATED.format('user')), 201
