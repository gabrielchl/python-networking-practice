#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import struct
import time
import select
import atexit
import statistics
import argparse

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
IP_HEADER_SIZE = 28

host = ''
send_count = 0
receive_count = 0
times = []

parser = argparse.ArgumentParser(description='Send ICMP ECHO_REQUEST to network hosts')

parser.add_argument('destination', type=str)
parser.add_argument('-c', '--count', type=int, help='Stop after sending count ECHO_REQUEST packets. With deadline option, ping waits for count ECHO_REPLY packets, until the timeout expires.')
parser.add_argument('-i', '--interval', type=float, default=1, help='Wait interval seconds between sending each packet. The default is to wait for one second between each packet normally. Hack this script to set interval to values less than 0.2 seconds.')
parser.add_argument('-t', '--timeout', type=float, default=1, help='Time to wait for a response, in seconds.')
parser.add_argument('-q', action='store_true', help='Quiet output. Nothing is displayed except the summary lines at startup time and when finished.')

args = parser.parse_args()

if args.interval < 0.2:
	print('ping: cannot flood; minimal interval allowed for user is 200ms')
	quit()


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


def receive_one_ping(icmp_socket, destination_address, ID, timeout):
	value_or_timeout = select.select([icmp_socket], [], [], timeout)
	if value_or_timeout[0] == []:
		return
	received = icmp_socket.recv(4096)
	global receive_count
	receive_count += 1
	receive_time = time.time()
	ttl = received[8]
	type, code, checksum_value, id, receive_seq_num = struct.unpack('bbHHH', received[20:28])
	if id != ID:
		return
	data_size = len(received) - 28
	return (receive_time, ttl, receive_seq_num, data_size)


def send_one_ping(icmp_socket, destination_address, ID, count):
	header = struct.pack('bbHHH', ICMP_ECHO_REQUEST, 0, 0, ID, count)
	data = struct.pack('8s', b'abcdefgh')
	checksum_result = checksum(header + data)
	icmp_socket.sendto(struct.pack('bbHHH', ICMP_ECHO_REQUEST, 0, checksum_result, ID, count) + data, destination_address)
	global send_count
	send_count += 1
	return time.time()


def do_one_ping(destination_address, count, timeout):
	try:
		icmp_socket = socket.socket(type=socket.SOCK_RAW, proto=socket.getprotobyname('icmp'))
	except PermissionError:
		print('Permission Error. Please run script as super user.')
		quit()
	send_time = send_one_ping(icmp_socket, destination_address, 64, count)
	receive_result = receive_one_ping(icmp_socket, destination_address, 64, timeout)
	icmp_socket.close()
	if receive_result is None:
		return None
	else:
		receive_time, ttl, receive_seq_num, data_size = receive_result
		return (receive_time - send_time, ttl, receive_seq_num, data_size)


def exit():
	if send_count == 0:
		return
	print(f'\n--- {host} ping statistics ---')
	print(f'{send_count} packets transmitted, {receive_count} received, {(send_count - receive_count) / send_count * 100:.0f}% packet loss')
	if len(times) < 2:
		stdev = 0
	else:
		stdev = statistics.stdev(times)
	print(f'rtt min/avg/max/mdev = {min(times):.3f}/{sum(times) / len(times):.3f}/{max(times):.3f}/{stdev:.3f} ms')


def ping(host_input):
	try:
		addr_info = socket.getaddrinfo(host, 80)[0][4]
	except socket.gaierror:
		print(f'ping: {host}: Name or service not known')
		quit()
	print(f'PING {host} ({addr_info[0]}) 8({8 + IP_HEADER_SIZE}) bytes of data.')
	atexit.register(exit)
	global send_count
	while True:
		try:
			time.sleep(args.interval)
			ping_result = do_one_ping(addr_info, send_count + 1, args.timeout)
			if ping_result is None:
				if not args.q:
					print('Request timed out.')
			else:
				delay, ttl, receive_seq_num, data_size = ping_result
				times.append(delay)
				if not args.q:
					print(f'{data_size} bytes from {socket.gethostbyaddr(addr_info[0])[0]} ({addr_info[0]}): icmp_seq={receive_seq_num} ttl={ttl} time={delay * 1000:.2f} ms')
			if args.count is not None and send_count >= args.count:
				break
		except KeyboardInterrupt:
			break


host = args.destination
ping(host)
