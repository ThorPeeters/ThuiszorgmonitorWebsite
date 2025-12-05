import asyncio
import random
import websockets
import django
import os
import json
from time import sleep
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.signal as sig
from sklearn import preprocessing
from scipy.signal import find_peaks, butter, lfilter
from urllib3 import request


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ThuiszorgmonitorWeb.settings')
django.setup()

from Thuiszorgmonitor.models import Heartbeat  # Importeer je model
from Thuiszorgmonitor.views import is_heartbeat_ok
from datetime import datetime
from asgiref.sync import sync_to_async
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model

import numpy as np
import matplotlib
"""matplotlib.use('TkAgg')"""
import matplotlib.pyplot as plt
import pandas as pd
import scipy.signal as sig
import time

User = get_user_model()











def start_processing(data):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    fig.suptitle("ECG Signal", fontsize=14)
    ax1.set_ylabel('Amplitude (μV)')
    ax1.set_xlabel('Time (s)')
    ax1.grid()
    plt.ion()  # Interactive mode

    obtaindata = []
    filtereddata = []

    t = [0]  # Time axis
    fs = 500  # Sample frequency in Hz
    cutoff1, cutoff2 = 5, 20  # Filter cutoff frequencies
    taps = 101  # Number of filter taps
    window_size = 1000  # Number of samples to display in the plotfig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))


    # Initialize plot objects
    graph1, = ax1.plot([], [], color='b', label="ECG Signal")

    # Configure axes

    values_forDCremoval = 5000  # Higher: more accurate DC removal, lower performance
    refresh_rate = 10  # Desired plot refresh rate in Hz
    max_refresh_rate = 15  # Max refresh rate limit
    min_refresh_rate = 3  # Min refresh rate limit

    # Initialize variables
    Ts = 1 / fs  # Sampling period
    delay = (taps - 1) / (2 * fs)  # Filter delay (in time)
    samples_before_start = int(delay * fs - 1)


    # Initialize filter
    fcof = sig.firwin(taps, [cutoff1 / (fs / 2), cutoff2 / (fs / 2)], pass_zero=False)
    z = sig.lfilter_zi(fcof, 1)

    # Create subplots


    plt.ion()  # Interactive mode
    # Real-time processing loop
    for j in range(len(data)):



        # Adjust index for filtering
        i = int(j - fs * delay)

        # Collect original data
        obtaindata.append(data[j])


        # Maintain data window size
        if len(filtereddata) > window_size:
            filtereddata = filtereddata[1:]
            t = t[1:]
        if len(obtaindata) > values_forDCremoval:
            obtaindata = obtaindata[1:]

        # Apply DC removal and filter at the start point
        if j == samples_before_start:
            removeDC = obtaindata - np.mean(obtaindata)
            _, z = sig.lfilter(fcof, 1, removeDC, zi=z)
            start_time = time.time()

        # Apply filter to the data after the start point
        if j > samples_before_start:
            # Filter the current sample
            filteredsample, z = sig.lfilter(fcof, 1, [data[j] - np.mean(obtaindata)], zi=z)
            filtereddata.append(filteredsample[0])

            # Refresh plots at specified intervals
            if i % int(fs / refresh_rate) == 0:
                # Calculate the expected time for the next update
                expected_time = i * Ts

                # Calculate how much time we need to wait
                elapsed_time = time.time()  - start_time
                time_to_wait = expected_time - elapsed_time


                # Adjust refresh rate dynamically



                # Wait for the correct time interval to pass
                if time_to_wait > 0:
                    time.sleep(time_to_wait)

                # Update original signal plot


                ax1.autoscale_view()
                ax1.relim()

                # Update filtered signal plot
                graph1.set_data(t, filtereddata)

                ax1.autoscale_view()
                ax1.relim()


                # Set x-axis limits to focus on the most recent data
                if i >= window_size:
                    ax1.set_xlim(t[-window_size], t[-1])
                else:
                    ax1.set_xlim(t[0], t[-1])



                # Redraw the plots
                plt.pause(0.01)
            if (j % 500) == 0:
                print(time_to_wait)
                print("refresh rate:", refresh_rate)
                if time_to_wait > 0:
                    if refresh_rate < max_refresh_rate:
                        refresh_rate += time_to_wait * 4
                else:
                    if refresh_rate > min_refresh_rate:
                        refresh_rate += time_to_wait * 4
            # Update the time axis for the current sample
            t.append(t[-1] + Ts)
            filtereddata = [int(x) for x in filtereddata]
    return filtereddata























