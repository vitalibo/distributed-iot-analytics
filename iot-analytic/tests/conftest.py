import json
import os

import apache_beam as beam
import pytest
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import *

from analytic.core import Pipeline


class Helpers:
    @staticmethod
    def assert_pipeline(pipeline_definition: Pipeline):
        with TestPipeline() as pipeline:
            pipeline_definition.define(pipeline)

    @staticmethod
    def absolute_path(root, path):
        return os.path.join(os.path.dirname(root), path)

    @staticmethod
    def resource_as_str(root, path):
        with open(Helpers.absolute_path(root, path), 'r') as f:
            return f.read()

    @staticmethod
    def resource_as_json(root, path):
        return json.loads(Helpers.resource_as_str(root, path))

    @staticmethod
    def resource_as_pcollection(root, path):
        return beam.Create(Helpers.resource_as_json(root, path))

    @staticmethod
    def resource_as_assert_pcollection(root, path):
        class EqualTo(beam.PTransform):
            def expand(self, output):
                assert_that(output, equal_to(Helpers.resource_as_json(root, path)))

        return EqualTo()


@pytest.fixture
def helpers():
    return Helpers
