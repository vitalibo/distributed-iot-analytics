import ssl
import unittest
from datetime import datetime
from unittest import mock

from gateway import gcp


class MQTTIoTCoreTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.client = gcp.MQTTIoTCore(
            project_id='new-idea-3040',
            region='europe-west1',
            registry_id='dia-rg',
            gateway_id='dia-rpi4-gw',
            private_key_file='private.pem',
            algorithm='RS256',
            ca_certs='roots.pem',
            mqtt_bridge_hostname='my-mqtt.googleapis.com',
            mqtt_bridge_port=88,
            jwt_expires_in_minutes=10
        )

    def test_constructor(self):
        self.assertEqual(self.client._project_id, 'new-idea-3040')
        self.assertEqual(self.client._region, 'europe-west1')
        self.assertEqual(self.client._registry_id, 'dia-rg')
        self.assertEqual(self.client._gateway_id, 'dia-rpi4-gw')
        self.assertEqual(self.client._client_id,
                         'projects/new-idea-3040/locations/europe-west1/registries/dia-rg/devices/dia-rpi4-gw')
        self.assertEqual(self.client._mqtt_bridge_hostname, 'my-mqtt.googleapis.com')
        self.assertEqual(self.client._mqtt_bridge_port, 88)
        self.assertEqual(self.client._private_key_file, 'private.pem')
        self.assertEqual(self.client._algorithm, 'RS256')
        self.assertEqual(self.client._ca_certs, 'roots.pem')
        self.assertEqual(self.client._jwt_expires_in_minutes, 10)

    @mock.patch('paho.mqtt.client.Client')
    def test_connect(self, mock_mqtt_client_cls):
        mock_create_jwt_token = mock.MagicMock()
        mock_create_jwt_token.return_value = 'jwt_token'
        self.client._create_jwt_token = mock_create_jwt_token
        mock_mqtt_client = mock_mqtt_client_cls.return_value
        mock_on_connect = mock.MagicMock()
        self.client.on_connect = mock_on_connect

        self.client.connect()

        mock_mqtt_client.username_pw_set.assert_called_once_with(username='unused', password='jwt_token')
        mock_mqtt_client.tls_set.assert_called_once_with(ca_certs='roots.pem', tls_version=ssl.PROTOCOL_TLSv1_2)
        mock_mqtt_client.connect.assert_called_once_with('my-mqtt.googleapis.com', 88)
        self.assertEqual(self.client._mqtt_client, mock_mqtt_client)
        self.assertEqual(mock_mqtt_client.on_connect, mock_on_connect)

    def test_delegate_calls(self):
        mock_mqtt_client = mock.MagicMock()
        mock_mqtt_client.foo.return_value = 'bar'
        self.client._mqtt_client = mock_mqtt_client

        actual = self.client.foo()

        self.assertEqual(actual, 'bar')

    @mock.patch('jwt.encode')
    def test_create_jwt_token(self, mock_jwt_encode):
        mock_jwt_encode.return_value = 'jwt_token'
        with mock.patch('gateway.gcp.open', mock.mock_open(read_data='PrivateKey')):
            actual = self.client._create_jwt_token(now_supplier=lambda: datetime.fromtimestamp(1624060800))

            self.assertEqual(actual, 'jwt_token')

        call_args = mock_jwt_encode.call_args
        self.assertEqual(call_args[0][0]['aud'], 'new-idea-3040')
        self.assertEqual(call_args[0][0]['exp'], datetime(2021, 6, 19, 3, 10))
        self.assertEqual(call_args[0][0]['iat'], datetime(2021, 6, 19, 3, 0))
        self.assertEqual(call_args[0][1], 'PrivateKey')
        self.assertEqual(call_args[1]['algorithm'], 'RS256')

    def test_on_connect(self):
        mqtt_client = mock.MagicMock()
        self.client._mqtt_client = mqtt_client
        self.client._gateway_id = 'foo'

        self.client.on_connect(None, None, None, None)

        mqtt_client.subscribe.assert_has_calls((
            mock.call('/devices/foo/config', qos=1),
            mock.call('/devices/foo/errors', qos=0)))

    def test_on_message(self):
        mock_client = mock.MagicMock()
        mock_userdata = mock.MagicMock()
        mock_message = mock.MagicMock()
        mock_message.topic = '/foo/'
        mock_subscription = mock.MagicMock()
        self.client._subscriptions = {'/foo/': mock_subscription}

        self.client.on_message(mock_client, mock_userdata, mock_message)

        mock_subscription.assert_called_with(mock_client, mock_userdata, mock_message)

    @mock.patch('logging.warning')
    def test_on_message_unknown_subscription(self, mock_logging_warning):
        mock_client = mock.MagicMock()
        mock_userdata = mock.MagicMock()
        mock_message = mock.MagicMock()
        mock_message.topic = '/foo/'
        mock_subscription = mock.MagicMock()
        self.client._subscriptions = {'/bar/': mock_subscription}

        self.client.on_message(mock_client, mock_userdata, mock_message)

        mock_subscription.assert_not_called()
        mock_logging_warning.assert_called_once()

    def test_attach(self):
        mock_mqtt_client = mock.MagicMock()
        self.client._mqtt_client = mock_mqtt_client

        self.client.attach('foo', 'jwt')

        mock_mqtt_client.publish.assert_called_once_with('/devices/foo/attach', '{"authorization": "jwt"}', qos=1)

    def test_detach(self):
        mock_mqtt_client = mock.MagicMock()
        self.client._mqtt_client = mock_mqtt_client

        self.client.detach('foo')

        mock_mqtt_client.publish.assert_called_once_with('/devices/foo/detach', '{}', qos=1)

    def test_publish_event(self):
        mock_mqtt_client = mock.MagicMock()
        self.client._mqtt_client = mock_mqtt_client

        self.client.publish_event('foo', 'json', qos=1)

        mock_mqtt_client.publish.assert_called_once_with('/devices/foo/events', 'json', 1)

    def test_subscribe_to_config(self):
        mock_subscribe = mock.MagicMock()
        self.client._subscribe = mock_subscribe
        mock_callback = mock.MagicMock()

        self.client.subscribe_to_config('foo', mock_callback)

        mock_subscribe.assert_called_once_with('/devices/foo/config', mock_callback, qos=1)

    def test_subscribe_to_commands(self):
        mock_subscribe = mock.MagicMock()
        self.client._subscribe = mock_subscribe
        mock_callback = mock.MagicMock()

        self.client.subscribe_to_commands('foo', mock_callback, 'bar/#', 0)

        mock_subscribe.assert_called_once_with('/devices/foo/commands/bar/#', mock_callback, qos=0)

    def test_subscribe(self):
        mock_mqtt_client = mock.MagicMock()
        self.client._mqtt_client = mock_mqtt_client
        mock_callback = mock.MagicMock()

        self.client._subscribe('/foo/bar/baz/', mock_callback, qos=2)

        mock_mqtt_client.subscribe.assert_called_once_with('/foo/bar/baz/', qos=2)
        self.assertEqual(self.client._subscriptions['/foo/bar/baz/'], mock_callback)
