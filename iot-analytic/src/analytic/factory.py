from __future__ import annotations

import argparse
import importlib
import logging
from pathlib import Path
from typing import *

import apache_beam as beam
import yaml
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions

from analytic import core

logging.getLogger().setLevel(logging.INFO)


class Factory:
    __CLASSPATH = [
        ['profile', 'default', 'application.yaml'],
        ['profile', '{profile}', 'application.yaml']
    ]

    def __init__(self, pipeline_name: str, pipeline_args: List, config: Dict) -> None:
        self.__pipeline_name = pipeline_name
        self.__pipeline_args = pipeline_args
        self.__config = config

    @classmethod
    def get_instance(cls, args: List) -> Factory:
        known_args, pipeline_args = Factory.__parse_args(args)
        config = Factory.__get_profile_configuration(profile=known_args.profile)
        config['pipeline'] = config['pipeline'][known_args.pipeline]
        for k, v in config.get('pipeline_args', {}).items():
            pipeline_args += [f'--{k}', v]
        return Factory(known_args.pipeline, pipeline_args, config)

    def create_pipeline(self) -> core.Pipeline:
        name = self.__pipeline_name
        module = importlib.import_module(f'analytic.pipeline.{name}')
        definition = getattr(module, ''.join(map(str.capitalize, name.split('_') + ['Pipeline'])))

        kwargs = {}
        for _property, config in self.__config['pipeline'].items():
            method = getattr(self, f"_Factory__create_{config['type']}")
            kwargs[_property] = method(_property, config)

        return definition(**kwargs)

    def create_runner(self) -> core.Runner:
        pipeline_options = PipelineOptions(self.__pipeline_args)
        pipeline_options.view_as(SetupOptions).save_main_session = \
            self.__config['pipeline_options'].get('save_main_session', True)
        pipeline = beam.Pipeline(options=pipeline_options)
        return core.Runner(pipeline)

    def __create_source(self, name: str, config: Dict[str, Any]):
        return f'Read [{name}]' >> self.__create_object(config)

    def __create_sink(self, name: str, config: Dict[str, Any]):
        return f'Write [{name}]' >> self.__create_object(config)

    def __create_property(self, name: str, config: Dict[str, Any]) -> Any:
        return config['value']

    @staticmethod
    def __create_object(config: Dict[str, Any]) -> Any:
        class_name = config['class'].split('.')
        module = importlib.import_module('.'.join(class_name[0:-1]))
        cls = getattr(module, class_name[-1])
        return cls(*config.get('args', []), **config.get('kwargs', {}))

    @staticmethod
    def __parse_args(args):
        parser = argparse.ArgumentParser()
        parser.add_argument('--pipeline', type=str, required=True, help='Pipeline name.')
        parser.add_argument('--profile', default='local', help='Use specific profile for activate your configuration.')
        return parser.parse_known_args(args)

    @staticmethod
    def __get_profile_configuration(**kwargs) -> Dict:
        def merge(source, destination):
            for key, value in source.items():
                if isinstance(value, dict):
                    node = destination.setdefault(key, {})
                    merge(value, node)
                else:
                    destination[key] = value
            return destination

        configuration = {}
        for classpath in Factory.__CLASSPATH:
            path = Path(__file__).parents[2].joinpath(*[c.format(**kwargs) for c in classpath])

            try:
                with open(path, 'r', encoding='unicode_escape') as file:
                    yaml_configuration = yaml.load(file, Loader=yaml.CLoader)
                    configuration = merge(yaml_configuration, configuration)
            except FileNotFoundError:
                pass

        return configuration
