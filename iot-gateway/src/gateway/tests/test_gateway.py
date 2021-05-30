import socket
import unittest
from unittest import mock

from gateway import gcp, gateway


class DeviceProxyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_connection = mock.MagicMock(spec=socket.socket)
        self.mock_mqtt = mock.MagicMock(spec=gcp.MQTTIoTCore)
        self.client = gateway.DeviceProxy(self.mock_connection, ('192.168.1.2', 8088), self.mock_mqtt)
        self.client.recv_cmd = mock.MagicMock()
        self.client.attach = mock.MagicMock()
        self.client.detach = mock.MagicMock()
        self.client.publish = mock.MagicMock()

    @mock.patch('logging.info')
    def test_run(self, mock_logging_info):
        self.client.recv_cmd.side_effect = []
        self.client._device_id = 'foo'

        self.client.run()

        self.client.attach.assert_not_called()
        self.client.detach.assert_called_once_with('foo')
        self.client.publish.assert_not_called()
        self.mock_connection.close.assert_called_once()
        mock_logging_info.assert_has_calls((
            mock.call('connection from 192.168.1.2:8088 open.'),
            mock.call('connection from 192.168.1.2:8088 close.')))

    def test_run_attach(self):
        self.client.recv_cmd.return_value = [('att', 'foo', 'bar')]

        self.client.run()

        self.client.attach.assert_called_once_with('foo', 'bar')
        self.client.detach.assert_not_called()
        self.client.publish.assert_not_called()
        self.mock_connection.close.assert_called_once()

    def test_run_detach(self):
        self.client.recv_cmd.return_value = [('det', 'foo', 'bar')]

        self.client.run()

        self.client.attach.assert_not_called()
        self.client.detach.assert_called_once_with('foo', 'bar')
        self.client.publish.assert_not_called()
        self.mock_connection.close.assert_called_once()

    def test_run_publish(self):
        self.client.recv_cmd.return_value = [('pub', 'foo', 'bar')]

        self.client.run()

        self.client.attach.assert_not_called()
        self.client.detach.assert_not_called()
        self.client.publish.assert_called_once_with('foo', 'bar')
        self.mock_connection.close.assert_called_once()

    @mock.patch('logging.warning')
    def test_run_unknown(self, mock_logging_warning):
        self.client.recv_cmd.return_value = [('foo', 'bar', 'baz')]

        self.client.run()

        self.client.attach.assert_not_called()
        self.client.detach.assert_not_called()
        self.client.publish.assert_not_called()
        self.mock_connection.close.assert_called_once()
        mock_logging_warning.assert_called_once_with("unknown command: foo ['bar', 'baz'].")

    @mock.patch('logging.warning')
    def test_run_with_exception(self, mock_logging_warning):
        exception = OSError('foo')
        self.client.recv_cmd.side_effect = exception

        self.client.run()

        self.client.attach.assert_not_called()
        self.client.detach.assert_not_called()
        self.client.publish.assert_not_called()
        self.mock_connection.close.assert_called_once()
        mock_logging_warning.assert_called_once_with(exception)

    def test_attach(self):
        client = gateway.DeviceProxy(self.mock_connection, ('192.168.1.2', 8088), self.mock_mqtt)
        client._device_id = None

        client.attach('foo')

        self.mock_mqtt.attach.assert_called_once_with('foo')
        self.assertEqual(client._device_id, 'foo')
        self.assertEqual(client._DeviceProxy__devices, {'foo': self.mock_connection})

    def test_detach(self):
        client = gateway.DeviceProxy(self.mock_connection, ('192.168.1.2', 8088), self.mock_mqtt)
        client._device_id = 'bar'

        client.detach('bar')

        self.mock_mqtt.detach.assert_called_once_with('bar')
        self.assertIsNone(client._device_id)
        self.assertFalse('bar' in client._DeviceProxy__devices)

    def test_publish(self):
        mock_now = mock.MagicMock()
        mock_now.return_value.timestamp.return_value = 1122334455
        client = gateway.DeviceProxy(self.mock_connection, ('192.168.1.2', 8088), self.mock_mqtt, mock_now)
        client._device_id = 'baz'

        client.publish('1.23', '4.56')

        self.mock_mqtt.publish_event.assert_called_once_with(
            'baz', '{"ip": "192.168.1.2", "timestamp": 1122334455, "temperature": 1.23, "humidity": 4.56}')

    def test_recv_cmd(self):
        self.mock_connection.recv.side_effect = [i.encode() for i in 'att foo\r\npub bar baz\n']
        client = gateway.DeviceProxy(self.mock_connection, ('192.168.1.2', 8088), self.mock_mqtt)

        actual = client.recv_cmd()

        self.assertEqual(next(actual), ['att', 'foo'])
        self.assertEqual(next(actual), ['pub', 'bar', 'baz'])


class GatewayTestCase(unittest.TestCase):

    @mock.patch('gateway.gateway.DeviceProxy')
    @mock.patch('gateway.gcp.MQTTIoTCore')
    @mock.patch('socket.socket')
    def test_main(self, mock_socket, mock_mqtt_iot_core, mock_device_proxy):
        mock_connection = mock.MagicMock()
        mock_sock = mock_socket.return_value
        mock_sock.accept.side_effect = [(mock_connection, ('192.168.0.1', 41192)), Exception('bar')]
        mock_mqtt = mock_mqtt_iot_core.return_value
        mock_thread = mock_device_proxy.return_value
        mock_args = mock.MagicMock()
        mock_args.server_ip = '192.168.0.1'
        mock_args.server_port = 41192
        mock_args.gateway_id = 'foo'

        with self.assertRaises(Exception):
            gateway.main(mock_args)

        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_sock.bind.assert_called_once_with(('192.168.0.1', 41192))
        mock_sock.listen.assert_called_once_with(10)
        mock_mqtt_iot_core.assert_called_once()
        mock_mqtt.connect.assert_called_once()
        mock_device_proxy.assert_called_once_with(mock_connection, ('192.168.0.1', 41192), mock_mqtt)
        mock_thread.start.assert_called_once()
        mock_sock.shutdown.assert_called_once_with(socket.SHUT_RDWR)
        mock_sock.close.assert_called_once()

    def test_parse_args(self):
        args = gateway.parse_args([
            '--server_ip', '192.169.128.1', '--server_port', '9099', '--project_id', 'new-idea-3040',
            '--region', 'europe-west1', '--registry_id', 'dia-rg', '--gateway_id', 'dia-rpi4-gw',
            '--private_key_file', 'private.pem', '--algorithm', 'RS256', '--ca_certs', 'roots.pem',
            '--mqtt_bridge_hostname', 'my-mqtt.googleapis.com', '--mqtt_bridge_port', '88',
            '--jwt_expires_in_minutes', '10'])

        self.assertEqual(args.server_ip, '192.169.128.1')
        self.assertEqual(args.server_port, 9099)
        self.assertEqual(args.project_id, 'new-idea-3040')
        self.assertEqual(args.region, 'europe-west1')
        self.assertEqual(args.registry_id, 'dia-rg')
        self.assertEqual(args.private_key_file, 'private.pem')
        self.assertEqual(args.algorithm, 'RS256')
        self.assertEqual(args.ca_certs, 'roots.pem')
        self.assertEqual(args.mqtt_bridge_hostname, 'my-mqtt.googleapis.com')
        self.assertEqual(args.mqtt_bridge_port, 88)
        self.assertEqual(args.jwt_expires_in_minutes, 10)

    def test_parse_args_empty(self):
        with self.assertRaises(SystemExit):
            gateway.parse_args([])
