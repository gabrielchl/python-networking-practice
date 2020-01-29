#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socketserver
import atexit

server = None

HTTP_VERSION = b'HTTP/1.1'
STATUS_CODES = {
	200: b'OK',
	301: b'Moved Permanently',
	307: b'Temporary Redirect',
	400: b'Bad Request',
	401: b'Unauthorized',
	403: b'Forbidden',
	404: b'Not Found',
	500: b'Internal Server Error',
	505: b'HTTP Version not supported'
}
HEADER_TAIL = b'\r\n\r\n'


def exit():
	server.server_close()
	server.socket.close()


def create_html(title, content):
	html = '<html>'
	html += f'<head><title>{title}</title></head>'
	html += f'<body>{content}<hr><i>Python webserver</i></body>'
	html += '</html>'
	return html


def handle_request(request, client_address, server):
	request_data = request.recv(2048)
	request_structured = str(request_data, 'ascii').splitlines()
	method, target, http_version = request_structured[0].split(' ')
	print(f'{method} {target}')
	if method == 'GET':
		try:
			f = open(target[1:], 'r')
			request.send(HTTP_VERSION + STATUS_CODES[200] + HEADER_TAIL + str.encode(f.read()))
			f.close()
		except FileNotFoundError:
			try:
				f = open('404.html', 'r')
				request.send(HTTP_VERSION + STATUS_CODES[404] + HEADER_TAIL + str.encode(f.read()))
				f.close()
			except FileNotFoundError:
				request.send(HTTP_VERSION + STATUS_CODES[404] + HEADER_TAIL + str.encode(create_html('404 Not Found', f'The requested URL {target} was not found on this server')))


def start_server(server_address, server_port):
	server = socketserver.TCPServer((server_address, server_port), handle_request)
	ip, port = server.server_address
	print(f'{ip}:{port}')
	server.serve_forever()


atexit.register(exit)
start_server('', 8963)
