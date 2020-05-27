from sqlalchemy.sql import expression, desc
from sqlalchemy.orm import joinedload
import numpy as np


class BaseFilterMixin:
    FILTER_QUERY_MAPPER = {}

    def join_col(self, query, rel_class):
        if rel_class not in self._joined_fields:  # then do join only once
            query = query.join(rel_class)
            self._joined_fields.append(rel_class)
        return query

    def extract_rel_model_and_col(self, model_column):
        if '.' in model_column:
            rel, rel_name = model_column.split('.')
            model_class_col = getattr(self.__model__, rel)
            rel_class = model_class_col.property.mapper.class_
            return rel, rel_name, model_class_col, rel_class


class SearchFilterMixin(BaseFilterMixin):
    __model__ = None
    EAGER_LOADING_FIELDS = SEARCH_FILTER_ARGS = {}

    def search_model(self, query_params):
        filter_condition = []
        model_query = self.__model__.eager(*self.EAGER_LOADING_FIELDS)
        for model_column in self.SEARCH_FILTER_ARGS:
            col_search_str = f'{str(model_column)}_search'
            search_value = query_params.get(col_search_str)
            col_filter = None
            filter_type = self.SEARCH_FILTER_ARGS[model_column]['filter_type']
            model_column = self.FILTER_QUERY_MAPPER.get(
                model_column, model_column)
            if search_value is not None and len(search_value) > 0:
                col_filter = self._retrieve_filter_binary_expression(
                    model_column, search_value, filter_type)
                rel_args = self.extract_rel_model_and_col(model_column)

                if rel_args:
                    rel_class = rel_args[3]
                    model_query = self.join_col(model_query, rel_class)
            if col_filter is not None:
                filter_condition.append(col_filter)

        if filter_condition:
            model_query = model_query.filter(
                np.bitwise_or.reduce(filter_condition))
        return model_query

    def _retrieve_filter_binary_expression(self, model_col, search_value,
                                           filter_type):
        rel_args = self.extract_rel_model_and_col(model_col)
        if rel_args:
            rel, rel_name, model_class_col, rel_class = rel_args
            model_class_col = getattr(rel_class, rel_name)
        else:
            model_class_col = getattr(self.__model__, model_col)

        if filter_type == 'ilike':
            return model_class_col.ilike(f'%{search_value}%')
        elif filter_type == 'eq':
            return model_class_col == search_value
        raise Exception('Invalid search args in model')


class PaginatorMixin(BaseFilterMixin):
    """
    Contains methods for paginating an output query.
    """
    SORT_KWARGS = None

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
                field_name = self.FILTER_QUERY_MAPPER.get(
                    field_name, field_name)
                rel_args = self.extract_rel_model_and_col(field_name)
                if rel_args:
                    rel, rel_name, model_class_col, rel_class = rel_args
                    filter_field = getattr(rel_class, rel_name)
                    query = self.join_col(query, rel_class)
                else:
                    filter_field = getattr(self.__model__, field_name)
                filter_field = desc(
                    filter_field) if asc_or_desc == '-' else filter_field
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
            'maxObjectsPerPage': paginated_query.per_page,
        }
        return paginated_query.items, meta
