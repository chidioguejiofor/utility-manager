import os
from sqlalchemy.sql import expression
import numpy as np
from flask_restplus import Resource
from flask import request
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.token_validator import TokenValidator
from api.utils.error_messages import authentication_errors
from api.utils.constants import LOGIN_TOKEN


class BaseView(Resource):
    def decode_token(self, check_user_is_verified=False):
        """Decoded a token and returns the decoded data

        Args:
            token_type (int, optional): The type of token being decoded
                Defaults to `1`(LOGIN_TOKEN)
            check_user_is_verified (bool): When this is true, this ensures that
                the user is also verified

        Returns:
            dict, str: The decoded token data
        """
        token = request.cookies.get('token')
        if not token:
            raise MessageOnlyResponseException(
                authentication_errors['missing_token'],
                401,
            )
        decoded_data = TokenValidator.decode_token_data(token,
                                                        token_type=LOGIN_TOKEN)
        if check_user_is_verified and not decoded_data['verified']:
            raise MessageOnlyResponseException(
                authentication_errors['unverified_user'],
                403,
            )
        return decoded_data


class CookieGeneratorMixin:
    def generate_cookie_header(self, user_data=None, expired=False):
        """Generates a dict that contains headers with cookie

        When expired is False, it uses the user_data to generate a token
        and puts it in the cookie of the response.

        When expired is True, it invalidates the previously sent token
        Args:
            user_data dict: User data that would be used to generate token
            expired bool: when True, token would be expired

        Returns:

        """
        secure_flag = 'secure' if os.getenv(
            'FLASK_ENV') != 'development' else ''

        token = 'deleted'
        expired_str = 'expires=Thu, 01 Jan 1970 00:00:00 GMT'
        if not expired:
            expired_str = ''
            payload = {
                'type': LOGIN_TOKEN,
                'email': user_data['email'],
                'id': user_data['id'],
                'username': user_data['username'],
                "verified": user_data['verified'],
            }
            token = TokenValidator.create_token(payload)
        return {
            'Set-Cookie':
            f'token={token}; path=/; HttpOnly; {secure_flag}; {expired_str}'
        }


class SearchFilter:
    __model__ = None

    def search_model(self, query_params):
        filter_condition = []
        model_query = self.__model__.query
        for model_column in self.SEARCH_FILTER_ARGS:
            col_search_str = f'{str(model_column)}_search'
            search_value = query_params.get(col_search_str)
            col_filter = None
            if search_value is not None and len(search_value) > 0:
                col_filter = self._retrieve_filter_binary_expression(
                    model_column, search_value)
            if col_filter is not None:
                filter_condition.append(col_filter)

        if filter_condition:
            model_query = model_query.filter(
                np.bitwise_or.reduce(filter_condition))
        return model_query

    def _retrieve_filter_binary_expression(self, model_col, search_value):
        filter_type = self.SEARCH_FILTER_ARGS[model_col]['filter_type']
        model_class_col = getattr(self.__model__, model_col)

        if filter_type == 'ilike':
            return model_class_col.ilike(f'%{search_value}%')
        raise Exception('Invalid search args in model')


class Paginator:
    """
    Contains methods for paginating an output query.
    """
    def _sort_query(self, query, query_params):
        """Sorts the query based on query_params provided

        The logic of the sorting in performed using the
         SORT_KWARGS provided in this object. This object follows this pattern:

         SORT_KWARGS= {
            'defaults': '<comma-seperated-model-column>',
            'sort_fields': <a-set-contiaining the fields>,
        }
        The sort_fields tells the function which fields can be sorted. It should contain a set of
        field that would be sorted.

        The defaults specified the default sorting order_by was not provided for this view
        For example:
           SORT_KWARGS= {
                'defaults': 'name,symbol',
                'sort_fields': {'name', 'symbol'}
            }


        Args:
            query(flask_sqlalchemy.BaseQuery): the query that we want to sort
            query_params: the params sent from the API call

        Returns:
            flask_sqlalchemy.BaseQuery: a sorted query object

        """
        sort_fields = self.SORT_KWARGS['sort_fields']
        default_sort = self.SORT_KWARGS['defaults']
        order_by_list = []
        order_by = query_params.get('sort_by', default_sort)

        for order_by_str in order_by.split(','):
            field_name = order_by_str.strip()
            asc_or_desc = '+'
            if len(field_name) > 0 and not order_by_str[0].isalpha():
                field_name = order_by_str[1:]
                asc_or_desc = order_by_str[0]
            if len(field_name) > 0 and field_name in sort_fields:
                filter_field = getattr(self.__model__, field_name)
                filter_field = filter_field.desc(
                ) if asc_or_desc == '-' else filter_field
                order_by_list.append(expression.nullslast(filter_field))

        return query.order_by(*order_by_list)

    def paginate_query(self, query, query_params):
        """Paginates the query using the query_params provided

        Uses the queries ?page=<page>&page_limit=<limit> to paginate output data.

        Would default to `?page=1&page_limit=10` if invalid values are provided for either
        page or page_limit

        Args:
            query(flask_sqlalchemy.BaseQuery): The query to be filtered
            query_params(dict): Query params passed by the user

        Returns:
            (flask_sqlalchemy.BaseQuery, dict): Returns a tuple containing the query items and metadata
        """
        page_str = query_params.get('page')
        page_limit_str = query_params.get('page_limit')
        page_is_valid = page_str and page_str.isnumeric()
        limit_is_valid = page_limit_str and page_limit_str.isnumeric()
        page = int(page_str) if page_is_valid else 1
        page_limit = int(page_limit_str) if limit_is_valid else 10
        sorted_query = self._sort_query(query, query_params)
        paginated_query = sorted_query.paginate(page, page_limit, False)
        curent_page = (paginated_query.pages +
                       1 if paginated_query.page > paginated_query.pages else
                       paginated_query.page)
        meta = {
            'currentPage': curent_page,
            'nextPage': paginated_query.next_num,
            'previousPage': paginated_query.prev_num,
            'totalObjects': paginated_query.total,
            'totalPages': paginated_query.pages,
            'objectsPerPage': paginated_query.per_page,
        }
        return paginated_query.items, meta


class FilterByQueryMixin(SearchFilter, Paginator):
    pass
