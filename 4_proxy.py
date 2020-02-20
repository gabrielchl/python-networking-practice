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


def exit():
	return
	# server.server_close()
	# server.socket.close()


def send_request(target_socket, dest, request_data):
	# print(dest)
	target_socket.sendall(request_data)
	return


def get_reply(target_socket):
	received, source_addr = target_socket.recvfrom(4096)
	return received


def handle_request(request, client_address, server):
	request_data = request.recv(2048)
	request_structured = str(request_data, 'ascii').splitlines()
	method, target, http_version = request_structured[0].split(' ')
	print(f'{method} {target}')

	# create socket to server
	dest = request_structured[1].split(' ')[1]
	print(dest)
	target_socket = socket.socket(type=socket.SOCK_STREAM)
	target_socket.connect((dest, 80))

	# send user's packet to server
	send_request(target_socket, dest, request_data)

	# get reply from server
	received = get_reply(target_socket)

	# send reply from server to user
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
