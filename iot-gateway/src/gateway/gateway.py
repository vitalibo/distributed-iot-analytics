import argparse
import json
import logging
import socket
import typing
from datetime import datetime
from threading import Thread

import sys

try:
    import gcp
except ModuleNotFoundError:
    from gateway import gcp

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')


class DeviceProxy(Thread):
    __devices = {}

    def __init__(self, connection, address, mqtt, now_supplier=datetime.now):
        super().__init__()
        self.__connection = connection
        self.__address = address
        self.__mqtt = mqtt
        self._device_id = None
        self.__now_supplier = now_supplier

    def run(self):
        commands = {
            'att': self.attach,
            'det': self.detach,
            'pub': self.publish
        }

        try:
            logging.info('connection from %s:%d open.' % self.__address)
            for command, *args in self.recv_cmd():
                func = commands.get(command, lambda *_: logging.warning('unknown command: %s %s.' % (command, args)))
                func(*args)
        except Exception as e:
            logging.warning(e)
        finally:
            if self._device_id:
                self.detach(self._device_id)
            self.__connection.close()
            logging.info('connection from %s:%s close.' % self.__address)

    def attach(self, device_id):
        self.__mqtt.attach(device_id)
        self._device_id = device_id
        DeviceProxy.register(device_id, self.__connection)
        logging.debug('attach %s.' % device_id)

    def detach(self, device_id):
        self.__mqtt.detach(device_id)
        self._device_id = None
        DeviceProxy.deregister(device_id)
        logging.debug('detach %s.' % device_id)

    def publish(self, temperature, humidity):
        payload = {
            'ip': self.__address[0],
            'timestamp': int(self.__now_supplier().timestamp()),
            'temperature': float(temperature),
            'humidity': float(humidity)
        }

        self.__mqtt.publish_event(self._device_id, json.dumps(payload))
        logging.debug(payload)

    @classmethod
    def register(cls, device_id, connection):
        cls.__devices[device_id] = connection

    @classmethod
    def deregister(cls, device_id):
        if device_id in cls.__devices:
            cls.__devices[device_id].close()
            del cls.__devices[device_id]

    def recv_cmd(self) -> typing.Iterable[typing.Tuple]:
        buffer = b''
        while True:
            data = self.__connection.recv(1)
            if data == b'\r':
                continue
            elif data == b'\n':
                yield buffer.decode('utf-8') \
                    .split(' ')
                buffer = b''
            else:
                buffer += data


def main(args):
    server_address = (args.server_ip, args.server_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen(10)
    logging.info('server started: %s.', server_address)

    mqtt = gcp.MQTTIoTCore(**vars(args))
    mqtt.connect()

    try:
        while True:
            connection, address = sock.accept()
            thread = DeviceProxy(connection, address, mqtt)
            thread.start()
    except KeyboardInterrupt:
        logging.info('exiting.')
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


def parse_args(args):
    parser = argparse.ArgumentParser(description='Google Cloud IoT Core MQTT device gateway.')
    parser.add_argument('--server_ip', type=str, default='0.0.0.0', help='Socket server host IP address for bind.')
    parser.add_argument('--server_port', type=int, default=10000, help='Socket server port for bind.')
    parser.add_argument('--project_id', type=str, required=True, help='GCP cloud project name.')
    parser.add_argument('--region', type=str, default='us-central1', help='GCP cloud region.')
    parser.add_argument('--registry_id', type=str, required=True, help='GCP IoT Core registry ID.')
    parser.add_argument('--gateway_id', type=str, required=True, help='GCP IoT Core device gateway ID.')
    parser.add_argument('--private_key_file', type=str, required=True, help='Path to private key file.')
    parser.add_argument('--algorithm', type=str, choices=('RS256', 'ES256'), required=True,
                        help='Which encryption algorithm to use to generate the JWT.')
    parser.add_argument('--ca_certs', type=str, required=True,
                        help="CA root from 'https://pki.google.com/roots.pem'.")
    parser.add_argument('--mqtt_bridge_hostname', type=str, default='mqtt.googleapis.com',
                        help='GCP IoT MQTT bridge hostname.')
    parser.add_argument('--mqtt_bridge_port', type=int, default=8883, help='GCP IoT MQTT bridge port.')
    parser.add_argument('--jwt_expires_in_minutes', type=int, default=15,
                        help='JWT token expiration time, in minutes.')
    return parser.parse_args(args=args)


if __name__ == '__main__':
    main(parse_args(sys.argv[1:]))