async def get_logged_in_user_age():
    """
    Retrieve the age of the currently logged-in user in an async context.
    """
    try:
        # Fetch all active sessions asynchronously
        sessions = await sync_to_async(
            lambda: list(Session.objects.filter(expire_date__gte=datetime.now()))
        )()

        for session in sessions:
            try:
                # Decode each session asynchronously
                data = await sync_to_async(session.get_decoded)()
                user_id = data.get('_auth_user_id')  # Get the user ID from the session
                if user_id:
                    # Fetch the user asynchronously
                    user = await sync_to_async(User.objects.get)(id=user_id)
                    if hasattr(user, 'age') and user.age is not None:
                        return user.age  # Return the user's age
            except Exception as e:
                print(f"Error processing session {session.session_key}: {e}")
        return None  # No logged-in user found
    except Exception as e:
        print(f"Error retrieving user: {e}")
        return None


clients = set()
listOfHeartbeats = []
HeartbeatValues = [0]*1880
avgValues = []

# variabelen Thomas en Lotte
waarschuwingswaarden = 0
d = 10
sample_frequency = 94
max_bpm = 200  # niet aanpassen is altijd 200
sample_tijd1 = 1 / sample_frequency
sample_tijd = np.arange(0, d - sample_tijd1, sample_tijd1)
percentageoppervlakteBPM = 0.95
percentageoppervlakteWaarschuwing = 0.965
x_afstand = 60 / (sample_tijd1 * max_bpm)
seconden = 5  # om de hoeveel seconden willen we een nieuwe meting toevoegen
aantal_cycli = np.floor((len(HeartbeatValues) * sample_tijd1) / seconden) - 1
aantal_samples = seconden / sample_tijd1




def standarize_data(set):
    standaardafwijking = np.std(set)
    verwachtingswaarde = np.mean(set)
    gestandaardiseerde_data = []

    for i in range(len(set)):
        gestandaardiseerde_data.append((set[i] - verwachtingswaarde) / standaardafwijking)
    return gestandaardiseerde_data

def calculate_peakheight(set,oppBPM,print):


    h, bins = np.histogram(set, 30, density=True)
    bin_width = np.diff(bins)
    if print == True:
        plt.hist(set,30)

    for i in range(0, len(h)):
        opp = 0
        som = 0
        for j in range(0, i):
            opp += h[j] * np.mean(bin_width)
        if opp > oppBPM:
            x = i
            break

    peakheight = bins[x]
    return peakheight

def give_peaks(data,pkheight):


    # Pieken in het signaal vinden
    xwaarde, niks = find_peaks(data, pkheight)


    # werkelijkX zal de x waarden van de hartslagen bevatten na de forlus
    werkelijkX = [0] * len(xwaarde)

    tel = 0

    for i in range(len(xwaarde)):
        if tel == 0:
            werkelijkX[tel] = xwaarde[i]
            tel += 1
        elif tel != 0 and (xwaarde[i] - werkelijkX[tel - 1]) > x_afstand:
            werkelijkX[tel] = xwaarde[i]
            tel += 1

    aantalpieken = 0

    # aantal hartslagen
    for piek in werkelijkX:
        if piek > 0:
            aantalpieken += 1

    return werkelijkX, aantalpieken

def calculate_bpm(werkelijkX, aantalpieken):
    # gemiddelde hartslag in het interval berekenen
    gemiddeld = []
    for i in range(int(aantalpieken) - 1):
        gemiddeld.append(werkelijkX[i + 1] - werkelijkX[i])

    m = np.mean(gemiddeld)
    bpm = 60 / (m * sample_tijd1)
    return bpm

def waarschuwingswaarde(werkelijkX, aantalpieken):
    waarschuwing = 0
    gemiddeld = []
    for i in range(int(aantalpieken) - 1):
        gemiddeld.append(werkelijkX[i + 1] - werkelijkX[i])

    m = np.mean(gemiddeld)
    for i in range(int(aantalpieken) - 1):
        afstandwaarde = abs((werkelijkX[i + 1] - werkelijkX[i]))
        if afstandwaarde > 1.7 * m:
            # print(m)
            # print(afstandwaarde)
            waarschuwing += 1
    return waarschuwing


