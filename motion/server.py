"""Run the local MOTION DESIGN NELVIS interface."""
import base64
import binascii
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import UnidentifiedImageError

from render import ROOT, load_brief, render

LIMIT = 26 * 1024 * 1024
LOCK = threading.Lock()

class Handler(BaseHTTPRequestHandler):
    def respond(self, status, content, mime, headers=()):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        for key,value in headers:
            self.send_header(key,value)
        self.end_headers()
        self.wfile.write(content)

    def error(self, status, message):
        self.respond(status,json.dumps({"error":message},ensure_ascii=False).encode(),
                     "application/json; charset=utf-8")

    def do_GET(self):
        if self.path == "/":
            self.respond(200,(ROOT/"interface.html").read_bytes(),"text/html; charset=utf-8")
        else:
            self.error(404,"Page introuvable.")

    def do_POST(self):
        if self.path != "/render":
            return self.error(404,"Page introuvable.")
        local = f"http://127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != local.removeprefix("http://") or self.headers.get("Origin") != local:
            return self.error(403,"Utilisez l’adresse locale affichée par le serveur.")
        try:
            size = int(self.headers.get("Content-Length","0"))
        except ValueError:
            return self.error(400,"Taille de requête invalide.")
        if not 0 < size <= LIMIT:
            return self.error(413,"Fichiers trop volumineux.")
        if not LOCK.acquire(blocking=False):
            return self.error(429,"Un rendu est déjà en cours.")
        try:
            request = json.loads(self.rfile.read(size))
            if not isinstance(request,dict) or not isinstance(request.get("brief"),dict):
                raise ValueError("Paramètres de rendu invalides.")
            with tempfile.TemporaryDirectory(prefix="nelvis-") as folder:
                work = Path(folder)
                data = load_brief(ROOT/"examples"/"volt.json")
                for key in ("brand","model","hook","detail","tagline","accent","format"):
                    data[key] = request["brief"].get(key)
                image_data = request.get("images",[])
                if not isinstance(image_data,list) or len(image_data) not in (0,3):
                    raise ValueError("Ajoutez trois visuels ou utilisez les visuels VOLT.")
                if image_data:
                    data["images"] = [self.upload(item,work/f"image-{index}") for index,item in enumerate(image_data)]
                    data["demo_orbit"] = False
                elif data["brand"] != "VOLT":
                    data["demo_orbit"] = False
                voice = self.upload(request["voice"],work/"voice") if request.get("voice") else None
                model = "base" if request.get("transcribe") else None
                target = render(data,work/"MOTION_NELVIS.mp4",voice=voice,model=model,draft=bool(request.get("draft")))
                self.respond(200,target.read_bytes(),"video/mp4",
                             (("Content-Disposition",'attachment; filename="MOTION_NELVIS.mp4"'),))
        except (ValueError, TypeError, UnidentifiedImageError, binascii.Error, RuntimeError, OSError) as exc:
            self.error(400,str(exc)[:450])
        finally:
            LOCK.release()

    @staticmethod
    def upload(data, path):
        if not isinstance(data,str):
            raise ValueError("Fichier invalide.")
        path.write_bytes(base64.b64decode(data,validate=True))
        return path

if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1",8765),Handler) as server:
        print("MOTION DESIGN NELVIS — http://127.0.0.1:8765",flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
