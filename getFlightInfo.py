import requests
import datetime
import re

def getIcao(flightNumber):
    alphanumeric_flightNumber = ''.join(e for e in flightNumber if e.isalnum())
    response = requests.get(f"https://www.flightradar24.com/v1/search/web/find?query={alphanumeric_flightNumber}&limit=1")
    if response.status_code == 200:
        responseJson = response.json()
        callsign = responseJson['results'][0]['detail'].get('callsign', 'Unknown')
        return callsign
    else:
        print("Error fetching callsign data")
        return None

def getFlightDate():
    flightDate = input("Enter the date you wish to fly (YYYY-MM-DD) (Press Enter for today's date): ")
    if not flightDate:
        flightDate = datetime.date.today().strftime("%Y-%m-%d")
    else:
        # Validate the input date format
        try:
            datetime.datetime.strptime(flightDate, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
            return getFlightDate()
    return flightDate

def getFlightDay(date):
    return datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%A")[:2].lower()

def getAirportId(airportName):
    response = requests.get("https://www.flightconnections.com/autocomplete_location.php?lang=en&term=" + airportName)
    if response.status_code == 200:
        responseJson = response.json()
    airports = responseJson['airports']
    if len(airports) == 1:
        print(f"Only one airport found for {airportName}: {airports[0]['airport']}")
        return airports[0]['id'], airports[0]['airport']
    elif len(airports) == 0:
        print(f"No airports found for {airportName}")
        return 0, None
    elif len(airports) > 1:
        print(f"Multiple airports found for {airportName}:")
        for index, airport in enumerate(airports, start=1):
            print(f"{index}. {airport['airport']}")
    while True:
        selected_number = input("Enter the number corresponding to the desired airport (Enter for 1, r to reenter): ")
        if selected_number == "" or selected_number.isdigit():
            break
        elif selected_number == "r" or selected_number == "R":
            return 0
        else:
            print("Please enter a valid number.")
    selected_airport_id = airports[int(selected_number) - 1]['id'] if selected_number else airports[0]['id']

    return selected_airport_id, airports[int(selected_number) - 1]['airport'] if selected_number else airports[0]['airport']

def getRouteIds(startingAirportId, destinationAirportId):
    response = requests.get(f"https://www.flightconnections.com/ro{startingAirportId}_{destinationAirportId}.json")

    if response.status_code == 200:
        responseJson = response.json()
        routeNumbers = [item['route'][0] for item in responseJson['data']]
    else:
        print("Error fetching routes data")
        routeNumbers = []
    return routeNumbers

def getFlightInfo(startingAirportId, destinationAirportId, routeId, flightDate, aircraftType):
    flightDay = getFlightDay(flightDate)
    payload = {'dep': startingAirportId, 'des': destinationAirportId, 'id': routeId, 'startDate': flightDate, 'endDate': flightDate}
    response = requests.post("https://www.flightconnections.com/validity.php", data=payload)
    if response.status_code == 200:
        flight_info = response.json()
        if 'flights' in flight_info:
            for flight in flight_info['flights']:
                if aircraftType and aircraftType.lower() not in flight['aircraft'].lower():
                    continue
                if flight[flightDay] == '1':
                    print(flight_info['airline'] + ":")
                    break
        if 'flights' in flight_info:
            previous_flight = {'deptime': '', 'flightnumber': ''}
            for flight in flight_info['flights']:
                if flight[flightDay] == '1':
                    if aircraftType and aircraftType.lower() not in flight['aircraft'].lower():
                        continue
                    if flight['flightnumber'] != previous_flight['flightnumber'] or flight['deptime'] != previous_flight['deptime']:
                        flight_number = ''.join(e for e in flight['flightnumber'] if e.isalnum())
                        print(f"   {flight_number} / {getIcao(flight_number)}:")
                        print(f"      {flight['aircraft']}")
                        print(f"      Departure time (Local): {flight['deptime']}")
                    previous_flight = flight
    else:
        print("Error fetching flight info")
        return False
    return True

flightDate = getFlightDate()

while True:
    startingAirportId = 0
    airportName = input("Enter starting airport name: ")
    startingAirport = getAirportId(airportName)
    if startingAirport:
        startingAirportId = startingAirport[0]
        startingAirportName = startingAirport[1]
    while startingAirportId == 0:
        print("Please reenter the starting airport.")
        airportName = input("Enter starting airport name: ")
        startingAirport = getAirportId(airportName)
        startingAirportId = startingAirport[0]
        startingAirportName = startingAirport[1]

    destinationAirportId = 0
    airportName = input("Enter destination airport name: ")
    destinationAirport = getAirportId(airportName)
    if destinationAirport:
        destinationAirportId = destinationAirport[0]
        destinationAirportName = destinationAirport[1]
    while destinationAirportId == 0:
        print("Please reenter the destination airport.")
        airportName = input("Enter destination airport name: ")
        destinationAirport = getAirportId(airportName)
        destinationAirportId = destinationAirport[0]
        destinationAirportName = destinationAirport[1]
   
    aircraftType = input("Enter aircraft type (leave blank for no filter): ")
    if re.match(r'^[bB]7[1-9][1-9]$', aircraftType):
        aircraftType = f"7{aircraftType[2]}7-{aircraftType[3:]}00"
    print()

    routeIds = getRouteIds(startingAirportId, destinationAirportId)

    print(f"Flights from {startingAirportName} to {destinationAirportName} on {flightDate}:")

    flightsFound = False
    for routeId in routeIds:
        if getFlightInfo(startingAirportId, destinationAirportId, routeId, flightDate, aircraftType):
            flightsFound = True

    if not flightsFound:
        print("No direct flights were found.")

    print()
    input("Press Enter to search for other flights...")
