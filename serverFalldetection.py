# serverfalldetection.py - Stuurt ontvangen valdetectiedata door naar de webpagina
import asyncio
import websockets
import django
import os
import json
from time import sleep
import math

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ThuiszorgmonitorWeb.settings')
django.setup()

from Thuiszorgmonitor.models import FallDetection

clients = set()
listOfxa = []
listOfya = []
listOfza = []
listOfxg = []
listOfyg = []
listOfzg = []


def HasFallen(accelX, accelY, accelZ, gyrX, gyrY, gyrZ):
    #HIER KOMT PROGRAMMA FALLDETECTION

    fallMaxTreshold = 3  # dit moet voor de echte data op 3 staan, maar de vbdata werkte met g
    fallMinTreshold = 1.2  # dit moet voor de echte data op 1.2 staan, maar de vbdata werkte met g
    fallTimeAcc = 0
    fallTimeOr = 0
    maxFalltime = 10
    minFalltime = 2
    alarm = False

    minAngleChange = 250  # dit moet voor de echte data op 250 staan, maar de vbdata werkte met graden
    maxtimebetweenFallAndRot = 2
    TimerbetweenAccandOR = 0
    TimerbetweenOrandAcc = 0
    alarmOr = False
    alarmAcc = False

    fallDetectionAcc = False
    fallDetectionOr = False

    for i in range(len(accelX)):

        aX = (accelX[i])
        aY = (accelY[i])
        aZ = (accelZ[i])

        gX = (gyrX[i])
        gY = (gyrY[i])
        gZ = (gyrZ[i])
        # magnitude_acceleration = magnitude_acceleration_data[i]
        # magnitude_gyroscope = magnitude_gyroscope_data[i]

        magnitude_acceleration = math.sqrt(aX ** 2 + aY ** 2 + aZ ** 2)
        magnitude_gyroscope = math.sqrt(gX ** 2 + gY ** 2 + gZ ** 2)
        if magnitude_acceleration >= fallMaxTreshold:
            fallDetectionAcc = True
            if fallTimeAcc == 0:
                TimerbetweenAccandOR = 0

            fallTimeAcc += 1
            if fallDetectionOr == False:
                TimerbetweenAccandOR += 1
        else:
            if fallTimeAcc <= maxFalltime and fallTimeAcc >= 1:
                alarmAcc = True
            fallDetectionAcc = False
            fallTimeAcc = 0

        if magnitude_gyroscope >= minAngleChange:
            fallDetectionOr = True
            if fallTimeOr == 0:
                TimerbetweenOrandAcc = 0
            fallTimeOr += 1
            if fallTimeAcc == False:
                TimerbetweenOrandAcc += 1
        else:
            if fallTimeOr <= maxFalltime and fallTimeOr >= 1:
                alarmOr = True
            fallDetectionOr = False
            fallTimeOr = 0
        if alarmAcc == True and alarmOr == True and TimerbetweenOrandAcc < maxtimebetweenFallAndRot and TimerbetweenAccandOR < maxtimebetweenFallAndRot:
            print("na", i * 0.1, "seconden gevallen")
            alarm = True
            alarmOr = False
            alarmAcc = False
    return alarm


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
    foutmelding = "Ik ben gevallen om 00:00, contacteer de hulpdiensten!"

    # SMS sturen naar noodcontacten
    stuur_sms_naar_noodcontacten(noodcontacten, foutmelding)


async def forward_to_clients(boolean_has_fallen):
    if clients:
        data = {
            'boolean_has_fallen': boolean_has_fallen,
        }
        message = json.dumps(data)

        print(f"Verstuur naar {len(clients)} clients: {message}")
        await asyncio.wait([asyncio.create_task(client.send(message)) for client in clients])


async def handle_client(websocket, path):
    global clients
    clients.add(websocket)
    try:
        async for message in websocket:
            messageList = []
            for i in range(len(message)):
                if message[i:i + 4] == 'stop':
                    # message = [xa,ya,za,gx,gy,gz]
                    listOfxa = messageList[0]
                    listOfya = messageList[1]
                    listOfza = messageList[2]
                    listOfxg = messageList[3]
                    listOfyg = messageList[4]
                    listOfzg = messageList[5]
                    print("Lxa: ", listOfxa)
                    print("Lya: ", listOfya)
                    print("Lza: ", listOfza)
                    print("Lxg: ", listOfxg)
                    print("Lyg: ", listOfyg)
                    print("Lzg: ", listOfzg)
                    for i in range(len(listOfxa)):
                        listOfxa[i] = float(listOfxa[i])
                        listOfya[i] = float(listOfya[i])
                        listOfza[i] = float(listOfza[i])
                        listOfxg[i] = float(listOfxg[i])
                        listOfyg[i] = float(listOfyg[i])
                        listOfzg[i] = float(listOfzg[i])

                    boolean_has_fallen = HasFallen(listOfxa, listOfya, listOfza, listOfxg, listOfyg, listOfzg)
                    break
                if message[i] == '[':
                    j = i
                if message[i] == ']':
                    var = message[j + 1:i].replace("'", "")
                    values = var.split(',')
                    for i in range(len(values)):
                        values[i] = values[i].replace(' ', '')
                    messageList.append(values)

            print(f"Verzonden naar web page: {boolean_has_fallen}")
            await forward_to_clients(boolean_has_fallen)
            if boolean_has_fallen == True:
                ONTDEKTEFOUT()

    finally:
        clients.remove(websocket)

# WebSocket server die communiceert met Server A op poort 8002
start_server = websockets.serve(handle_client, "0.0.0.0", 8002)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()