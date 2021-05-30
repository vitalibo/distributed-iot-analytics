#!/usr/bin/env python3

import argparse
import logging
import socket
from random import randint, random

import sys
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(message)s')


class GatewayClient:

    def __init__(self, device_id: str):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._device_id = device_id

    def connect(self, gateway_ip: str, gateway_port: int):
        self._sock.connect((gateway_ip, gateway_port))
        logging.info('establish connection %s:%s', gateway_ip, gateway_port)

    def attach(self):
        self.detach()
        self._send(f'att {self._device_id}')

    def detach(self):
        self._send(f'det {self._device_id}')

    def publish(self, temperature: float, humidity: float):
        self._send(f'pub {temperature:.2f} {humidity:.2f}')

    def _send(self, message: str):
        self._sock.send(f'{message}\r\n'.encode())
        logging.debug(message)


def main(args):
    client = GatewayClient(args.device_id)
    client.connect(args.gateway_ip, args.gateway_port)
    client.attach()

    temperature = random() * 70 - 20
    humidity = random() * 100

    try:
        while True:
            temperature = max(-20, min(temperature + random() * 3.0 - 1.5, 50))
            humidity = max(0, min(humidity + random() * 5.0 - 2.5, 100))

            client.publish(temperature, humidity)
            time.sleep(randint(1, 5))

    except KeyboardInterrupt:
        client.detach()


def parse_args(args):
    parser = argparse.ArgumentParser(description='GCP IoT Core device emulator')
    parser.add_argument('--gateway_ip', type=str, default='127.0.0.1', help='Device Gateway IP address.')
    parser.add_argument('--gateway_port', type=int, default=10000, help='Device Gateway port.')
    parser.add_argument('--device_id', type=str, required=True, help='GCP IoT Core device ID.')
    return parser.parse_args(args=args)


if __name__ == '__main__':
    main(parse_args(sys.argv[1:]))
