# server.py — HTTP-сервер + универсальный прокси для KudaGo и Ticketmaster
import http.server
import socketserver
import urllib.request
import os
import sys

PORT = 8000

PROXIES = {
    '/kudago/':       'https://kudago.com/public-api/v1.4',
    '/ticketmaster/': 'https://app.ticketmaster.com/discovery/v2',
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        for prefix, target_base in PROXIES.items():
            if self.path.startswith(prefix):
                real_path = self.path[len(prefix) - 1:]  # сохраняем ведущий /
                target_url = target_base + real_path
                try:
                    req = urllib.request.Request(target_url, headers={
                        'User-Agent': 'Mozilla/5.0 (DashboardProxy/1.0)',
                        'Accept': 'application/json',
                    })
                    with urllib.request.urlopen(req, timeout=20) as response:
                        body = response.read()
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Content-Length', str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                except Exception as e:
                    error_body = ('{"error": "' + str(e).replace('"', "'") + '"}').encode('utf-8')
                    self.send_response(502)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(error_body)))
                    self.end_headers()
                    self.wfile.write(error_body)
                return
        super().do_GET()

    def log_message(self, format, *args):
        for prefix in PROXIES:
            if prefix in self.path:
                sys.stderr.write("PROXY: %s\n" % self.path)
                return

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Сервер: http://localhost:{PORT}/дашбординг1.html")
    print("Прокси: /kudago/* → kudago.com, /ticketmaster/* → app.ticketmaster.com")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлен.")