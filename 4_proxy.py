#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import socketserver
import atexit
import argparse
import struct

parser = argparse.ArgumentParser(description='A python webserver')
parser.add_argument('-p', '--port', type=int, default=8963, help='Specifies the port for the server to bind to. The default is 8963.')
args = parser.parse_args()

server = None

HTTP_VERSION = b'HTTP/1.1'
STATUS_CODES = {
	200: b'200 OK',
	301: b'301 Moved Permanently',
	307: b'307 Temporary Redirect',
	400: b'400 Bad Request',
	401: b'401 Unauthorized',
	403: b'403 Forbidden',
	404: b'404 Not Found',
	500: b'500 Internal Server Error',
	505: b'505 HTTP Version not supported'
}
HEADER_TAIL = b'\r\n\r\n'


def checksum(string):
	csum = 0
	countTo = (len(string) // 2) * 2
	count = 0

	while count < countTo:
		thisVal = string[count+1] * 256 + string[count]
		csum = csum + thisVal
		csum = csum & 0xffffffff
		count = count + 2

	if countTo < len(string):
		csum = csum + string[len(string) - 1]
		csum = csum & 0xffffffff

	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum
	answer = answer & 0xffff
	answer = answer >> 8 | (answer << 8 & 0xff00)

	answer = socket.htons(answer)

	return answer


def exit():
	pass
	# server.server_close()
	# server.socket.close()


def send_request(target_socket, dest, request_data):
	print(dest)
	# header = struct.pack('HHiiHHHH', socket.htons(8963), socket.htons(80), 1, 1, socket.htons(0b101000000011000), socket.htons(502), 0, 0)
	# checksum_value = checksum(header)
	# packet = struct.pack('HHiiHHHH', socket.htons(8963), socket.htons(80), 1, 1, socket.htons(0b101000000011000), socket.htons(502), checksum_value, 0) + b'GET / HTTP/1.1\r\n' + b'\r\n'.join(request_data.splitlines()[1:-2])
	#print(socket.getaddrinfo(dest, 80)[0][4])
	target_socket.sendall(request_data)
	pass


def get_reply(target_socket):
	received, source_addr = target_socket.recvfrom(4096)
	return received


def handle_request(request, client_address, server):
	request_data = request.recv(2048)
	request_structured = str(request_data, 'ascii').splitlines()
	method, target, http_version = request_structured[0].split(' ')
	print(f'{method} {target}')
	print(request_structured)
	dest = request_structured[1].split(' ')[1]
	target_socket = socket.socket(type=socket.SOCK_STREAM)
	target_socket.connect((dest, 80))
	send_request(target_socket, dest, request_data)
	received = get_reply(target_socket)
	request.send(received)
	target_socket.close()


def start_server(server_address, server_port):
	global server
	server = socketserver.TCPServer((server_address, server_port), handle_request)
	ip, port = server.server_address
	print(f'{ip}:{port}')
	server.serve_forever()


atexit.register(exit)
start_server('', args.port)
