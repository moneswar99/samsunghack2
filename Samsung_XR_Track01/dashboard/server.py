"""
Dashboard HTTP Server for Samsung XR Hackathon Track 01
Serves the web viewer, rendered frames, contact sheet, and metadata.
"""

import os
import sys
import http.server
import socketserver

PORT = 8000
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class HackathonHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Strip query parameters
        clean_path = path.split('?', 1)[0].split('#', 1)[0]
        
        if clean_path in ('/', '/index.html'):
            return os.path.join(project_root, 'dashboard', 'index.html')
        elif clean_path == '/metadata.json':
            return os.path.join(project_root, 'metadata.json')
        elif clean_path == '/contact_sheet.png':
            return os.path.join(project_root, 'contact_sheet.png')
        elif clean_path.startswith('/renders/'):
            filename = os.path.basename(clean_path)
            return os.path.join(project_root, 'renders', filename)
        elif clean_path.startswith('/textures/'):
            filename = os.path.basename(clean_path)
            return os.path.join(project_root, 'textures', filename)
        else:
            return os.path.join(project_root, clean_path.lstrip('/'))

def run_server():
    os.chdir(project_root)
    # Enable socket address reuse to prevent 'address already in use' errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), HackathonHandler) as httpd:
        print("=" * 72)
        print(f"  SAMSUNG XR HACKATHON DASHBOARD SERVER RUNNING")
        print(f"  URL: http://localhost:{PORT}")
        print("=" * 72)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()
