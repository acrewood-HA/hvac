import requests
import time
import argparse
import re
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def get_sensor_data(url, node=1):
    """
    Fetches temperature and humidity from the sensor node's JSON endpoint.
    """
    try:
        parsed_url = urlparse(url)
        data_url = parsed_url._replace(path='/nodeinfoget').geturl()
        params = {'node': node, 't': int(time.time() * 1000)}
        response = requests.get(data_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        temp_key = next((k for k in data if k.lower() in ['temperature', 'temp']), None)
        hum_key = next((k for k in data if k.lower() in ['humidity', 'hum', 'rh']), None)
        
        return {
            'temperature': float(data[temp_key]) if temp_key and data[temp_key] is not None else None,
            'humidity': float(data[hum_key]) if hum_key and data[hum_key] is not None else None
        }
    except Exception:
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
        for module_data in data.values():
            if isinstance(module_data, dict) and 'FilterRemainingTime' in module_data:
                filter_time = int(module_data['FilterRemainingTime'])
                break
        
        return {'filter_remaining_time': filter_time}
    except Exception:
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HVAC data reader for Home Assistant.")
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
    args = parser.parse_args()

    # Fetch data from both sources
    sensor_data = get_sensor_data(args.node_url, args.node)
    box_data = get_box_info(args.box_url)

    # Combine into a single JSON output
    output = {}
    if sensor_data:
        output.update(sensor_data)
    if box_data:
        output.update(box_data)
        
    # Print the combined JSON data
    print(json.dumps(output))
