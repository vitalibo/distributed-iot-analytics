import datetime
import logging
import ssl
import typing

import jwt
import paho.mqtt.client as mqtt


class MQTTIoTCore:

    def __init__(
            self,
            project_id: str,
            region: str,
            registry_id: str,
            gateway_id: str,
            private_key_file: str,
            algorithm: str,
            ca_certs: str,
            mqtt_bridge_hostname: str = 'mqtt.googleapis.com',
            mqtt_bridge_port: int = 8883,
            jwt_expires_in_minutes: int = 15,
            **kwargs
    ) -> None:
        self._project_id = project_id
        self._region = region
        self._registry_id = registry_id
        self._gateway_id = gateway_id
        self._client_id = f'projects/{project_id}/locations/{region}/registries/{registry_id}/devices/{gateway_id}'
        self._mqtt_bridge_hostname = mqtt_bridge_hostname
        self._mqtt_bridge_port = mqtt_bridge_port
        self._private_key_file = private_key_file
        if algorithm not in ('RS256', 'ES256'):
            raise ValueError('unsupported encryption algorithm')
        self._algorithm = algorithm
        self._ca_certs = ca_certs
        self._jwt_expires_in_minutes = jwt_expires_in_minutes
        self._mqtt_client = None
        self._subscriptions = {}

    def connect(self) -> None:
        client = mqtt.Client(self._client_id)
        for attr in dir(self):
            if attr.startswith('on_'):
                setattr(client, attr, getattr(self, attr))

        client.username_pw_set(username='unused', password=self._create_jwt_token())
        client.tls_set(ca_certs=self._ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)
        client.connect(self._mqtt_bridge_hostname, self._mqtt_bridge_port)
        self._mqtt_client = client

    def __getattr__(self, name: str) -> typing.Any:
        attr = getattr(self._mqtt_client, name)
        if attr:
            return attr

        raise AttributeError(f'module {__name__} has no attribute {name}')

    def _create_jwt_token(self, now_supplier: typing.Callable = datetime.datetime.utcnow) -> str:
        now = now_supplier()
        payload = {
            'iat': now,
            'exp': now + datetime.timedelta(minutes=self._jwt_expires_in_minutes),
            'aud': self._project_id
        }

        with open(self._private_key_file, 'r') as f:
            private_key = f.read()

        return jwt.encode(payload, private_key, algorithm=self._algorithm)

    def on_connect(self, client, userdata, flags, rc, properties=None) -> None:
        logging.debug('on_connect %s', mqtt.connack_string(rc))

        self._mqtt_client.subscribe(f'/devices/{self._gateway_id}/config', qos=1)
        self._mqtt_client.subscribe(f'/devices/{self._gateway_id}/errors', qos=0)

    def on_message(self, client, userdata, message) -> None:
        callback = self._subscriptions.get(message.topic)
        if callback:
            callback(client, userdata, message)
        else:
            payload = message.payload.decode('utf8')
            logging.warning("received message '%s' on topic '%s' with Qos '%s'",
                            payload, message.topic, message.qos)

    def attach(self, device_id: str, jwt_token: str = '') -> None:
        attach_payload = '{{"authorization": "{}"}}'.format(jwt_token)
        self._mqtt_client.publish(f'/devices/{device_id}/attach', attach_payload, qos=1)

    def detach(self, device_id: str) -> None:
        self._mqtt_client.publish(f'/devices/{device_id}/detach', '{}', qos=1)

    def publish_event(self, device_id: str, payload: str, qos: int = 0) -> None:
        self._mqtt_client.publish(f'/devices/{device_id}/events', payload, qos)

    def subscribe_to_config(self, device_id: str, callback: typing.Callable) -> None:
        self._subscribe(f'/devices/{device_id}/config', callback, qos=1)

    def subscribe_to_commands(
            self,
            device_id: str,
            callback: typing.Callable,
            subfolder: str = '#',
            qos: int = 1
    ) -> None:
        self._subscribe(f'/devices/{device_id}/commands/{subfolder}', callback, qos=qos)

    def _subscribe(self, topic: str, callback: typing.Callable, qos: int = 1) -> None:
        self._mqtt_client.subscribe(topic, qos=qos)
        self._subscriptions[topic] = callback
