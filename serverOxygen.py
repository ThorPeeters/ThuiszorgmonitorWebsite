import asyncio
import websockets
import django
import os
import json
import random
from time import sleep
import numpy as np
import pandas as pd
from numpy.ma.core import less_equal
from scipy.signal import butter, filtfilt, find_peaks, welch, lfilter, kaiserord, firwin
import matplotlib.pyplot as plt

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ThuiszorgmonitorWeb.settings')
django.setup()

from Thuiszorgmonitor.models import Oxygen

clients = set()
listOfSaturationValues = []
listOfInfraRood = [0]*1880
listOfRood = [0]*1880

def FilterSaturation(infra_red, red):
    print("infra_red doorgekregen: ", infra_red)
    print(len(infra_red))
    print("red doorgekregen: ", red)
    print(len(red))


    sample_frequency = 94
    # lowpass
    cutoff_frequency = 45
    b, a = butter(4, cutoff_frequency, btype='low', fs=sample_frequency)
    red_lowpass_filtered = filtfilt(b, a, red)
    infra_red_lowpass_filtered = filtfilt(b, a, infra_red)

    # Minus DC-component
    red_DC = np.mean(red_lowpass_filtered)
    infra_red_DC = np.mean(infra_red_lowpass_filtered)
    red_AC = red_lowpass_filtered - red_DC
    infra_red_AC = infra_red_lowpass_filtered - infra_red_DC

    # Highpass
    cutoff_freq = 0.25
    numtaps = 577
    taps = firwin(numtaps, cutoff_freq, pass_zero='highpass', fs=sample_frequency, window='hamming')

    red_AC_filtered = lfilter(taps, 1.0, red_AC)
    infra_red_AC_filtered = lfilter(taps, 1.0, infra_red_AC)

    # Realtime calculation
    interval_short = 5 * sample_frequency
    interval_difference = len(red_AC_filtered) - interval_short
    minpeak = 0.6 * sample_frequency

    peaks_red, _ = find_peaks(red_AC_filtered[interval_difference:], distance=minpeak)
    red_AC_filtered = np.array(red_AC_filtered)
    AC_red = np.mean(red_AC_filtered[peaks_red + interval_difference])
    R_red = AC_red / red_DC

    peaks_infra_red, _ = find_peaks(infra_red_AC_filtered[interval_difference:], distance=minpeak)
    infra_red_AC_filtered = np.array(infra_red_AC_filtered)
    AC_infra_red = np.mean(infra_red_AC_filtered[peaks_infra_red + interval_difference])
    R_infra_red = AC_infra_red / infra_red_DC

    R = R_red / R_infra_red
    SpO2 = round(98.52 - 1.0504 * R, 4)

    if infra_red[len(infra_red)-1] > 500 or red[len(red)-1] > 500:
        SpO2 = 0

    return  SpO2


from twilio.rest import Client

def stuur_sms_naar_noodcontacten(noodcontacten, foutmelding):
    """
    Stuur een SMS-bericht naar noodcontacten wanneer ONTDEKTEFOUT wordt geactiveerd.

    Parameters:
    - noodcontacten: lijst van telefoonnummers van noodcontacten
    - foutmelding: bericht dat details over de fout bevat
    """
    # Twilio-configuratie
    #account_sid = ""  # Vul je Twilio-account SID in
    #auth_token = ""  # Vul je Twilio-auth token in
    #twilio_nummer = ""  # Je Twilio-telefoonnummer

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
    foutmelding = "My oxygen saturation level is dangerously low, please check on me or contact my doctor!"
    # SMS sturen naar noodcontacten
    stuur_sms_naar_noodcontacten(noodcontacten, foutmelding)


async def forward_to_clients(saturationValue):
    # Maak taken van de coroutines en wacht er expliciet op
    if clients:
        data = {
            'saturationValue': saturationValue,
        }
        message = json.dumps(data)
        print(f"Verstuur naar {len(clients)} clients: {message}")
        await asyncio.wait([asyncio.create_task(client.send(message)) for client in clients])



async def handle_client(websocket, path):
    global clients
    global listOfSaturationValues
    global listOfInfraRood
    global listOfRood

    clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Ontvangen van Server A: {message}")

            messageList = []
            values = []

            for i in range(len(message)):
                if i == 1:
                    values = []
                if message[i:i + 4] == 'stop':
                    # message = [Infra, rood]
                    messageList[1] = messageList[0][470:]
                    messageList[0] = messageList[0][:470]
                    """if listOfInfraRood[len(listOfInfraRood)-1] == 0:
                        if len(messageList[0]) >= 470:
                            listOfInfraRood = messageList[0][:470]*4
                        else:
                            listOfInfraRood[1880-(len(messageList[0])*4):] = messageList[0]*4
                    else:
                        if len(messageList[0]) >= 470:
                            for i in messageList[0][:470]:
                                listOfInfraRood.append(i)
                            del listOfInfraRood[:470]
                        else:
                            for i in messageList[0][:len(messageList[0])]:
                                listOfInfraRood.append(i)
                            del listOfInfraRood[:len(messageList[0])]


                    if listOfRood[len(listOfRood)-1] == 0:
                        if len(messageList[1]) >= 470:
                            listOfRood = messageList[1][:470]*4
                        else:
                            listOfRood[1880-(len(messageList[1])*4):] = messageList[1]*4
                    else:
                        if len(messageList[1]) >= 470:
                            for i in messageList[1][:470]:
                                listOfRood.append(i)
                            del listOfRood[:470]
                        else:
                            for i in messageList[1][:len(messageList[1])]:
                                listOfRood.append(i)
                            del listOfRood[:len(messageList[1])]

                    print("LInfraRood: ", listOfInfraRood)
                    print(len(listOfInfraRood))
                    print("LRood: ", listOfRood)
                    print(len(listOfRood))"""

                    if listOfRood[len(listOfRood)-1] == 0:
                        listOfRood = messageList[1]*7
                        listOfRood = listOfRood[:1880]
                    else:
                        for i in messageList[1]:
                            listOfRood.append(i)
                        del listOfRood[:len(messageList[1])]

                    if listOfInfraRood[len(listOfInfraRood)-1] == 0:
                        listOfInfraRood = messageList[0]*7
                        listOfInfraRood = listOfInfraRood[:1880]
                    else:
                        for i in messageList[0]:
                            listOfInfraRood.append(i)
                        del listOfInfraRood[:len(messageList[0])]

                    Saturationvalue = FilterSaturation(listOfInfraRood, listOfRood)
                    break
                if message[i] == '[':
                    j = i
                if message[i] == ']':
                    var = message[j + 1:i].replace("'", "")
                    values_temp = var.split(',')
                    for i in values_temp:
                        values.append(int(i))
                        print(values)
                    messageList.append(values)
            print("MESSAGELIST: ", messageList)
            print("MESSAGELIST0: ", messageList[0])
            print("MESSAGELIST1: ", messageList[1])
            print(len(messageList[0]), len(messageList[1]))
            await forward_to_clients(Saturationvalue)
            print("Dit is de Saturationvalue: ", Saturationvalue)
            """if Saturationvalue <=90:
                sleep(15)
                ONTDEKTEFOUT()"""

    finally:
        clients.remove(websocket)


# WebSocket server die communiceert met Server A op poort 8002
start_server = websockets.serve(handle_client, "0.0.0.0", 8004)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

