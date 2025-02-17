#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socketserver
import atexit
import argparse
import traceback

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


def http_header(status_code):
	return HTTP_VERSION + STATUS_CODES[status_code] + HEADER_TAIL


def exit():
	if server is not None:
		server.shutdown()
		server.server_close()
		server.socket.close()
	print('\ngood bye :)')
	return


def create_html(title, content):
	html = '<html>'
	html += f'<head><title>{title}</title></head>'
	html += f'<body>{content}<hr><i>Python webserver at port {args.port}</i></body>'
	html += '</html>'
	return html


def handle_request(request, client_address, server):
	try:
		request_data = request.recv(2048)
		request_structured = request_data.split(b'\r\n')
		method, target, http_version = request_structured[0].split(b' ')
		print(f'{method} {target}')
		if http_version != b'HTTP/1.1':
			request.send(http_header(505) + str.encode(create_html('505 HTTP Version not supported', f'<h1>HTTP Version not supported</h1>The server does not support your HTTP version and was unable to complete your request.')))
			print(505)
			return
		if method == b'GET':
			if target == b'/':
				target = b'/index.html'
			try:
				f = open(target[1:], 'r')
				request.send(http_header(200) + str.encode(f.read()))
				print(200)
				f.close()
			except FileNotFoundError:
				try:
					f = open('404.html', 'r')
					request.send(http_header(404) + str.encode(f.read()))
					print(400)
					f.close()
				except FileNotFoundError:
					target_str = str(target, 'ascii')
					request.send(http_header(404) + str.encode(create_html('404 Not Found', f'<h1>Not Found</h1>The requested URL {target_str} was not found on this server')))
					print(400)
	except Exception:
		traceback.print_exc()
		request.send(http_header(500) + str.encode(create_html('500 Internal Server Error', f'<h1>Internal Server Error</h1>The server encountered an internal error or misconfiguration and was unable to complete your request.')))
		print(500)


def start_server(server_address, server_port):
	global server
	try:
		while server is None:
			try:
				server = socketserver.TCPServer((server_address, server_port), handle_request)
				ip, port = server.server_address
				print(f'{ip}:{port}')
				server.serve_forever()
			except OSError as e:
				if e.errno == 98:
					print(f'port {server_port} occupied, attempting to bind server to port {server_port + 1}')
					server_port += 1
	except KeyboardInterrupt:
		quit()


atexit.register(exit)
start_server('', args.port)
