import socket
import unittest
from unittest import mock

import device
from device import GatewayClient


class GatewayClientTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.patcher = mock.patch('socket.socket')
        self.mock_socket = self.patcher.start()
        self.mock_sock = self.mock_socket.return_value
        self.client = GatewayClient('foo')

    def test_init(self):
        self.assertEqual(self.client._device_id, 'foo')
        self.assertEqual(self.client._sock, self.mock_sock)
        self.mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)

    def test_connect(self):
        self.client.connect('192.168.0.1', 8088)

        self.mock_sock.connect.assert_called_once_with(('192.168.0.1', 8088))

    def test_attach(self):
        with mock.patch.object(self.client, '_send', wraps=self.client._send) as mock_send:
            self.client.attach()

            mock_send.assert_has_calls((mock.call('det foo'), mock.call('att foo')))

    def test_detach(self):
        with mock.patch.object(self.client, '_send', wraps=self.client._send) as mock_send:
            self.client.detach()

            mock_send.assert_called_once_with('det foo')

    def test_publish(self):
        with mock.patch.object(self.client, '_send', wraps=self.client._send) as mock_send:
            self.client.publish(1.2345, 6.789)

            mock_send.assert_called_once_with('pub 1.23 6.79')

    def test_send(self):
        self.client._send('msg')

        self.mock_sock.send.assert_called_once_with(b'msg\r\n')

    def tearDown(self) -> None:
        self.patcher.stop()

    @classmethod
    def tearDownClass(cls) -> None:
        mock.patch.stopall()


class DeviceTestCase(unittest.TestCase):

    @mock.patch('device.GatewayClient', autospec=True)
    def test_main(self, mock_gateway_client_cls):
        args = mock.PropertyMock()
        args.device_id = 'foo'
        args.gateway_ip = '192.168.0.1'
        args.gateway_port = 8088
        mock_gateway_client = mock_gateway_client_cls.return_value
        mock_gateway_client.publish.side_effect = [None, None, KeyboardInterrupt()]

        device.main(args)

        mock_gateway_client.connect.assert_called_once_with('192.168.0.1', 8088)
        mock_gateway_client.attach.assert_called_once()
        call_args_list = mock_gateway_client.publish.call_args_list
        self.assertEqual(len(call_args_list), 3)
        for call_args in call_args_list:
            temperature, humidity = call_args[0]
            self.assertTrue(-20 <= temperature <= 50)
            self.assertTrue(0 <= humidity <= 100)
        mock_gateway_client.detach.assert_called_once()

    def test_parse_args(self):
        args = device.parse_args([
            '--device_id', 'foo', '--gateway_ip', '192.168.1.1', '--gateway_port', '80'])

        self.assertEqual(args.device_id, 'foo')
        self.assertEqual(args.gateway_ip, '192.168.1.1')
        self.assertEqual(args.gateway_port, 80)

    def test_parse_args_empty(self):
        with self.assertRaises(SystemExit):
            device.parse_args([])

    def test_parse_args_default(self):
        args = device.parse_args(['--device_id', 'foo'])

        self.assertEqual(args.device_id, 'foo')
        self.assertEqual(args.gateway_ip, '127.0.0.1')
        self.assertEqual(args.gateway_port, 10000)
