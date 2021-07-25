#!/usr/bin/env python3

import logging
import sys
import typing

from analytic.factory import Factory


def main(args: typing.List[str]) -> None:
    factory = Factory.get_instance(args)

    try:
        pipeline = factory.create_pipeline()

        with factory.create_runner() as runner:
            runner.submit(pipeline)

    except Exception as e:
        logging.critical('Pipeline failed execution.', stack_info=True)
        raise e


if __name__ == '__main__':
    main(sys.argv[1:])
