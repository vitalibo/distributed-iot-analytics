from unittest import mock

from analytic import core
import apache_beam as beam


def test_runner_submit():
    mock_pipeline_definition = mock.Mock(spec=core.Pipeline)
    mock_pipeline = mock.Mock(spec=beam.Pipeline)
    runner = core.Runner(mock_pipeline)

    runner.submit(mock_pipeline_definition)

    mock_pipeline_definition.define.assert_called_once_with(mock_pipeline)


def test_runner_context_manager():
    mock_pipeline = mock.MagicMock(spec=beam.Pipeline)
    runner = core.Runner(mock_pipeline)

    with runner as r:
        assert runner == r
        mock_pipeline.__enter__.assert_called_once()
        mock_pipeline.__exit__.assert_not_called()
    mock_pipeline.__exit__.assert_called_once()
