import requests
import time
import argparse
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def get_sensor_data(url, node=1):
    """
    Fetches temperature and humidity from the sensor node's JSON endpoint.
    """
    try:
        parsed_url = urlparse(url)
        data_url = parsed_url._replace(path='/nodeinfoget').geturl()
        
        params = {
            'node': node,
            't': int(time.time() * 1000)
        }
        
        response = requests.get(data_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        temp_key = next((k for k in data if k.lower() in ['temperature', 'temp']), None)
        hum_key = next((k for k in data if k.lower() in ['humidity', 'hum', 'rh']), None)
        
        return {
            'temperature': float(data[temp_key]) if temp_key else None,
            'humidity': float(data[hum_key]) if hum_key else None,
            'raw_response': data
        }

    except (requests.exceptions.RequestException, ValueError, Exception) as e:
        print(f"Error getting sensor data: {e}")
        return None

def get_box_info(box_url):
    """
    Fetches FilterRemainingTime from the box's JSON endpoint.
    """
    try:
        parsed_url = urlparse(box_url)
        data_url = parsed_url._replace(path='/boxinfoget').geturl()
        
        params = {'t': int(time.time() * 1000)}
        
        response = requests.get(data_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        filter_time = None
        
        # The JSON is nested; iterate through the modules to find the key
        for module_name, module_data in data.items():
            if isinstance(module_data, dict) and 'FilterRemainingTime' in module_data:
                filter_time = int(module_data['FilterRemainingTime'])
                break # Stop once found

        return {'filter_remaining_time': filter_time}

    except (requests.exceptions.RequestException, ValueError, Exception) as e:
        print(f"Error getting box info: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HVAC data reader.")
    parser.add_argument(
        '--node-url',
        type=str,
        default='http://192.168.1.44/nodeconfig.html',
        help='URL of the sensor node page.'
    )
    parser.add_argument(
        '--box-url',
        type=str,
        default='http://192.168.1.44/boxinfo.html',
        help='URL of the box info page for filter time.'
    )
    parser.add_argument(
        '--node', type=int, default=1, help='The node number to query.'
    )
    parser.add_argument(
        '--interval', type=int, default=30, help='Polling interval in seconds.'
    )
    args = parser.parse_args()

    while True:
        sensor_data = get_sensor_data(args.node_url, args.node)
        box_data = get_box_info(args.box_url)
        
        # Prepare display strings
        temp_str = "N/A"
        hum_str = "N/A"
        filter_str = "N/A"

        if sensor_data:
            print(f"Reading from {args.node_url} (Node {args.node})")
            if sensor_data.get('temperature') is not None:
                temp_str = f"{sensor_data['temperature']}°C"
            if sensor_data.get('humidity') is not None:
                hum_str = f"{sensor_data['humidity']}%"
        else:
            print(f"Failed to retrieve sensor data from {args.node_url}")

        if box_data:
            print(f"Reading from {args.box_url}")
            if box_data.get('filter_remaining_time') is not None:
                filter_str = f"{box_data['filter_remaining_time']} hours"
        else:
            print(f"Failed to retrieve box info from {args.box_url}")

        print("-" * 20)
        print(f"Temperature: {temp_str}")
        print(f"Humidity: {hum_str}")
        print(f"Filter Remaining: {filter_str}")
        print("-" * 20)
        
        # Debugging for missing values
        if sensor_data and (sensor_data.get('temperature') is None or sensor_data.get('humidity') is None):
            print("Debug: Could not find temp/humidity in JSON.")
            print(f"Raw Sensor JSON: {sensor_data.get('raw_response')}")
        
        if box_data and box_data.get('filter_remaining_time') is None:
            print("Debug: Could not find 'FilterRemainingTime' in HTML.")

        print(f"Waiting for {args.interval} seconds...")
        time.sleep(args.interval)
