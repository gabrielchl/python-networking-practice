#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select
import binascii
import atexit
import statistics

ICMP_ECHO_REQUEST = 8 #ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0 #ICMP type code for echo reply messages
IP_HEADER_SIZE = 28

host = ''
send_count = 0
receive_count = 0
times = []

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
	# 1. Wait for the socket to receive a reply
	# 2. Once received, record time of receipt, otherwise, handle a timeout
	# 3. Compare the time of receipt to time of sending, producing the total network delay
	# 4. Unpack the packet header for useful information, including the ID
	# 5. Check that the ID matches between the request and reply
	# 6. Return total network delay
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
	# 1. Build ICMP header
	# 2. Checksum ICMP packet using given function
	# 3. Insert checksum into packet
	# 4. Send packet using socket
	# 5. Record time of sending
	icmp_socket.connect(destination_address)
	header = struct.pack('bbHHH', ICMP_ECHO_REQUEST, 0, 0, ID, count)
	data = struct.pack('8s', b'abcdefgh')
	checksum_result = checksum(header + data)
	icmp_socket.send(struct.pack('bbHHH', ICMP_ECHO_REQUEST, 0, checksum_result, ID, count) + data)
	global send_count
	send_count += 1
	return time.time()

def do_one_ping(destination_address, count, timeout):
	icmp_socket = socket.socket(type=socket.SOCK_RAW, proto=socket.getprotobyname('icmp'))
	send_time = send_one_ping(icmp_socket, destination_address, 0, count)
	receive_result = receive_one_ping(icmp_socket, destination_address, 0, timeout)
	if receive_result == None:
		return None
	else:
		receive_time, ttl, receive_seq_num, data_size = receive_result
		return (receive_time - send_time, ttl, receive_seq_num, data_size)
	# 1. Create ICMP socket
	# 2. Call sendOnePing function
	# 3. Call receiveOnePing function
	# 4. Close ICMP socket
	# 5. Return total network delay
	pass # Remove/replace when function is complete

def exit():
	if send_count == 0:
		return
	print(f'--- {host} ping statistics ---')
	print(f'{send_count} packets transmitted, {receive_count} received, {(send_count - receive_count) / send_count * 100:.0f}% packet loss')
	if len(times) < 2:
		stdev = 0
	else:
		stdev = statistics.stdev(times)
	print(f'rtt min/avg/max/mdev = {min(times):.3f}/{sum(times) / len(times):.3f}/{max(times):.3f}/{stdev:.3f} ms')

def ping(host_input, timeout=1):
	# 1. Look up hostname, resolving it to an IP address
	# 2. Call doOnePing function, approximately every second
	# 3. Print out the returned delay
	# 4. Continue this process until stopped
	addr_info = socket.getaddrinfo(host, 80)[0][4]
	print(f'PING {host} ({addr_info[0]}) 8({8 + IP_HEADER_SIZE}) bytes of data.')
	atexit.register(exit)
	for i in range(10):
		time.sleep(1)
		ping_result = do_one_ping(addr_info, i + 1, timeout)
		if ping_result == None:
			print('Request timed out.')
		else:
			delay, ttl, receive_seq_num, data_size = ping_result
			times.append(delay)
			print(f'{data_size} bytes from {socket.gethostbyaddr(addr_info[0])[0]} ({addr_info[0]}): icmp_seq={receive_seq_num} ttl={ttl} time={delay * 1000:.2f} ms')
	pass # Remove/replace when function is complete

host = 'lancaster.ac.uk'
ping(host)
