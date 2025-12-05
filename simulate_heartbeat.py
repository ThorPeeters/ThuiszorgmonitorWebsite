import time
import json
import random
import websocket


# WebSocket connectie naar de server
def on_open(ws):
    print("Verbinding geopend met WebSocket server")

    # Stuur elke seconde een willekeurige hartslag naar de server
    def send_heartbeat():
        while True:
            # Simuleer een willekeurige hartslag tussen 60 en 100
            hartslag = random.randint(60, 100)
            data = json.dumps({'hartslag': hartslag})
            ws.send(data)
            print(f"Verzonden hartslag: {hartslag}")
            time.sleep(1)  # Verzenden elke seconde

    send_heartbeat()


def on_message(ws, message):
    print(f"Bericht ontvangen van server: {message}")


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("WebSocket verbinding gesloten")



if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:8000/ws/hartslag/",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()
