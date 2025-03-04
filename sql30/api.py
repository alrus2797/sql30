#!/usr/bin/env python
# Copyright (c) 2020 Vipin Sharma. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""
This module serves SQLITE database data as JSON through HTTP server.
"""
import json
import platform
import signal
import sys

from sys import argv
from http.server import BaseHTTPRequestHandler

IS_PYTHON2 = not platform.python_version().startswith('3')

try:
    _ = ModuleNotFoundError
except Exception:   # Python 3.6 and before.
    class ModuleNotFoundError(Exception):
        pass

try:
    from http.server import ThreadingHTTPServer
except (ModuleNotFoundError, ImportError):
    # python 3.6 and before.
    import socketserver
    from http.server import HTTPServer
    class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        pass

from sql30 import db

DBPATH = None


class SQL30Handler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    # GET sends back a Hello world message
    def do_GET(self):
        if not self.path or self.path == '/':
            response, error = json.dumps({'message': 'Welcome to SQL30', 'staus': 200}), None
        elif '/tables' not in self.path:
            response, error = "/tables/ is missing from path", True
        else:
            response, error = self._get_records()

        self.send_response(200 if not error else 400)
        self._set_headers()
        response = bytes(response, 'utf-8') if not IS_PYTHON2 else response
        self.wfile.write(response)

    def _get_records(self):
        class DummyDB(db.Model):
            pass

        with DummyDB(db_name=DBPATH) as dummydb:
            try:
                dummydb.fetch_schema()
                path = self.path.split('/')
                try:
                    tidx = path.index('tables')
                except Exception:
                    return "Invalid path", True
                dummydb.table = path[tidx+1]
                records = dummydb.read(include_header=True)
                return json.dumps(records), None
            except Exception as err:
                return str(err), str(err)


def start_server(db_path, server=ThreadingHTTPServer, handler=SQL30Handler, port=8008):
    global DBPATH
    DBPATH = db_path

    server_address = ('', port)
    server = server(server_address, handler)

    def signal_handler(sig, frame):
        print('Closing server..')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print('Starting httpd on port %d...' % port)
    server.serve_forever()


if __name__ == "__main__":
    if len(argv) >= 2:
        start_server(argv[1], port=int(argv[2]))
    else:
        start_server(None)
