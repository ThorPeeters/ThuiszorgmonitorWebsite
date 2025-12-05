import asyncio
import websockets
import json
import numpy as np
import pandas as pd
import scipy.signal as sig

clients = set()  # Keep track of connected clients

async def start_processing(data, websocket):
    global clients
    clients.add(websocket)  # Add client to set

    fs = 500  # Sampling frequency
    taps = 101
    fcof = sig.firwin(taps, [5 / (fs / 2), 20 / (fs / 2)], pass_zero=False)
    z = sig.lfilter_zi(fcof, 1)

    filtereddata = []
    obtaindata = []
    t = [0]  # Time axis
    Ts = 1 / fs  # Sampling period

    for j in range(len(data)):
        obtaindata.append(data[j])

        if len(obtaindata) > taps:
            removeDC = obtaindata - np.mean(obtaindata)
            filtered_sample, z = sig.lfilter(fcof, 1, [removeDC[-1]], zi=z)
            filtereddata.append(filtered_sample[0])

            if len(filtereddata) > 1000:  # Limit displayed points
                filtereddata = filtereddata[1:]
                t = t[1:]

            t.append(t[-1] + Ts)

            # Send data at a slower rate (every 20 samples)
            if j % 5 == 0:
                await websocket.send(json.dumps({
                    "t": t[-1],
                    "filtered": filtered_sample[0]
                }))


# WebSocket server
async def ecg_server(websocket, path):
    x = pd.read_csv("s21_walk.csv")
    data = x["ecg"].to_numpy()
    await start_processing(data, websocket)

start_server = websockets.serve(ecg_server, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
