# -*- coding: utf-8 -*-
#
# Copyright (C) 2016  Alex Revetchi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import zlib
import argparse
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from multiprocessing import Process, current_process, cpu_count
from SocketServer import ThreadingMixIn

parser = argparse.ArgumentParser()
parser.add_argument('www_root', help='directory/path to serve')
parser.add_argument('-port', default=8000, help='port number, default 8000')
parser.add_argument('-mode', default='mt', help='therading mode: mt - multithreaded, mp - multiprocessing, default multithreading')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def note(format, *args):
    sys.stderr.write('[%s]\t%s\n' % (current_process().name, format%args))

class DeflateHTTPHandler(SimpleHTTPRequestHandler):
	""" Adds compressed http payload"""

	def log_message(self, format, *args):
		note(format, *args)

	def zlib_encode(self, content):
		zlib_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)
		data = zlib_compress.compress(content) + zlib_compress.flush()
		return data

	def deflate_encode(self, ontent):
		deflate_compress = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
		data = deflate_compress.compress(content) + deflate_compress.flush()
		return data


	def gzip_encode(self, content):
		gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
		data = gzip_compress.compress(content) + gzip_compress.flush()
		return data


	def do_GET(self):
		"""Serve a GET request."""
		content = self.send_head()
		if content:
			self.wfile.write(content)

	def do_HEAD(self):
		"""Serve a HEAD request."""
		content = self.send_head()

	def send_head(self):
		path = self.translate_path(self.path)
		f = None
		if os.path.isdir(path):
			if not self.path.endswith('/'):
				# redirect browser - doing basically what apache does
				self.send_response(301)
				self.send_header("Location", self.path + "/")
				self.end_headers()
				return None
			for index in "index.html", "index.htm":
				index = os.path.join(path, index)
				if os.path.exists(index):
					path = index
					break
				else:
					return self.list_directory(path).read()
		ctype = self.guess_type(path)
		try:
			f = open(path, 'rb')
		except IOError:
			self.send_error(404, "File not found")
			return None

		content = f.read()
		encoding = None

		if (ctype.startswith('text/') or ctype.startswith('application/') or ctype.startswith('image/svg+xml')) and 'accept-encoding' in self.headers:
			if 'gzip' in self.headers['accept-encoding']:
				content = self.gzip_encode(content)
				encoding = 'gzip'
			elif 'zlib' in self.headers['accept-encoding']:
				content = self.zlib_encode(content)
				encoding = 'zlib'
			elif 'deflate' in self.headers['accept-encoding']:
				content = self.deflate_encode(content)
				encoding = 'deflate'

		self.send_response(200)
		self.send_header("Content-type", ctype)
		if encoding:
			self.send_header("Content-Encoding", encoding)
		fs = os.fstat(f.fileno())
		self.send_header("Content-Length", len(content))
		self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
		self.end_headers()
		f.close();
		return content

def serve_forever(server):
	note('starting server process ...')
	try:
		server.serve_forever(poll_interval=0.5)
	except KeyboardInterrupt:
		note('[DeflateHTTPServer] ^C received, shutting down...')
		raise

def runpool(server, number_of_processes):
	# create child processes to act as workers
	for i in range(number_of_processes-1):
		p = Process(target=serve_forever, args=(server,))
		p.daemon = True
		p.start()

	# main process also acts as a worker
	serve_forever(server)

# Multi-processing server
def run_mp(port):
	try:
		HTTPServer.allow_reuse_address = True
		server = HTTPServer(('', port), DeflateHTTPHandler)
		sockname = server.socket.getsockname()
		note('[MultiProcessingDeflateHTTPServer] started on %s port %s ...', sockname[0], sockname[1])


		ccount = cpu_count()
		if ccount > 8: ccount = ccount/2 
		runpool(server, ccount)

	except KeyboardInterrupt:
		note('[MultiProcessingDeflateHTTPServer] ^C received, shutting down...')
		server.shutdown()
		server.server_close()

# Multi-threaded server
def run_mt(port):
    try:
        ThreadedHTTPServer.allow_reuse_address = True
        server = ThreadedHTTPServer(('', port), DeflateHTTPHandler)
        sockname = server.socket.getsockname()
        note('[MultiThreadedDeflateHTTPServer] started on %s port %s ...', sockname[0], sockname[1])

#       Wait forever for incoming http requests
        server.serve_forever(poll_interval=0.5)

    except KeyboardInterrupt:
        note('[MultiThreadedDeflateHTTPServer] ^C received, shutting down...')
        server.shutdown()
        server.server_close()

def main(args):
	for arg in ('www_root', 'port', 'mode'):
		if not getattr(args, arg, None):
			print >> sys.stderr, '{} arg must not be empty'.format(arg)
			return -1
	os.chdir(args.www_root)

	if args.mode == 'mt':
		run_mt(int(args.port))
	elif args.mode == 'mp':
		run_mp(int(args.port))
	else:
		note('Unsupported server type: %s requested, fallback to MultiThreaded type...', args.mode)
		run_mt(int(args.port))

if __name__ == '__main__':
	sys.exit(main(parser.parse_args()))
