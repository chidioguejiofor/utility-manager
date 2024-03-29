import yaml
import numpy as np
import os
from abc import ABC

import dateutil.parser
from datetime import datetime, timezone
from api.utils.id_generator import IDGenerator


class BaseSeeder(ABC):
    __model__ = KEY = None

    def __init__(self, *args, **kwargs):
        self.id = kwargs.get('id') if id else IDGenerator.generate_id()
        created_at = kwargs.get('created_at')
        updated_at = kwargs.get('updated_at')

        self.created_at = created_at if created_at else datetime.now(
            timezone.utc)
        if updated_at is not None:
            updated_at = dateutil.parser.parse(updated_at)
        self.updated_at = updated_at

    @classmethod
    def _convert_to_dicts(cls, list_of_objs):
        return [obj.to_dict() for obj in list_of_objs]

    def model_filter(self):
        raise Exception(f'Implement model_filter in {self.__class__.__name__}')

    def __eq__(self, other):
        raise Exception(f'Implement __eq__ in {self.__class__.__name__}')

    def __lt__(self, other):
        return False

    @classmethod
    def read_data_from_file_to_model(cls):
        with open(f'seeders/fixtures/{cls.KEY}.yaml', 'r') as file:
            list_of_data = yaml.full_load(file)
        if list_of_data:
            return [cls.__model__(**data) for data in list_of_data]
        else:
            return []

    @classmethod
    def _initialise_from_dict_or_query(cls, obj):
        if isinstance(obj, dict):
            return cls(**obj)

        query_to_dict = {}
        for column in obj.__table__.columns:
            query_to_dict[column.name] = getattr(obj, column.name)

        return cls(**query_to_dict)

    @classmethod
    def generate_data(cls, list_of_dicts):
        filename = f'seeders/fixtures/{cls.KEY}.yaml'

        imputed_objects = np.array([
            cls._initialise_from_dict_or_query(data) for data in list_of_dicts
        ])
        existing_data = np.array([])
        if not os.path.isfile(filename):
            with open(filename, 'w'):
                new_data = imputed_objects

        else:
            existing_data = cls.read_data_from_yaml_file(existing_data)
            new_inputs = [
                item for item in filter(lambda obj: obj not in existing_data,
                                        imputed_objects)
            ]
            new_data = existing_data.tolist() + new_inputs

        return cls._convert_to_dicts(
            new_data), len(new_data) > len(existing_data)

    @classmethod
    def read_data_from_yaml_file(cls, existing_data=None):
        existing_data = existing_data if existing_data else np.array([])
        with open(f'seeders/fixtures/{cls.KEY}.yaml', 'r') as file:
            list_of_data = yaml.full_load(file)
        if list_of_data:
            existing_data = np.array([cls(**data) for data in list_of_data])
        return existing_data

    def to_dict(self):
        raise Exception(f'Implement to_dict {self.__class__.__name__}')

    def to_model(self):
        return self.__model__(**self.to_dict())
