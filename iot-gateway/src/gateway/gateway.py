import _thread as thread
import socket
import sys


def on_new_client(connection, client_address):
    print('connection from %s:%d open' % client_address)

    try:
        while True:
            data = connection.recv(1)
            sys.stdout.write(data.decode('utf-8'))
    finally:
        print('connection from %s:%s close' % client_address)
        connection.close()


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('192.168.0.100', 10000)
    sock.bind(server_address)
    sock.listen(10)

    try:
        while True:
            connection, client_address = sock.accept()
            thread.start_new_thread(on_new_client, (connection, client_address))
    except KeyboardInterrupt:
        print('exiting')
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


if __name__ == '__main__':
    main()
