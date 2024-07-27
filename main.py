from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os
from threading import Thread
import socket
import json
from datetime import datetime

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message.html':
            self.send_html_file('message.html')
        elif pr_url.path.startswith('/static/'):
            self.send_static_file(pr_url.path)
        else:
            self.send_html_file('error.html', 404)

    def do_POST(self):
        if self.path == '/message':
            length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(length).decode('utf-8')
            data = urllib.parse.parse_qs(post_data)
            username = data['username'][0]
            message = data['message'][0]
            self.send_to_socket(username, message)
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        try:
            with open(filename, 'rb') as fd:
                self.wfile.write(fd.read())
        except FileNotFoundError:
            if status != 404:
                self.send_html_file('error.html', 404)

    def send_static_file(self, path, status=200):
        file_path = '.' + path
        self.send_response(status)
        if path.endswith('.css'):
            self.send_header('Content-type', 'text/css')
        elif path.endswith('.png'):
            self.send_header('Content-type', 'image/png')
        self.end_headers()
        try:
            with open(file_path, 'rb') as fd:
                self.wfile.write(fd.read())
        except FileNotFoundError:
            self.send_html_file('error.html', 404)

    def send_to_socket(self, username, message):
        data = json.dumps({'username': username, 'message': message})
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data.encode(), ('127.0.0.1', 5000))

def run_web_server():
    server_address = ('', 3000)
    http = HTTPServer(server_address, HttpHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_socket_server():
    if not os.path.exists('storage'):
        os.makedirs('storage')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 5000))
    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        file_path = 'storage/data.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}
        existing_data[timestamp] = message
        with open(file_path, 'w') as f:
            json.dump(existing_data, f, indent=4)

if __name__ == '__main__':
    thread_web = Thread(target=run_web_server)
    thread_socket = Thread(target=run_socket_server)
    thread_web.start()
    thread_socket.start()
    thread_web.join()
    thread_socket.join()