import requests
import osmnx as ox
from geopy.geocoders import Nominatim
from geopy.geocoders import Nominatim, GoogleV3, Photon
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import openrouteservice
from openrouteservice import exceptions
import os
from dotenv import load_dotenv
import json
import folium


load_dotenv()

def get_roads(city_name):
    """
    Fetches all road names in Deinze using the Overpass API.
    Returns:
        list: A list of unique road names in Deinze.
    """
    # Overpass API query to get all roads in Deinze
    query = f"""
    [out:json];
    area[name="{city_name}"]->.searchArea;
    way[highway](area.searchArea);
    out body;
    >;
    out skel qt;
    """

    url = "http://overpass-api.de/api/interpreter"
    response = requests.get(url, params={'data': query})
    data = response.json()
    # Extract road names
    road_names = set()
    for element in data["elements"]:
        if element["type"] == "way" and "tags" in element and "name" in element["tags"]:
            road_names.add(element["tags"]["name"])

    return sorted(road_names)


def get_city_name(city_name):
    # Overpass API query to get all villages, towns, and suburbs in Deinze

    query = f"""
    [out:json];
    area[name="{city_name}"]->.searchArea;
    (
      node[place=village](area.searchArea);
      node[place=town](area.searchArea);
      node[place=suburb](area.searchArea);
    );
    out body;
    """

    # Request Overpass API
    url = "http://overpass-api.de/api/interpreter"
    response = requests.get(url, params={'data': query})
    data = response.json()

    # Extract location names
    locations = set()
    for element in data["elements"]:
        if "tags" in element and "name" in element["tags"]:
            locations.add(element["tags"]["name"])

    # Print results
    # print("\n".join(sorted(locations)))
    return locations


def find_city_pass_through():
    # Start and finish locations (Example: Deinze to Nokere, Belgium)
    start = (50.9812, 3.5250)  # Deinze
    finish = (50.8354, 3.5126)  # Nokere

    # OSRM Routing API (Driving route)
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{finish[1]},{finish[0]}?overview=full&geometries=geojson"

    # Request route from OSRM
    osrm_response = requests.get(osrm_url).json()
    coordinates = osrm_response["routes"][0]["geometry"]["coordinates"]

    # Get city names from route waypoints
    city_names = set()
    nominatim_url = "https://nominatim.openstreetmap.org/reverse"
    headers = {"User-Agent": "your-app-name"}

    for lon, lat in coordinates[::10]:  # Sample every 10th point to reduce API calls
        params = {"lat": lat, "lon": lon, "format": "json"}
        nominatim_response = requests.get(nominatim_url, params=params, headers=headers).json()

        # Extract city, town, or village name
        city = nominatim_response.get("address", {}).get("city") or \
               nominatim_response.get("address", {}).get("town") or \
               nominatim_response.get("address", {}).get("village")

        if city:
            city_names.add(city)

    # Print unique cities along the route
    print("\n".join(sorted(city_names)))


def get_lat_lon(city_name, country=None):
    # Nominatim Forward Geocoding API with optional country filter
    if country:
        query = f"{city_name}, {country}"
    else:
        query = city_name

    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"

    # Send the request
    response = requests.get(url, headers={'User-Agent': 'your-app-name'})
    data = response.json()

    # Extract latitude and longitude from the response
    if data:
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        return float(lat), float(lon)
    else:
        return None, None


def get_location_details(address):
    geolocator = Nominatim(user_agent="location_finder")

    # Add a delay to respect usage limits
    time.sleep(1)

    try:
        # Get location
        location = geolocator.geocode(address, addressdetails=True)

        if location:
            # Extract components from the raw response
            address_components = location.raw.get('address', {})

            # Extract different administrative levels
            city = address_components.get('city')
            town = address_components.get('town')
            village = address_components.get('village')
            suburb = address_components.get('suburb')
            neighborhood = address_components.get('neighbourhood')  # Note the British spelling
            county = address_components.get('county')
            state = address_components.get('state')
            country = address_components.get('country')

            print(f"Full address: {location.address}")
            print(f"Coordinates: {location.latitude}, {location.longitude}")

            # Print available components
            for component_type, value in {
                'City': city,
                'Town': town,
                'Village': village,
                'Suburb': suburb,
                'Neighborhood': neighborhood,
                'County': county,
                'State': state,
                'Country': country
            }.items():
                if value:
                    print(f"{component_type}: {value}")

            return location.raw
        else:
            print("Location not found")
            return None

    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Error: {e}")
        return None


