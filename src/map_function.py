import osmnx as ox
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from dotenv import load_dotenv
import json
import matplotlib.pyplot as plt
import requests
import networkx as nx
import folium
import math
from itertools import pairwise

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


def get_all_main_roads_between(city1, city2):
    # Get the street networks for both cities
    G1 = ox.graph_from_place(f"{city1}", network_type="drive")
    G2 = ox.graph_from_place(f"{city2}", network_type="drive")

    # Get a larger area that contains both cities
    combined_area = f"{city1} to {city2}"
    # G_combined = ox.graph_from_place(combined_area, network_type="drive")

    # Filter for just the main roads
    main_roads = ["motorway", "trunk", "primary", "secondary"]
    G_main = ox.graph_from_place(combined_area, network_type="drive",
                                 custom_filter=f'["highway"~"{"|".join(main_roads)}"]')

    # Plot the result
    fig, ax = plt.subplots(figsize=(12, 8))
    ox.plot_graph(G_main, ax=ax, node_size=0, edge_linewidth=1.5)
    plt.title(f"Main Roads Between {city1} and {city2}")
    plt.show()

    return G_main

def get_city_coords(city_name):
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    headers = {'User-Agent': 'MainRoadFinder/1.0'}
    response = requests.get(url, headers=headers)
    data = response.json()
    if data:
        return float(data[0]['lat']), float(data[0]['lon'])
    return None

def raw():
    city1_name = "Deinze, Belgium"
    city2_name = "Nokere, Belgium"
    city1_coords = get_city_coords(city1_name)
    city2_coords = get_city_coords(city2_name)
    print(f"Coordinates of {city1_name}: {city1_coords}")
    print(f"Coordinates of {city2_name}: {city2_coords}")

    lat1, lon1 = city1_coords
    lat2, lon2 = city2_coords

    min_lat = min(lat1, lat2) - 0.1
    max_lat = max(lat1, lat2) + 0.1
    min_lon = min(lon1, lon2) - 0.1
    max_lon = max(lon1, lon2) + 0.1

    # Query for main roads
    overpass_url = "https://overpass-api.de/api/interpreter"
    condition_query = """
        ["highway"~"motorway|trunk|primary|cycleway"]["bicycle"!~"no"]
        """
    query = f"""
            [out:json];
            way
              ({min_lat},{min_lon},{max_lat},{max_lon})
              {condition_query};
            out geom;
            """

    response = requests.post(overpass_url, data=query)
    data = response.json()

    # Create a map centered between the two cities
    center_lat = (lat1 + lat2) / 2
    center_lon = (lon1 + lon2) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=9)

    # Add markers for cities
    folium.Marker([lat1, lon1], popup=city1_name).add_to(m)
    folium.Marker([lat2, lon2], popup=city2_name).add_to(m)
    road_names = []
    for way in data['elements']:
        if 'geometry' in way:
            points = [(node['lat'], node['lon']) for node in way['geometry']]

            # Determine color based on road type
            color = 'gray'
            if 'tags' in way:
                if way['tags'].get('bicycle') == 'no' or not way['tags'].get('bicycle'):
                    continue
                print(way['tags'])
                if way['tags'].get('highway') == 'motorway':
                    color = 'blue'
                elif way['tags'].get('highway') == 'trunk':
                    color = 'green'
                elif way['tags'].get('highway') == 'primary':
                    color = 'red'
                elif way['tags'].get('highway') == 'cycleway':
                    color = 'orange'
                # elif way['tags'].get('bicycle') == 'yes':
                #     color = 'purple'
                # elif way['tags'].get('bicycle') == 'designated':
                #     color = 'yellow'

            road_name = way['tags'].get('name', 'Unnamed road')
            road_ref = way['tags'].get('ref', '')
            popup_text = f"{road_name} ({road_ref})" if road_ref else road_name
            if not road_name == 'Unnamed road' and road_name not in road_names:
                road_names.append(popup_text)

            folium.PolyLine(
                points,
                color=color,
                weight=3,
                opacity=0.7,
                popup=popup_text
            ).add_to(m)

        # Save map to HTML file
    m.save('main_roads_map.html')
    print(road_names)
    print("Map saved as 'main_roads_map.html'")


