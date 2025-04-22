import argparse
import math
import os
from itertools import pairwise
from typing import Dict, List, Optional

import folium
import networkx as nx
import openrouteservice
import osmnx as ox
import requests
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from openrouteservice import exceptions
import json

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

    def get_multi_waypoint_route(self, waypoints, max_routes_per_segment=3):
        """
        Route through multiple waypoints in order using Overpass API and NetworkX

        Args:
            waypoints: List of (lat, lon) tuples representing points to visit in order
            max_routes_per_segment: Max number of alternative routes per segment

        Returns:
            A folium map with the complete route including alternatives
        """
        if len(waypoints) < 2:
            return "Need at least two waypoints"

        # Create a map centered on the average of all waypoints
        center_lat = sum(wp[0] for wp in waypoints) / len(waypoints)
        center_lon = sum(wp[1] for wp in waypoints) / len(waypoints)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

        # Add markers for all waypoints
        colors = ['green', 'cadetblue', 'orange', 'purple', 'darkpurple', 'red']
        for i, point in enumerate(waypoints):
            if i == 0:
                marker_text = "Start"
                color = "green"
            elif i == len(waypoints) - 1:
                marker_text = "End"
                color = "red"
            else:
                marker_text = f"Waypoint {i}"
                color = "cadetblue" or colors[min(i, len(colors) - 1)]

            folium.Marker(
                point,
                popup=marker_text,
                icon=folium.Icon(color=color)
            ).add_to(m)

        # Process each segment between consecutive waypoints
        total_distance = 0
        all_segments = []
        all_road = []

        # Get pairs of waypoints (start->wp1, wp1->wp2, etc.)
        for i, (start_point, end_point) in enumerate(pairwise(waypoints)):
            print(f"\nRouting from waypoint {i} to waypoint {i + 1}:")
            print(f"  {start_point} -> {end_point}")

            # Get routes for this segment
            result = self.get_segment_route(start_point, end_point, max_routes_per_segment)

            if isinstance(result, str):  # Error message
                print(f"Error: {result}")
                continue

            # Process all routes for this segment
            segment_data = {
                "routes": [],
                "total_routes": len(result["routes"]),
                "best_route_index": 0,  # Default to first route as best
                "best_distance": float('inf')
            }

            # Route colors alternating by segment
            segment_base_colors = ["blue", "purple"]
            segment_base_color = segment_base_colors[i % len(segment_base_colors)]

            # Alternative route color variants
            if segment_base_color == "blue":
                route_colors = ["blue", "darkblue"]
            else:
                route_colors = ["purple", "violet"]

            # Add all alternative routes to the map
            for j, route_path in enumerate(result["routes"]):
                route_points = result["segment_points"][j]
                route_distance = result["distances"][j]
                road_names = result["road_names"][j]
                all_road.extend(road_names)

                # Track the best (shortest) route
                if route_distance < segment_data["best_distance"]:
                    segment_data["best_distance"] = route_distance
                    segment_data["best_route_index"] = j

                # Store route data
                segment_data["routes"].append({
                    "path": route_path,
                    "points": route_points,
                    "distance": route_distance,
                    "road_names": road_names
                })

                # Add this route to the map with varying opacity
                # Primary route (shortest) is more opaque
                opacity = 0.9 if j == 0 else 0.6
                weight = 5 if j == 0 else 3

                route_color = route_colors[min(j, len(route_colors) - 1)]

                folium.PolyLine(
                    route_points,
                    color=route_color,
                    weight=weight,
                    opacity=opacity,
                    popup=f"Segment {i + 1}, Route {j + 1}: {route_distance:.1f}km"
                ).add_to(m)

                print(f"  Route {j + 1}: {route_distance:.1f}km")
                print(f"  Roads: {', '.join(road_names[:5])}{'...' if len(road_names) > 5 else ''}")

            # Add segment to overall route data
            all_segments.append(segment_data)

            # Add primary route distance to total
            primary_route = segment_data["routes"][0]
            total_distance += primary_route["distance"]

        print(f"\nTotal primary route distance: {total_distance:.1f}km")

        # Add a legend
        # legend_html = """
        # <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 2px solid grey; border-radius: 5px;">
        # <h4>Route Legend</h4>
        # <div><span style="background-color: blue; width: 15px; height: 5px; display: inline-block;"></span> Primary Route</div>
        # <div><span style="background-color: purple; width: 15px; height: 5px; display: inline-block;"></span> Alternative Routes</div>
        # </div>
        # """
        # m.get_root().html.add_child(folium.Element(legend_html))
        all_road = [road for road in list(set(all_road)) if not road.startswith("way_")]
        return {
            "map": m,
            "segments": all_segments,
            "total_distance": total_distance,
            "total_road_names": all_road,
        }

    def get_segment_route(self, start_point, end_point, max_routes=3):
        """
        Get possible routes for a single segment using Overpass API and NetworkX
        """
        # Create a bounding box around the points with some padding
        min_lat = min(start_point[0], end_point[0]) - 0.05
        max_lat = max(start_point[0], end_point[0]) + 0.05
        min_lon = min(start_point[1], end_point[1]) - 0.05
        max_lon = max(start_point[1], end_point[1]) + 0.05

        # Query for roads in this area
        overpass_url = "https://overpass-api.de/api/interpreter"
        condition_highway = """motorway|trunk|primary|secondary|tertiary|unclassified"""
        query = f"""
        [out:json];
        (
          way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential"]
            ({min_lat},{min_lon},{max_lat},{max_lon});
        );
        (._;>;);  // Get all nodes for ways
        out body;
        """

        response = requests.post(overpass_url, data=query)
        data = response.json()

        # Create a graph from the data
        G = nx.DiGraph()  # Directed graph for one-way roads

        # Process nodes
        nodes = {}
        for element in data['elements']:
            if element['type'] == 'node':
                node_id = element['id']
                nodes[node_id] = (element['lat'], element['lon'])
                G.add_node(node_id, pos=(element['lat'], element['lon']))

        # Process ways (roads)
        for element in data['elements']:
            if element['type'] == 'way' and 'tags' in element and 'highway' in element['tags']:
                way_id = element['id']
                highway_type = element['tags']['highway']
                name = element['tags'].get('name', f"way_{way_id}")

                # Set edge weight based on road type
                weight_factors = {
                    'motorway': 0.7,  # Fast
                    'trunk': 0.8,
                    'primary': 0.9,
                    'secondary': 1.0,  # Normal
                    'tertiary': 1.1,
                    'unclassified': 1.2,
                    'residential': 1.3  # Slow
                }
                weight_factor = weight_factors.get(highway_type, 1.0)

                # Process nodes in the way
                for i in range(len(element['nodes']) - 1):
                    from_node = element['nodes'][i]
                    to_node = element['nodes'][i + 1]

                    if from_node in nodes and to_node in nodes:
                        # Calculate distance between nodes
                        from_pos = nodes[from_node]
                        to_pos = nodes[to_node]
                        distance = self.haversine_distance(from_pos[0], from_pos[1], to_pos[0], to_pos[1])

                        # Adjusted distance based on road type
                        weighted_distance = distance * weight_factor

                        # Add edge to graph
                        G.add_edge(from_node, to_node,
                                   weight=weighted_distance,
                                   highway=highway_type,
                                   name=name)

                        # Handle one-way streets
                        oneway = element['tags'].get('oneway', 'no')
                        if oneway != 'yes':
                            G.add_edge(to_node, from_node,
                                       weight=weighted_distance,
                                       highway=highway_type,
                                       name=name)

        # Find the nearest graph nodes to our start and end points
        start_node = self.find_nearest_node(G, start_point, nodes)
        end_node = self.find_nearest_node(G, end_point, nodes)

        if not start_node or not end_node:
            return "Could not find suitable start/end nodes in the graph"

        # Find multiple routes
        routes = []
        segment_points = []
        distances = []
        all_road_names = []

        try:
            # Find shortest path
            shortest_path = nx.shortest_path(G, start_node, end_node, weight='weight')
            routes.append(shortest_path)

            # Get the points for this route
            route_points = [nodes[node_id] for node_id in shortest_path]
            segment_points.append(route_points)

            # Calculate route distance
            distance = sum(self.haversine_distance(route_points[j][0], route_points[j][1],
                                              route_points[j + 1][0], route_points[j + 1][1])
                           for j in range(len(route_points) - 1))
            distances.append(distance)

            # Get road names along the route
            road_names = []
            for j in range(len(shortest_path) - 1):
                if G.has_edge(shortest_path[j], shortest_path[j + 1]):
                    road_name = G[shortest_path[j]][shortest_path[j + 1]].get('name')
                    if road_name and road_name not in road_names:
                        road_names.append(road_name)
            all_road_names.append(road_names)

            # Create a copy of the graph for alternative routes
            G_alt = G.copy()

            # Find alternative paths if requested
            if max_routes > 1:
                for i in range(1, max_routes):
                    # Increase weights on the shortest path to encourage different routes
                    for j in range(len(shortest_path) - 1):
                        if G_alt.has_edge(shortest_path[j], shortest_path[j + 1]):
                            G_alt[shortest_path[j]][shortest_path[j + 1]]['weight'] *= 2.0

                    # Find new shortest path
                    try:
                        alt_path = nx.shortest_path(G_alt, start_node, end_node, weight='weight')
                        # Only add if it's sufficiently different
                        if self.is_different_route(routes[0], alt_path, threshold=0.5):
                            routes.append(alt_path)

                            # Get the points for this route
                            alt_route_points = [nodes[node_id] for node_id in alt_path]
                            segment_points.append(alt_route_points)

                            # Calculate route distance using original distances
                            alt_distance = 0
                            for j in range(len(alt_path) - 1):
                                if G.has_edge(alt_path[j], alt_path[j + 1]):
                                    # Use original graph weights, not the penalized ones
                                    alt_distance += G[alt_path[j]][alt_path[j + 1]]['weight']
                            distances.append(alt_distance)

                            # Get road names along the route
                            alt_road_names = []
                            for j in range(len(alt_path) - 1):
                                if G.has_edge(alt_path[j], alt_path[j + 1]):
                                    road_name = G[alt_path[j]][alt_path[j + 1]].get('name')
                                    if road_name and road_name not in alt_road_names:
                                        alt_road_names.append(road_name)
                            all_road_names.append(alt_road_names)

                            # Also penalize this path for future alternatives
                            for j in range(len(alt_path) - 1):
                                if G_alt.has_edge(alt_path[j], alt_path[j + 1]):
                                    G_alt[alt_path[j]][alt_path[j + 1]]['weight'] *= 1.5
                    except nx.NetworkXNoPath:
                        break
        except nx.NetworkXNoPath:
            return "No route found between the specified points"

        return {
            "routes": routes,
            "segment_points": segment_points,
            "distances": distances,
            "road_names": all_road_names
        }

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate the distance between two points on earth"""
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth radius in kilometers
        return c * r


    @staticmethod
    def is_different_route(route1, route2, threshold=0.7):
        """Check if two routes are sufficiently different"""
        # Simple check: if they share less than threshold% of nodes
        common_nodes = set(route1).intersection(set(route2))
        return len(common_nodes) / max(len(route1), len(route2)) < threshold


    def find_nearest_node(self, G, point, nodes):
        """Find the node in the graph closest to the given point"""
        min_dist = float('inf')
        nearest_node = None

        for node_id, node_pos in nodes.items():
            dist = self.haversine_distance(point[0], point[1], node_pos[0], node_pos[1])
            if dist < min_dist:
                min_dist = dist
                nearest_node = node_id

        return nearest_node

    @staticmethod
    def get_city_coords(city_name):
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {'User-Agent': 'MainRoadFinder/1.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
        return None


def parser_setter():
    parser = argparse.ArgumentParser(description="Map Utility")
    parser.add_argument("-l", "--locations", type=str, nargs='+', required=True, help="List of locations to route through")
    parser.add_argument("--visualize", action='store_true', help="Visualize the route on a map")
    return parser.parse_args()

def main():
    map_util = MapUtility()
    city_names = [
        "Deinze, Flanders, Belgium",
        "Gavere, Flanders, Belgium",
        "Velzeke, Belgium",
        "Strijpen, Belgium",
        "Oudenaarde, Belgium",
        "Anzegem, Belgium",
        "Waregem, Belgium",
        "Nokere, Flanders, Belgium",
        "Kruishoutem, Belgium",
        "Ouwegem, Belgium",
        "Lange Ast, Belgium",
        "Wannegem, Belgium",
        "Nokere, Flanders, Belgium"
    ]
    tour_de_france = ["Lille Métropole, France", "Souchez, France", "Mont Cassel, France", "Mont Noir, France", "Lille Métropole, France"]
    van_vranderen = ["BRUGGE, Belgium", "Bellem, Belgium", "Izegem, Belgium","Deinze, Belgium", "Kruisem, Belgium", "Kluisbergen, Belgium", "Zwalm, Belgium", "Ronse, Belgium"]
    waypoints = [(map_util.get_city_coords(city)) for city in city_names]
    result = map_util.get_multi_waypoint_route(waypoints, max_routes_per_segment=3)
    print(result.keys())
    map_result = result["map"]

    # Save map to HTML file
    map_result.save("multi_waypoint_routes_with_alternatives.html")
    print(f"Routes generated with total primary route distance: {result['total_distance']:.1f}km")
    print(f"Total alternative routes generated: {sum(segment['total_routes'] for segment in result['segments'])}")
    print("Total road names found:", len(result["total_road_names"]))
    # route_city = map_util.get_route_city()
    with open("multi_waypoint_routes.json", "w+") as f:
        json.dump(result["total_road_names"], f, indent=4)

if __name__ == '__main__':
    main()
    # map_util = MapUtility()
    # print(map_util.get_route_city())