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
import SocketServer
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class DeflateHTTPHandler(SimpleHTTPRequestHandler):
	""" Adds compressed http payload"""

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

		if (ctype.startswith('text/') or ctype.startswith('application/')) and 'accept-encoding' in self.headers:
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

def run(port):
	try:
		ThreadedHTTPServer.allow_reuse_address = True
		server = ThreadedHTTPServer(('', port), DeflateHTTPHandler)
		sockname = server.socket.getsockname()
		print '[DeflateHTTPServer] started on', sockname[0], 'port', sockname[1], '...'

#       Wait forever for incoming http requests
		server.serve_forever(poll_interval=0.5)

	except KeyboardInterrupt:
		print '[DeflateHTTPServer] ^C received, shutting down...'
		server.shutdown()
		server.server_close()

if __name__ == '__main__':
	if sys.argv[1:]:
		port = int(sys.argv[1])
	else:
		port = 8000
	run(port)
