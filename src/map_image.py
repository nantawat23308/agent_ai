import os
import numpy as np
import matplotlib.pyplot as plt
import cv2
import requests
import folium
from shapely.geometry import LineString, Point
import osmnx as ox
import geopandas as gpd
from PIL import Image
import rasterio
from rasterio.transform import from_origin
import pyproj


def extract_route_from_image(image_path):
    """Extract the red line route from the race map image"""
    # Load the image
    img = cv2.imread(image_path)

    # Convert to HSV color space for better color filtering
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define range for red color
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # Create masks for red regions
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Find contours of the red line
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Extract the route as a series of points
    route_points = []
    for contour in contours:
        # Filter out small contours (noise)
        if cv2.contourArea(contour) > 100:
            for point in contour:
                route_points.append(point[0])

    return np.array(route_points)


def georeference_image_and_route(image_path, route_points):
    """
    Georeference the image and route points based on known coordinates
    of cities visible in the map
    """
    # Known reference points (image x,y to geo lat,lon)
    # These would need to be adjusted for the actual image
    reference_points = {
        "Deinze": {"pixel": (218, 37), "coord": (50.9847, 3.5263)},
        "Nokere": {"pixel": (193, 245), "coord": (50.8883, 3.5458)},
        "Oudenaarde": {"pixel": (320, 330), "coord": (50.8454, 3.6067)},
        "Zwalm": {"pixel": (105, 245), "coord": (50.8868222, 3.4323622)}  # Added point
    }

    # Create transformation matrix
    src_points = np.array([p["pixel"] for p in reference_points.values()])
    dst_points = np.array([p["coord"] for p in reference_points.values()])

    # Calculate transformation matrix
    transform_matrix, _ = cv2.findHomography(src_points, dst_points)

    # Transform route points to geographic coordinates
    route_points_homogeneous = np.hstack([route_points, np.ones((len(route_points), 1))])
    route_geo_points = np.dot(transform_matrix, route_points_homogeneous.T).T
    route_geo_points = route_geo_points[:, :2] / route_geo_points[:, 2:3]

    return route_geo_points


def get_cities_along_route(route_geo_points, buffer_distance=0.01):
    """
    Get cities along the route using OpenStreetMap data
    """
    # Create a LineString from the route points
    route_line = LineString(route_geo_points)
    print("Route LineString:", route_line)
    # Create a buffer around the route
    route_buffer = route_line.buffer(buffer_distance)
    print("Route Buffer:", route_buffer)
    # Get the bounding box of the route
    minx, miny, maxx, maxy = route_buffer.bounds
    bbox = (maxy, miny, maxx, minx)
    print("Bounding Box:", bbox)
    # Download OpenStreetMap data for the area
    places = ox.features.features_from_bbox(
        bbox,
        tags={'place': ['city', 'town', 'village', 'hamlet']}
    )
    print("Places from OSM:", places)

    # Convert to GeoDataFrame
    gdf_places = gpd.GeoDataFrame(places, crs='EPSG:4326')

    # Find places that intersect with the route buffer
    cities_along_route = []
    for idx, place in gdf_places.iterrows():
        if place.geometry.intersects(route_buffer):
            cities_along_route.append({
                'name': place.get('name', 'Unknown'),
                'type': place.get('place', 'Unknown'),
                'geometry': place.geometry
            })

    return cities_along_route


def visualize_route_with_cities(image_path, route_geo_points, cities):
    """
    Visualize the route and cities on an interactive map
    """
    # Create a map centered on the route
    center_lat = np.mean([p[1] for p in route_geo_points])
    center_lon = np.mean([p[0] for p in route_geo_points])
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

    # Add the route
    folium.PolyLine(
        locations=[[p[1], p[0]] for p in route_geo_points],
        color='red',
        weight=5,
        opacity=0.7
    ).add_to(m)

    # Add cities along the route
    for city in cities:
        if isinstance(city['geometry'], Point):
            folium.Marker(
                location=[city['geometry'].y, city['geometry'].x],
                popup=f"{city['name']} ({city['type']})",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

    # Save the map
    m.save('danilith_nokere_koerse_route_with_cities.html')

    return m


def main(image_path):
    """
    Main function to process the race map and extract cities
    """
    # Extract the route from the image
    print("Extracting route from image...")
    route_points = extract_route_from_image(image_path)

    # Geo reference the image and route
    print("Geo referencing route...")
    route_geo_points = georeference_image_and_route(image_path, route_points)
    print("Route Geo Points:", route_geo_points)

    # Get cities along the route
    print("Finding cities along the route...")
    cities = get_cities_along_route(route_geo_points)

    # Visualize the route with cities
    print("Creating visualization...")
    visualize_route_with_cities(image_path, route_geo_points, cities)

    # Print the cities
    print("\nCities along the Danilith Nokere Koerse route:")
    for i, city in enumerate(cities, 1):
        print(f"{i}. {city['name']} ({city['type']})")

    return cities


if __name__ == "__main__":
    image_path = "/home/nantawat/Desktop/my_project/agent_with_me/doc/DNK_Bikeraceinfo.png"  # Path to the map image
    cities = main(image_path)