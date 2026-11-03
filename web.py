import threading

from flask import Flask, send_from_directory
from flask_sock import Sock
from simple_websocket import Client, ConnectionClosed

AURORA_HOST = "startendo.org"
AURORA_PORT = 7071

app = Flask(__name__)
sock = Sock(app)


class AuroraConnection:
    def __init__(self):
        self.websocket = Client.connect(f"ws://{AURORA_HOST}:{AURORA_PORT}/")
        self.running = True
        self._close_lock = threading.Lock()

    def send_raw(self, raw):
        self.websocket.send(raw)

    def receive(self):
        return self.websocket.receive()

    def close(self):
        with self._close_lock:
            if not self.running:
                return
            self.running = False

        if self.websocket.connected:
            try:
                self.websocket.close()
            except ConnectionClosed:
                pass


@sock.route("/ws")
def websocket_proxy(ws):
    aurora = AuroraConnection()

    def aurora_reader():
        try:
            while aurora.running:
                message = aurora.receive()
                if message is not None:
                    ws.send(message)
        except ConnectionClosed as e:
            if aurora.running:
                print("Aurora WebSocket closed:", e)
        except Exception as e:
            print("Aurora WebSocket reader error:", e)
        finally:
            aurora.close()
            try:
                ws.close()
            except Exception as e:
                print("Browser WebSocket close error:", e)

    reader_thread = threading.Thread(target=aurora_reader, daemon=True)
    reader_thread.start()

    try:
        while True:
            message = ws.receive()
            if message is None:
                break

            command = message.split("|", 1)[0]
            print("WS->AURORA command:", repr(command))
            aurora.send_raw(message)
    except Exception as e:
        print("Browser WebSocket error:", e)
    finally:
        aurora.close()

@app.route("/")
def index():
    return send_from_directory("HTML", "index.html")

@app.route("/web")
def web():
    return send_from_directory("HTML", "web.html")

@app.route("/web/v7.js")
def givejs():
    return send_from_directory("JS", "v7.js")
@app.route("/web/bg.js")
def givejs2():
    return send_from_directory("JS", "bg.js")
@app.route("/web/bg.png")
def givepng():
    return send_from_directory("IMAGES", "bg.png")
@app.route("/web/logo.png")
def givepng2():
    return send_from_directory("IMAGES", "logo.png")
@app.route("/web/font.tff")
def givefont():
    return send_from_directory("FONTS", "font.tff")
@app.route("/web/style.css")
def givecss():
    return send_from_directory("CSS", "style.css")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5992, # CHANGE OR THE REMOTE SERVER MAY BE ABLE TO USE AN AUTOMATED SYSTEM TO IP BAN. (I do not approve of illegal use though)
        threaded=True
    )
