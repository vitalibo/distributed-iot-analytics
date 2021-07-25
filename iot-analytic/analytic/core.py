from __future__ import annotations

from abc import abstractmethod, ABC
from types import TracebackType
from typing import *

import apache_beam as beam


class Pipeline(ABC):

    @abstractmethod
    def define(self, pipeline: beam.Pipeline) -> None:
        pass


class Runner:

    def __init__(self, pipeline: beam.Pipeline) -> None:
        self.__pipeline = pipeline

    def submit(self, definition: Pipeline) -> None:
        definition.define(self.__pipeline)

    def __enter__(self) -> Runner:
        self.__pipeline.__enter__()
        return self

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType]
    ):
        try:
            if not exc_type:
                pass
        finally:
            return self.__pipeline.__exit__(exc_type, exc_val, exc_tb)

    @property
    def pipeline(self):
        return self.__pipeline


__all__ = (
    Pipeline,
    Runner
)
