# server_a.py - Ontvangt hartslagdata van een externe bron
import asyncio
import websockets

#from Thuiszorgmonitor.models import Heartbeat

async def receive_heartbeat(websocket, path):
    sensor = ''
    coordinate = ''

    xacoordinates = []
    yacoordinates = []
    zacoordinates = []

    xgcoordinates = []
    ygcoordinates = []
    zgcoordinates = []

    InfraRoodvalues = []
    Roodvalues = []
    ECGval = []

    async for message in websocket:
        print(message)
        if message != 'stop':
            print(f"Ontvangen data: {message}")
            if message == ' ' or message == '':
                break
            if message == 'ACCEL_DATA' or message == 'GYRO_DATA' or message == 'InfraRood' or message == 'Rood' or message == 'ECG_DATA':
                sensor = message
                coordinate = ''
            if message == 'X' or message == 'Y' or message == 'Z':
                coordinate = message

            if sensor == 'ACCEL_DATA':
                if coordinate == 'X':
                    if message != 'X':
                        values = message.split(',')
                        for i in values:
                            if i == '' or i == ' ':
                                values.remove(i)
                        xacoordinates.extend(values)
                if coordinate == 'Y':
                    if message != 'Y':
                        values = message.split(',')
                        for i in values:
                            if i == '' or i == ' ':
                                values.remove(i)
                        yacoordinates.extend(values)
                if coordinate == 'Z':
                    if message != 'Z':
                        values = message.split(',')
                        for i in values:
                            if i == '' or i == ' ':
                                values.remove(i)
                        zacoordinates.extend(values)

            if sensor == 'GYRO_DATA':
                if coordinate == 'X':
                    if message != 'X':
                        values = message.split(',')
                        for i in values:
                            if i == '' or i == ' ':
                                values.remove(i)
                        xgcoordinates.extend(values)
                if coordinate == 'Y':
                    if message != 'Y':
                        values = message.split(',')
                        for i in values:
                            if i == '' or i == ' ':
                                values.remove(i)
                        ygcoordinates.extend(values)
                if coordinate == 'Z':
                    if message != 'Z':
                        values = message.split(',')
                        for i in values:
                            if i == '' or i == ' ':
                                values.remove(i)
                        zgcoordinates.extend(values)

            if sensor == 'InfraRood':
                if message != 'InfraRood':
                    values = message.split(',')
                    for i in values:
                        if i == '' or i == ' ':
                            values.remove(i)
                    InfraRoodvalues.extend(values)

            if sensor == 'Rood':
                if message != 'Rood':
                    values = message.split(',')
                    for i in values:
                        if i == '' or i == ' ':
                            values.remove(i)
                    Roodvalues.extend(values)

            if sensor == 'ECG_DATA':
                if message != 'ECG_DATA':
                    values = message.split(',')
                    for i in values:
                        if i == '' or i == ' ':
                            values.remove(i)
                    ECGval.extend(values)

        if message == 'stop':
            coordinates = [xacoordinates, yacoordinates, zgcoordinates, xgcoordinates, ygcoordinates, zgcoordinates, 'stop']
            PPGvalues = [InfraRoodvalues, Roodvalues, 'stop']
            ECGvalues = [ECGval, 'stop']
            if coordinates[0]:
                async with websockets.connect('ws://localhost:8002') as serverFalldetection:
                    await serverFalldetection.send(str(coordinates))
            if ECGvalues[0]:
                async with websockets.connect('ws://localhost:8003') as serverHeartbeat:
                    await serverHeartbeat.send(str(ECGvalues))
            if PPGvalues[0]:
                async with websockets.connect('ws://localhost:8004') as serverOxygen:
                  await serverOxygen.send(str(PPGvalues))
            print(f"Data verzonden naar Server Falldetection: {coordinates}")
            print(f"Data verzonden naar Server Heartbeat: {ECGvalues}")
            print(f"Data verzonden naar Server Oxygen: {PPGvalues}")
            xacoordinates = []
            yacoordinates = []
            zacoordinates = []

            xgcoordinates = []
            ygcoordinates = []
            zgcoordinates = []

            InfraRoodvalues = []
            Roodvalues = []
            ECGval = []
# Start WebSocket server om te luisteren naar de hartslaggegevens van de externe bron
start_server = websockets.serve(receive_heartbeat, "0.0.0.0", 8001, ping_interval=4000, ping_timeout=8000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()