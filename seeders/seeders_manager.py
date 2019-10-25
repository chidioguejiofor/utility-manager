import numpy as np
from .model_seeders import UnitSeed
import yaml


class SeederManager:
    MAPPER = {
        'unit': UnitSeed,
    }

    @classmethod
    def write_seed_data(cls, key, list_of_dicts):
        manager_class = cls.MAPPER[key]
        data_to_write, input_has_new_value = manager_class.generate_data(
            list_of_dicts)
        if input_has_new_value:
            with open(f'seeders/fixtures/{key}.yaml', 'w') as file:
                yaml.dump(data_to_write, file)

    @classmethod
    def seed_database(cls, key):
        data_from_seed_file = cls.MAPPER[key].read_data_from_yaml_file()
        seed_filter = None
        for seed_obj in data_from_seed_file:
            filter_ = seed_obj.model_filter()
            if seed_filter is None:
                seed_filter = filter_
            else:
                seed_filter = seed_filter | filter_

        model_objs = cls.MAPPER[key].__model__.query.filter(seed_filter)
        model_objs = np.array(model_objs.all())
        seed_data_not_in_db = [
            item.to_model() for item in filter(
                lambda obj: obj not in model_objs, data_from_seed_file)
        ]

        cls.MAPPER[key].__model__.bulk_create(seed_data_not_in_db)
