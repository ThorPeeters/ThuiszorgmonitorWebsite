import asyncio
import websockets
import json
import scipy.signal as sig
import numpy as np
import pandas as pd

async def start_processing(data, websocket):
    fs = 500  # Sampling frequency
    cutoff1, cutoff2 = 5, 20  # Filter cutoff frequencies
    taps = 101
    fcof = sig.firwin(taps, [cutoff1 / (fs / 2), cutoff2 / (fs / 2)], pass_zero=False)
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
            print(filtereddata[0])

            # Send data to WebSocket
            if j % 10 == 0:  # Send data at intervals
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
