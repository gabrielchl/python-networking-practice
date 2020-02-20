#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import socketserver
import atexit
import argparse
import sys
import select
import struct
import threading

def string_to_bool(input):
	return input.lower() in ['yes', 'y', 'ya', 'yup', 'hellya', 'sure', 'true', 't', 1]


parser = argparse.ArgumentParser(description='A python webserver')
parser.add_argument('-p', '--port', type=int, default=8963, help='Specifies the port for the server to bind to. The default is 8963.')
parser.add_argument('-t', '--timeout', type=float, default=5, help='Time to wait for a response from the target server, in seconds.')
parser.add_argument('-v', '--verbal', type=string_to_bool, default=False, help='Provides verbal output. The default is false.')
parser.add_argument('-c', '--cache', type=string_to_bool, default=True, help='Support basic cache. The default is true.')
args = parser.parse_args()

server = None

cache = {}


def exit():
	return
	# server.server_close()
	# server.socket.close()


def send_request(target_socket, dest, request_data):
	target_socket.sendall(request_data)
	return


def get_reply(target_socket):
	# retrieve first 1024 bytes
	received_header, _ = target_socket.recvfrom(1024)
	received_header_structured = received_header.split(b'\r\n')

	# get content length
	content_length = 0
	for line in received_header_structured:
		line = line.split(b': ')
		if line[0].lower() == b'content-length':
			content_length = int(line[1])

	# determine if we need to get more bytes
	header_length = len(received_header.split(b'\r\n\r\n', 1)[0])
	if 1024 - header_length < content_length:
		received_body, _ = target_socket.recvfrom(content_length)
		return received_header + received_body
	else:
		return received_header


def handle_request(request, client_address, server):
	request_data = request.recv(2048)
	request_structured = request_data.split(b'\r\n')
	method, target, http_version = request_structured[0].split(b' ')
	print(f'{method} {target}')

	# attempt to retrieve webpage from cache
	if target in cache and args.cache:
		if args.verbal:
			print('retrieved from cache')
		request.send(cache[target])
		return

	# create socket to server
	dest = request_structured[1].split(b' ')[1]
	target_socket = socket.socket(type=socket.SOCK_STREAM)
	target_socket.settimeout(5)
	target_socket.connect((dest, 80))

	# send user's packet to server
	send_request(target_socket, dest, request_data)

	# get reply from server
	received = get_reply(target_socket)

	# cache webpage
	if target not in cache and args.cache:
		if args.verbal:
			print('cached')
		cache[target] = received

	# send reply from server to user
	request.send(received)
	target_socket.close()
	return


def start_server(server_address, server_port):
	global server
	while server == None:
		try:
			server = socketserver.TCPServer((server_address, server_port), handle_request)
		except OSError as e:
			if e.errno == 98:
				print(f'port {server_port} occupied, attempting to bind server to port {server_port + 1}')
				server_port += 1
	ip, port = server.server_address
	print(f'server bound to {ip}:{port}')
	server.serve_forever()
	return


def monitor_input():
	while True:
		command = input()
		if command.lower() == 'cache-list':
			for url, _ in cache.items():
				print(str(url, 'ascii'))


input_thread = threading.Thread(target=monitor_input)
input_thread.start()

atexit.register(exit)
start_server('', args.port)
