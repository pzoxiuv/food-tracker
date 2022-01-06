#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
import ssl
from urllib import parse
import json
import os
import mimetypes
import csv
from functools import partial

class WebServer:
    def __init__(self, protein_file='protein.list', secure=True, port=8080, address='0.0.0.0'):
        if secure:
            self.port = 443
        else:
            self.port = port
        self.secure = secure
        self.address = address

        server_address = (self.address, self.port)
        handler = partial(HTTPHandler, protein_file)
        self.httpd = HTTPServer(server_address, handler)

        if secure:
            print('Secure mode unsupported')
            assert False

    def run(self):
        print(f'Running HTTP server... secure: {self.secure} {self.address}:{self.port}')
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        self.httpd.server_close()

class HTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, protein_file, *args, **kwargs):
        self.protein_file = protein_file

        super().__init__(*args, **kwargs)

    def _set_response(self, resp=200, fname='', ctype='text/plain'):
        self.send_response(resp)
        if fname != '':
            ctype = mimetypes.guess_type(fname)[0]
        self.send_header('Content-type', ctype)
        self.end_headers()

    def do_GET(self):
        print(f'GET request,\nPath: {self.path}\nHeaders:\n{self.headers}\n')

        path = parse.urlsplit(self.path)
        if path.path.startswith('/protein'):
            p = path.path.lstrip('/protein')
        else:
            p = path.path
        if p == '':
            p = '/'
        print(path)
        print(p)

        if p == '/':
            self._set_response(fname='protein.html')
            with open('protein.html') as f:
                self.wfile.write(f.read().encode('utf-8'))

        elif p == '/get-data':
            with open(self.protein_file) as f:
                reader = csv.DictReader(f)
                data = [r for r in reader]
                self._set_response(ctype='application/json')
                self.wfile.write(json.dumps(data).encode('utf-8'))

        elif os.path.exists(os.path.basename(p)):
            fname = os.path.basename(p)
            self._set_response(fname=fname)
            with open(fname) as f:
                self.wfile.write(f.read().encode('utf-8'))

        else:
            print('not found')
            self._set_response(404)
            self.wfile.write(f'{self.path} not found'.encode('utf-8'))

    def do_POST(self):
        print(f'POST request,\nPath: {self.path}\nHeaders:\n{self.headers}\n')

        #form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        #form.getvalue("
        length = int(self.headers['content-length'])
        data = self.rfile.read(length)
        try:
            table_data = json.loads(data)
        except Exception as e:
            self._set_response(404)
            self.wfile.write(f'exception parsing table data to json'.encode('utf-8'))
            print(e)
            return

        print(table_data)

        with open(self.protein_file, 'w') as f:
            fieldnames = table_data[-1].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in table_data:
                writer.writerow(r)

        self._set_response(200)
        self.wfile.write(f'ok'.encode('utf-8'))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--port', required=False, default=8080, type=int)
    p.add_argument('-s', '--secure', required=False, action='store_true', default=False)
    p.add_argument('-a', '--listen-address', required=False, default='0.0.0.0')
    p.add_argument('-f', '--protein-file', required=False, default='protein.list')
    a = p.parse_args()

    print(a)

    webserver = WebServer(a.protein_file, a.secure, a.port, a.listen_address)
    webserver.run()