# Example usage
def geocode_location(client, address):
    """Geocode an address to coordinates using OpenRouteService."""
    try:
        geocode_result = client.pelias_search(text=address, size=1)
        if geocode_result and 'features' in geocode_result and len(geocode_result['features']) > 0:
            coordinates = geocode_result['features'][0]['geometry']['coordinates']
            return coordinates
        else:
            print(f"Warning: Could not geocode address: {address}")
            return None
    except exceptions.ApiError as e:
        print(f"Geocoding API Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during geocoding: {e}")
        return None

def get_route_with_towns(origin, destination, profile='cycling-road'):
    """Fetch route details including street names and towns."""
    api_key = os.getenv("OPENROUTESERVICE_API_KEY")
    client = openrouteservice.Client(key=api_key)

    # Geocode origin and destination
    origin_coords = geocode_location(client, origin)
    destination_coords = geocode_location(client, destination)
    another = geocode_location(client, origin)
    print(origin_coords, destination_coords, another)
    # Check if geocoding was successful
    if not origin_coords or not destination_coords:
        print("Error: Failed to geocode origin or destination.")
        return None



    try:
        # Request route details
        route_request = {
            'coordinates': [origin_coords, destination_coords, another],
            'profile': profile,
            'instructions': True,
            # "geometry":'true',
            "format_out":"geojson",
            # 'instruction_format': 'text'
        }



        directions = client.directions(**route_request)

        # plot the route on a map
        route = directions['features'][0]['geometry']['coordinates']
        m = folium.Map(location=[origin_coords[1], origin_coords[0]], zoom_start=12)
        folium.PolyLine(locations=[(lat, lon) for lon, lat in route], color='blue').add_to(m)
        folium.Marker(location=[origin_coords[1], origin_coords[0]], popup=origin).add_to(m)
        folium.Marker(location=[destination_coords[1], destination_coords[0]], popup=destination).add_to(m)
        folium.Marker(location=[another[1], another[0]], popup="Oudenaarde").add_to(m)
        m.save("map.html")

        if not directions or "features" not in directions or not directions['features']:
            print(f"No route found between '{origin}' and '{destination}'.")
            return None

        route = directions["features"][0]['properties']
        steps = route['segments'][0]['steps']

        # Extract street names and towns
        route_details = []
        for step in steps:
            street_name = step.get('name', 'Unnamed road')
            instruction = step['instruction']
            route_details.append(f"{instruction} on {street_name}")

        return route_details

    except exceptions.ApiError as e:
        print(f"Routing API Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during routing: {e}")
        return None

def get_road_names(city_name):
    """
    Retrieves a list of road names within a specified city using OSMnx.

    Args:
        city_name (str): The name of the city.

    Returns:
        set: A set of unique road names in the city. Returns an empty set if
             no road names are found or the city is not recognized.
    """
    try:
        # Download the street network for the city
        G = ox.graph_from_place(city_name, network_type="drive")

        # Extract edge attributes, which contain road names
        edges = ox.convert.graph_to_gdfs(G, nodes=False, edges=True)

        # Get the 'name' column, which contains road names
        road_names = edges['name']

        # Handle cases where 'name' might be a single string or a list
        unique_road_names = set()
        for name in road_names:
            if isinstance(name, str):
                unique_road_names.add(name)
            elif isinstance(name, list):
                unique_road_names.update(name)

        return list(unique_road_names)

    except Exception as e:
        print(f"An error occurred: {e}")
        return list()

def event_danilith_nokere_koerse():
    event = {
        "Danilith Nokere Koerse Cities": [
            "Deinze, Belgium",
            "Nokere, Belgium",
            "Oudenaarde, Belgium",
            "Anzegem, Belgium",
            "Wortegem-Petegem, Belgium",
            "Nazareth, Belgium",
            "Gavere, Belgium",
            "Zwalm, Belgium",
            "Zottegem, Belgium",
            "Horebeke, Belgium",
            "Maarkedal, Belgium",
            "Kruisem, Belgium",
            "Machelen, Belgium"
        ]
    }
    location = []
    location_road_name = {}
    for city in event["Danilith Nokere Koerse Cities"]:
        print(city)
        # location.extend(get_city_name(city))
        location_road_name[city] =  get_road_names(city_name=city)
    # print(location)
    # for town in location:
    #     road = get_road_names(city_name=town)
    #     print(road)
    #     location_road_name[town] = road
    print(location_road_name)
    with open("location_road_name.json", "w") as f:
        json.dump(location_road_name, f)
    return

if __name__ == '__main__':
    # event_danilith_nokere_koerse()
    # start_town = "Lille, France"
    # end_town = "Mantes-la-Jolie, France"
    start_town = "Deinze Markt, Belgium"
    end_town = "Nokere, Waregemsestraat, Belgium"
    route_details = get_route_with_towns(start_town, end_town)
    if route_details:
        print("\nRoute Details:")
        # for detail in route_details:
        #     print(detail.split("on")[-1].strip())

        for detail in route_details:
            print(detail)