def FilterHeartbeat(waardenset):
    #HIER KOMT PROGRAMMA LOTTE EN THOMAS
    global waarschuwingswaarden

    # DC filteren
    remove_DC = waardenset - np.mean(waardenset)

    # Highpass and Lowpass filters
    b, a = butter(2, 7 / (sample_frequency / 2), btype='high')
    hoogfilter = sig.filtfilt(b, a, remove_DC)

    b1, a1 = butter(6, 20 / (sample_frequency / 2), btype='low', analog=False)
    laagfilter = sig.filtfilt(b1, a1, hoogfilter)

    # bpm
    standarized_data = standarize_data(laagfilter)
    peak_height = calculate_peakheight(standarized_data, percentageoppervlakteWaarschuwing, False)
    realX, numberOfPeaks = give_peaks(standarized_data, peak_height)
    bpm = calculate_bpm(realX, numberOfPeaks)
    waarschuwingswaarden += waarschuwingswaarde(realX, numberOfPeaks)

    return bpm

from twilio.rest import Client

def stuur_sms_naar_noodcontacten(noodcontacten, foutmelding):
    """
    Stuur een SMS-bericht naar noodcontacten wanneer ONTDEKTEFOUT wordt geactiveerd.

    Parameters:
    - noodcontacten: lijst van telefoonnummers van noodcontacten
    - foutmelding: bericht dat details over de fout bevat
    """
    # Twilio-configuratie
    #account_sid = "" # Vul je Twilio-account SID in
    #auth_token =  "" # Vul je Twilio-auth token in
    #twilio_nummer = "" # Je Twilio-telefoonnummer

    # Maak een Twilio-client
    client = Client(account_sid, auth_token)

    # Verstuur SMS naar alle noodcontacten
    for ontvanger in noodcontacten:
        try:
            bericht = client.messages.create(
                body=f"NOODALERT: {foutmelding}",
                from_=twilio_nummer,
                to=ontvanger
            )
            print(f"SMS succesvol verzonden naar {ontvanger}. SID: {bericht.sid}")

        except Exception as e:
            print(f"Fout bij het verzenden naar {ontvanger}: {e}")


# Simulatie van ONTDEKTEFOUT
def ONTDEKTEFOUT():
    # Noodcontacten en foutmelding definiëren
    noodcontacten = [
        "+32471347450"
    ]
    foutmelding = "My heart rate is dangerously high/low, please check on me or contact my doctor!"
    # SMS sturen naar noodcontacten
    stuur_sms_naar_noodcontacten(noodcontacten, foutmelding)


async def forward_to_clients(currentHeartRate, avgHeartRate):
    # Maak taken van de coroutines en wacht er expliciet op
    if clients:
        data = {
            'currentHeartRate': currentHeartRate,
            'avgHeartRate': avgHeartRate,
        }
        message = json.dumps(data)

        print(f"Verstuur naar {len(clients)} clients: {message}")
        await asyncio.wait([asyncio.create_task(client.send(message)) for client in clients])
        # ontvangen hartslag opslaan in database


async def handle_client(websocket, path):
    global clients
    global listOfHeartbeats
    global HeartbeatValues

    clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Ontvangen van Server A: {message}")

            messageList = []
            values = []

            for i in range(len(message)):
                if i == 0:
                    values = []
                if message[i:i + 4] == 'stop':
                    if HeartbeatValues[len(HeartbeatValues)-1] == 0:
                        if len(messageList[0]) >= 470:
                            HeartbeatValues = messageList[0][:470]*4
                        else:
                            HeartbeatValues[1880-(len(messageList[0])*4):] = messageList[0]*4
                    else:
                        if len(messageList[0]) >= 470:
                            for i in messageList[0][:470]:
                                HeartbeatValues.append(i)
                            del HeartbeatValues[:470]
                        else:
                            for i in messageList[0][:len(messageList[0])-1]:
                                HeartbeatValues.append(i)
                            del HeartbeatValues[:len(messageList[0])-1]
                    print("LECG: ", HeartbeatValues)
                    print(len(HeartbeatValues))
                    Heartbeat = FilterHeartbeat(HeartbeatValues)
                    avgValues.append(Heartbeat)
                    avgHeartbeat = round(sum(avgValues)/len(avgValues))
                    Heartbeat = round(Heartbeat)
                    break
                if message[i] == '[':
                   j = i
                if message[i] == ']':
                    var = message[j + 1:i].replace("'", "")
                    values_temp = var.split(',')
                    for i in values_temp:
                        values.append(int(i))
                    messageList.append(values)
                    print("messagelist",messageList)


            await forward_to_clients(Heartbeat, avgHeartbeat)
            age = await get_logged_in_user_age()
            if Heartbeat > round(206.9 - (0.67 * age)) or Heartbeat < 40:
                ONTDEKTEFOUT()


    finally:
        clients.remove(websocket)

# WebSocket server die communiceert met Server A op poort 8002
start_server = websockets.serve(handle_client, "0.0.0.0", 8003)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()