def get_road_names(city_names: list[str]) -> list[str]:
    city_coo = {}
    city_to_city = {}
    for index1 in range(0, len(city_names)-1):
        city1_name = city_names[index1]
        city2_name = city_names[index1 + 1]
        city1_coords = get_city_coords(city1_name)
        city2_coords = get_city_coords(city2_name)

        city_coo[city1_name] = city1_coords
        city_coo[city2_name] = city2_coords

        lat1, lon1 = city1_coords
        lat2, lon2 = city2_coords

        min_lat = min(lat1, lat2) - 0.1
        max_lat = max(lat1, lat2) + 0.1
        min_lon = min(lon1, lon2) - 0.1
        max_lon = max(lon1, lon2) + 0.1
        city_to_city[f"{city1_name} to {city2_name}"] = min_lat, min_lon, max_lat, max_lon
    overpass_url = "https://overpass-api.de/api/interpreter"
    condition_query = '["highway"~"motorway|trunk|primary|secondary|cycleway"]'

    lat1, lon1 = city_coo[city_names[0]]
    lat2, lon2 = city_coo[city_names[-1]]
    print(f"Coordinates of {city_names[0]}: {lat1}, {lon1}")
    print(f"Coordinates of {city_names[-1]}: {lat2}, {lon2}")

    lat = (lat1 + lat2) / 2
    lon = (lon1 + lon2) / 2
    differ = abs(lat1-lat2)
    print(f"Difference in latitude: {differ}")
    zoom = round((differ* 1000)/8)
    print(f"Zoom level: {zoom}")

    m = folium.Map(location=[lat, lon], zoom_start=8)
    for city_name, (lat, lon) in city_coo.items():
        folium.Marker([lat, lon], popup=city_name).add_to(m)

    sum_query = []
    for coor in city_to_city.values():
        min_lat, min_lon, max_lat, max_lon = coor
        # Query for main roads
        line_query = f"""
                way
                  ({min_lat},{min_lon},{max_lat},{max_lon})
                  {condition_query};
                """
        sum_query.append(line_query)
    sum_query = [f"way({min_lat},{min_lon},{max_lat},{max_lon}){condition_query};" for min_lat, min_lon, max_lat, max_lon in city_to_city.values()]
    print(sum_query)
    query = f"""
            [out:json];
            (
            {"\n".join([line_query for line_query in sum_query])}
            );
            out geom;
            """
    print(query)
    response = requests.post(overpass_url, data=query)
    data = response.json()
    road_names = []
    road_names_no_ref = []
    print(data)
    for way in data['elements']:
        if 'geometry' in way:
            points = [(node['lat'], node['lon']) for node in way['geometry']]

            # Determine color based on road type
            color = 'gray'
            if 'tags' in way:
                if way['tags'].get('bicycle') == 'no':
                    continue

            road_name = way['tags'].get('name', 'Unnamed road')

            road_ref = way['tags'].get('ref', '')
            popup_text = f"{road_name} ({road_ref})" if road_ref else road_name

            if (road_name != 'Unnamed road') and road_name not in road_names_no_ref:
                road_names_no_ref.append(road_name)
                road_names.append(road_name)

            folium.PolyLine(
                points,
                color='blue',
                weight=3,
                opacity=0.7,
            ).add_to(m)
    m.save('main_roads_map.html')
    print(road_names)
    data
    with open('data_streetmao.json', 'w+') as file:
        json.dump(data, file, indent=4)

    with open('main_roads_map.json', 'w+') as file:
        json.dump(road_names, file, indent=4)
    return road_names

def get_multi_waypoint_route(waypoints, max_routes_per_segment=3):
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
            color = colors[min(i, len(colors) - 1)]

        folium.Marker(
            point,
            popup=marker_text,
            icon=folium.Icon(color=color)
        ).add_to(m)

    # Process each segment between consecutive waypoints
    total_distance = 0
    all_segments = []

    # Get pairs of waypoints (start->wp1, wp1->wp2, etc.)
    for i, (start_point, end_point) in enumerate(pairwise(waypoints)):
        print(f"\nRouting from waypoint {i} to waypoint {i + 1}:")
        print(f"  {start_point} -> {end_point}")

        # Get routes for this segment
        result = get_segment_route(start_point, end_point, max_routes_per_segment)
        print(result)

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
            route_colors = ["blue", "darkblue", "lightblue"]
        else:
            route_colors = ["purple", "darkpurple", "violet"]

        # Add all alternative routes to the map
        for j, route_path in enumerate(result["routes"]):
            route_points = result["segment_points"][j]
            route_distance = result["distances"][j]
            road_names = result["road_names"][j]

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
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 2px solid grey; border-radius: 5px;">
    <h4>Route Legend</h4>
    <div><span style="background-color: blue; width: 15px; height: 5px; display: inline-block;"></span> Primary Route</div>
    <div><span style="background-color: purple; width: 15px; height: 5px; display: inline-block;"></span> Alternative Routes</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return {
        "map": m,
        "segments": all_segments,
        "total_distance": total_distance
    }


def get_segment_route(start_point, end_point, max_routes=3):
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
                    distance = haversine_distance(from_pos[0], from_pos[1], to_pos[0], to_pos[1])

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
    start_node = find_nearest_node(G, start_point, nodes)
    end_node = find_nearest_node(G, end_point, nodes)

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
        distance = sum(haversine_distance(route_points[j][0], route_points[j][1],
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
                    if is_different_route(routes[0], alt_path, threshold=0.5):
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


def find_nearest_node(G, point, nodes):
    """Find the node in the graph closest to the given point"""
    min_dist = float('inf')
    nearest_node = None

    for node_id, node_pos in nodes.items():
        dist = haversine_distance(point[0], point[1], node_pos[0], node_pos[1])
        if dist < min_dist:
            min_dist = dist
            nearest_node = node_id

    return nearest_node


def is_different_route(route1, route2, threshold=0.7):
    """Check if two routes are sufficiently different"""
    # Simple check: if they share less than threshold% of nodes
    common_nodes = set(route1).intersection(set(route2))
    return len(common_nodes) / max(len(route1), len(route2)) < threshold




if __name__ == '__main__':
    city_names = [
        "Deinze, Flanders, Belgium",
        "Gavere, Flanders, Belgium",
        # "Zottegem, Belgium",
        # "Oudenaarde, Belgium",
        # "Anzegem, Belgium",
        # "Waregem, Belgium",
        # "Nokere, Flanders, Belgium",
        # "Kruisem, Belgium"
    ]
    waypoints = [(get_city_coords(city)) for city in city_names]
    print(waypoints)
    # start = (48.8566, 2.3522)  # Paris
    # end = (48.5734, 2.4520)  # Evry (closer destination for faster testing)
    result = get_multi_waypoint_route(waypoints, max_routes_per_segment=5)
    map_result = result["map"]

    # Save map to HTML file
    map_result.save("multi_waypoint_routes_with_alternatives.html")
    print(f"Routes generated with total primary route distance: {result['total_distance']:.1f}km")
    print(f"Total alternative routes generated: {sum(segment['total_routes'] for segment in result['segments'])}")