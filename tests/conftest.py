# -*- coding: utf-8 -*-


import os

import pytest
import yaml


@pytest.fixture
def petstore_dict():
    spec_path = os.path.join(os.path.dirname(__file__), 'petstore.yaml')
    with open(spec_path) as f:
        return yaml.safe_load(f)
