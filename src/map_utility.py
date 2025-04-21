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
from typing import Dict, List, Optional
import argparse
import osmnx as ox

load_dotenv()


class MapUtility:
    def __init__(self):
        self.locations = []
        self.__api_key = ""

        self.geolocator = Nominatim(user_agent="geoapiExercises")
        self.__initial_key()
        self.cclient = openrouteservice.Client(key=self.__api_key)
        self._visualize = False

    def set_location(self, locations: List[str]):
        """Set the location for geocoding."""
        self.locations = locations

    @property
    def visualize(self):
        """Get the current visualization setting."""
        return self._visualize

    @visualize.setter
    def visualize(self, visualize: bool):
        """Set whether to visualize the route on a map."""
        self._visualize = visualize


    def __initial_key(self):
        if not os.getenv("OPENROUTESERVICE_API_KEY"):
            raise ValueError("API key not found. Please set the OPENROUTESERVICE_API_KEY environment variable.")
        self.__api_key = os.getenv("OPENROUTESERVICE_API_KEY")


    @staticmethod
    def geocode_location(client, address: str) -> Optional[List[float]]:
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

    def get_route_with_towns(self, profile='cycling-road'):
        """Fetch route details including street names and towns."""
        api_key = os.getenv("OPENROUTESERVICE_API_KEY")
        client = openrouteservice.Client(key=api_key)
        locations = self.locations
        # Geocode origin and destination
        coordinates = []
        for loc in locations:
            coord = self.geocode_location(client, loc)
            if coord:
                coordinates.append(coord)
            else:
                print(f"Error: Could not geocode location: {loc}")
                return None


        try:
            # Request route details
            route_request = {
                'coordinates': coordinates,
                'profile': profile,
                'instructions': True,
                # "geometry":'true',
                "format_out": "geojson",
                # 'instruction_format': 'text'
            }

            directions = client.directions(**route_request)

            # plot the route on a map
            if self.visualize:
                self.visualize_map(directions, locations, coordinates)

            if not directions or "features" not in directions or not directions['features']:
                # print(f"No route found between '{origin}' and '{destination}'.")
                return None

            route = directions["features"][0]['properties']
            return route

        except exceptions.ApiError as e:
            print(f"Routing API Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error during routing: {e}")
            return None

    def route_segments(self, route):
        """Extract properties from the route."""
        properties = route['features'][0]['properties']
        return {
            'distance': properties['segments'][0]['distance'],
            'duration': properties['segments'][0]['duration'],
            'steps': properties['segments'][0]['steps']
        }

    def route_detail(self, route):
        route_details = []
        for segment in route['segments']:
            for step in segment['steps']:
                street_name = step.get('name', 'Unnamed road')
                instruction = step['instruction']
                route_details.append(f"{instruction} on {street_name}")
        return route_details

    def route_name(self):
        """Get the name of the route."""
        street_name = []
        routes = self.get_route_with_towns()
        for segment in routes['segments']:
            for step in segment['steps']:
                street_name.append(step.get('name', 'Unnamed road'))
        street_name = [route for route in (set(street_name))]
        return street_name

    @staticmethod
    def visualize_map(directions, locations, coordinates):
        route = directions['features'][0]['geometry']['coordinates']
        m = folium.Map(location=[coordinates[0][1], coordinates[0][0]], zoom_start=12)
        # color marker
        for i, loc in enumerate(locations):
            if i == 0:
                folium.Marker(location=[coordinates[i][1], coordinates[i][0]], popup=loc,
                              icon=folium.Icon(color='green')).add_to(m)
            elif i == len(locations) - 1:
                folium.Marker(location=[coordinates[i][1], coordinates[i][0]], popup=loc,
                              icon=folium.Icon(color='red')).add_to(m)
            else:
                folium.Marker(location=[coordinates[i][1], coordinates[i][0]], popup=loc).add_to(m)
        folium.PolyLine(locations=[(lat, lon) for lon, lat in route], color='blue').add_to(m)
        m.save("map.html")


    def get_route_city(self) -> Dict[str, list[str]]:
        locate_route = {}
        for loc in self.locations:
            locate_route[loc] = self.get_road_names(loc)
        return locate_route

    @staticmethod
    def get_road_names(city_name: str) -> list[str]:
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


def parser_setter():
    parser = argparse.ArgumentParser(description="Map Utility")
    parser.add_argument("-l", "--locations", type=str, nargs='+', required=True, help="List of locations to route through")
    parser.add_argument("--visualize", action='store_true', help="Visualize the route on a map")
    return parser.parse_args()

def main():
    par = parser_setter()
    print(par)
    map_util = MapUtility()
    map_util.set_location(par.locations)
    map_util.visualize = par.visualize
    route_details = map_util.route_name()
    # route_city = map_util.get_route_city()
    # with open("route.json", "w") as f:
    #     json.dump(route_city, f, indent=4)
    for route in route_details:
        print(route)


if __name__ == '__main__':
    main()
    # map_util = MapUtility()
    # print(map_util.get_route_city())