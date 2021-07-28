from importlib.machinery import SourceFileLoader
from unittest import mock

import apache_beam as beam

from analytic import factory, core


def test_get_instance():
    default_config = """
pipeline_options:
  save_main_session: False
pipeline:
  foo_job:
    foo: '%s - %'
    bar:
      - 1
      - 2
"""

    profile_config = """
pipeline_options:
  save_main_session: True
pipeline_args:
  runner: DataflowRunner
  region: 'us-central1'
pipeline:
  foo_job:
    foo: '%s: %'
    baz: taz
"""

    expected_config = {
        'pipeline_options': {
            'save_main_session': True
        },
        'pipeline_args': {
            'runner': 'DataflowRunner',
            'region': 'us-central1'
        },
        'pipeline': {
            'foo': '%s: %',
            'bar': [1, 2],
            'baz': 'taz'
        }
    }

    mock_open = mock.mock_open()
    mock_open.side_effect = [mock.mock_open(read_data=f).return_value for f in (default_config, profile_config)]
    with mock.patch('builtins.open', mock_open):
        actual = factory.Factory.get_instance(['--pipeline', 'foo_job', '--profile', 'dev', '--project', 'inferno'])

        assert isinstance(actual, factory.Factory)
        assert actual._Factory__config == expected_config
        assert actual._Factory__pipeline_name == 'foo_job'
        assert actual._Factory__pipeline_args == ['--project', 'inferno', '--runner', 'DataflowRunner', '--region',
                                                  'us-central1']


@mock.patch('importlib.import_module')
def test_create_pipeline(mock_import_module):
    instance = factory.Factory('test', [], {
        'pipeline': {
            'foo': {
                'type': 'source',
                'class': 'analytic.test_factory.TestSource',
                'kwargs': {
                    'baz': 'taz'
                }
            },
            'baz': {
                'type': 'property',
                'value': 1.234
            }
        }
    })
    factory._Factory__create_source = mock.Mock()
    factory._Factory__create_source.return_value = 'foo-source'
    mock_import_module.return_value = SourceFileLoader("test_factory", __file__).load_module()

    actual = instance.create_pipeline()

    assert isinstance(actual, TestPipeline)
    assert isinstance(actual.foo.transform, TestSource)
    assert actual.foo.label == 'Read [foo]'
    assert actual.foo.transform.baz == 'taz'
    assert actual.baz == 1.234


def test_create_runner():
    instance = factory.Factory('test', ['--runner', 'SparkRunner'], {
        'pipeline_options': {
            'save_main_session': False
        }
    })

    actual = instance.create_runner()

    assert isinstance(actual, core.Runner)
    assert isinstance(actual.pipeline, beam.Pipeline)


class TestPipeline(core.Pipeline):
    def __init__(self, foo, baz):
        self.foo = foo
        self.baz = baz

    def define(self, pipeline: beam.Pipeline) -> None:
        pass


class TestSource(beam.PTransform):
    def __init__(self, baz):
        super().__init__()
        self.baz = baz

    def expand(self, input_or_inputs):
        pass
