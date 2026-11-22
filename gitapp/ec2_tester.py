import http.server
import socketserver
import urllib.request
import platform

PORT = 8080

def get_aws_metadata():
    """Fetches EC2 instance metadata using IMDSv2."""
    try:
        # Request an IMDSv2 token (required for modern EC2 instances) - changes to token for defect fix
            req_hash = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            method="PUT"
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            token = response.read().decode()

        metadata = {}
        # Fetch specific metadata endpoints and validte
        endpoints = ['instance-id', 'instance-type', 'placement/availability-zone', 'public-ipv4']
        for item in endpoints:
            try:
                req_meta = urllib.request.Request(
                    f"http://169.254.169.254/latest/meta-data/{item}",
                    headers={"X-aws-ec2-metadata-token": token}
                )
                with urllib.request.urlopen(req_meta, timeout=1) as res:
                    metadata[item] = res.read().decode()
            except Exception:
                metadata[item] = "Unavailable instance check further"
        return metadata
    except Exception:
        return None

class EC2TesterHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            meta = get_aws_metadata()
            aws_html = ""
            if meta:
                aws_html = "<h2>AWS EC2 Metadata</h2><ul>"
                for k, v in meta.items():
                    aws_html += f"<li><strong>{k}:</strong> {v}</li>"
                aws_html += "</ul>"
            else:
                aws_html = "<p><em>Not running on AWS EC2 (or metadata service is unreachable).</em></p>"

            sys_info = f"""
            <h2>System Information</h2>
            <ul>
                <li><strong>Hostname:</strong> {platform.node()}</li>
                <li><strong>OS:</strong> {platform.system()} {platform.release()}</li>
                <li><strong>Architecture:</strong> {platform.machine()}</li>
                <li><strong>Python Version:</strong> {platform.python_version()}</li>
            </ul>
            """

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>EC2 Instance Tester</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px auto; max-width: 650px; line-height: 1.6; color: #333; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .card {{ background: #f9f9f9; border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                    ul {{ list-style: none; padding: 0; }}
                    li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
                    li:last-child {{ border-bottom: none; }}
                    .status {{ color: #27ae60; font-weight: 600; font-size: 1.1em; }}
                </style>
            </head>
            <body>
                <h1>EC2 Instance Tester</h1>
                <div class="card">
                    <p class="status">✅ Web UI is running and responding successfully!</p>
                    {aws_html}
                </div>
                <div class="card">
                    {sys_info}
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            super().do_GET()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), EC2TesterHandler) as httpd:
        print(f"Serving UI on port {PORT}...")
        httpd.serve_forever()