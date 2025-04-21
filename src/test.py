import requests
import networkx as nx
import folium
import math
from itertools import pairwise


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


# Example usage with multiple waypoints
waypoints = [
    (48.8566, 2.3522),  # Paris
    (48.7486, 2.3557),  # Orly
    (48.6210, 2.4521),  # Corbeil-Essonnes
    (48.5734, 2.4520)  # Evry
]

result = get_multi_waypoint_route(waypoints, max_routes_per_segment=3)
map_result = result["map"]

# Save map to HTML file
map_result.save("multi_waypoint_routes_with_alternatives.html")
print(f"Routes generated with total primary route distance: {result['total_distance']:.1f}km")
print(f"Total alternative routes generated: {sum(segment['total_routes'] for segment in result['segments'])}")