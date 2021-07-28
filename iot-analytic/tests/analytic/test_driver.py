from unittest import mock

import pytest

from analytic import driver, factory, core


@mock.patch('logging.critical')
@mock.patch('analytic.driver.Factory')
def test_main(mock_factory_class, mock_logging_critical):
    mock_factory = mock.Mock(spec=factory.Factory)
    mock_factory_class.get_instance.return_value = mock_factory
    mock_pipeline = mock.Mock(spec=core.Pipeline)
    mock_factory.create_pipeline.return_value = mock_pipeline
    mock_runner = mock.MagicMock(spec=core.Runner)
    mock_factory.create_runner.return_value = mock_runner
    mock_runner.__enter__.return_value = mock_runner

    driver.main(['foo', 'bar'])

    mock_factory_class.get_instance.assert_called_once_with(['foo', 'bar'])
    mock_factory.create_pipeline.assert_called_once()
    mock_factory.create_runner.assert_called_once()
    mock_runner.__enter__.assert_called_once()
    mock_runner.__exit__.assert_called_once()
    mock_runner.submit.assert_called_once_with(mock_pipeline)
    mock_logging_critical.assert_not_called()


@mock.patch('logging.critical')
@mock.patch('analytic.driver.Factory')
def test_main(mock_factory_class, mock_logging_critical):
    mock_factory = mock.Mock(spec=factory.Factory)
    mock_factory_class.get_instance.return_value = mock_factory
    mock_pipeline = mock.Mock(spec=core.Pipeline)
    mock_factory.create_pipeline.return_value = mock_pipeline
    mock_runner = mock.MagicMock(spec=core.Runner)
    mock_factory.create_runner.return_value = mock_runner
    mock_runner.__enter__.return_value = mock_runner
    mock_runner.submit.side_effect = RuntimeError('crash')

    with pytest.raises(RuntimeError):
        driver.main(['foo', 'bar'])

    mock_factory_class.get_instance.assert_called_once_with(['foo', 'bar'])
    mock_factory.create_pipeline.assert_called_once()
    mock_factory.create_runner.assert_called_once()
    mock_runner.__enter__.assert_called_once()
    mock_runner.__exit__.assert_called_once()
    mock_runner.submit.assert_called_once_with(mock_pipeline)
    mock_logging_critical.assert_called_once()
