import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(__file__))
import services


class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        try:
            if path == '/api/tickets':
                status = query.get('status', [None])[0]
                priority = query.get('priority', [None])[0]
                group = query.get('group', [None])[0]
                keyword = query.get('keyword', [None])[0]
                result = services.get_ticket_list(
                    status=status, priority=priority, group=group, keyword=keyword)
                self._set_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

            elif path == '/api/tickets/stats':
                result = services.get_full_statistics()
                self._set_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

            elif path.startswith('/api/tickets/'):
                ticket_id = path.split('/')[-1]
                result = services.get_ticket_by_id(ticket_id)
                if result:
                    self._set_headers()
                    self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({'error': 'not found'}, ensure_ascii=False).encode('utf-8'))

            elif path == '/api/meta':
                from models import STATUS_OPTIONS, PRIORITY_OPTIONS, GROUP_OPTIONS, STATUS_LABELS, GROUP_LABELS, VALID_TRANSITIONS
                meta = {
                    'statuses': [{'value': s, 'label': STATUS_LABELS.get(s, s)} for s in STATUS_OPTIONS],
                    'priorities': [{'value': p, 'label': {'low': 'low', 'medium': 'medium', 'high': 'high'}[p]} for p in PRIORITY_OPTIONS],
                    'groups': [{'value': g, 'label': GROUP_LABELS.get(g, g)} for g in GROUP_OPTIONS],
                    'transitions': VALID_TRANSITIONS
                }
                self._set_headers()
                self.wfile.write(json.dumps(meta, ensure_ascii=False).encode('utf-8'))

            elif path == '/' or path == '/index.html':
                self._serve_static('index.html', 'text/html; charset=utf-8')
            elif path == '/style.css':
                self._serve_static('style.css', 'text/css; charset=utf-8')
            elif path == '/app.js':
                self._serve_static('app.js', 'application/javascript; charset=utf-8')
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'not found'}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            if path == '/api/tickets':
                result = services.create_ticket(
                    title=data.get('title', ''),
                    priority=data.get('priority', 'medium'),
                    group=data.get('group', 'logistics'),
                    assignee=data.get('assignee', ''),
                    location=data.get('location', ''),
                    contact=data.get('contact', ''),
                    deadline=data.get('deadline'),
                    operator=data.get('operator', 'web')
                )
                if result['success']:
                    self._set_headers(201)
                else:
                    self._set_headers(400)
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

            elif path.startswith('/api/tickets/') and path.endswith('/assign'):
                ticket_id = path.split('/')[3]
                result = services.assign_ticket(
                    ticket_id,
                    assignee=data.get('assignee', ''),
                    operator=data.get('operator', 'web')
                )
                if result['success']:
                    self._set_headers(200)
                else:
                    self._set_headers(400)
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'not found'}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            if path.startswith('/api/tickets/') and not path.endswith('/assign'):
                ticket_id = path.split('/')[-1]
                new_status = data.get('status', '')
                result = services.update_ticket_status(
                    ticket_id, new_status, operator=data.get('operator', 'web'))
                if result['success']:
                    self._set_headers(200)
                else:
                    self._set_headers(400)
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'not found'}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))

    def _serve_static(self, filename, content_type):
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        filepath = os.path.join(frontend_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self._set_headers(content_type=content_type)
            self.wfile.write(content.encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'file not found'}, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        pass


def run(host='localhost', port=8000):
    server_address = (host, port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f'Server running at http://{host}:{port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
        httpd.server_close()


if __name__ == '__main__':
    run()
