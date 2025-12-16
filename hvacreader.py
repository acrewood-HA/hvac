import requests
import time
import argparse
from urllib.parse import urlparse

def get_sensor_data(url, node=1):
    """
    Fetches temperature and humidity from the sensor node's JSON endpoint.
    """
    try:
        parsed_url = urlparse(url)
        # Construct the correct API endpoint URL based on the provided JS file
        data_url = parsed_url._replace(path='/nodeinfoget').geturl()
        
        params = {
            'node': node,
            't': int(time.time() * 1000) # Cache-busting timestamp
        }
        
        response = requests.get(data_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Look for common key names for temperature and humidity in the JSON response
        temp = None
        humidity = None
        
        # Likely keys for temperature: "temp", "temperature", etc.
        temp_key = next((k for k in data if k.lower() in ['temperature', 'temp']), None)
        if temp_key:
            temp = float(data[temp_key])
            
        # Likely keys for humidity: "humidity", "hum", "rh", etc.
        hum_key = next((k for k in data if k.lower() in ['humidity', 'hum', 'rh']), None)
        if hum_key:
            humidity = float(data[hum_key])

        return {
            'temperature': temp,
            'humidity': humidity,
            'source': 'json',
            'raw_response': data
        }

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return None
    except ValueError as e: # Catches JSON parsing errors
        print(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Usage example with continuous monitoring
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HVAC sensor data reader.")
    parser.add_argument(
        '--url',
        type=str,
        default='http://192.168.1.44/nodeconfig.html',
        help='Base URL of the sensor node. Can be the HTML page, the script will find the API endpoint.'
    )
    parser.add_argument(
        '--node',
        type=int,
        default=1,
        help='The node number to query.'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Polling interval in seconds.'
    )
    args = parser.parse_args()

    while True:
        data = get_sensor_data(args.url, args.node)
        if data:
            temp_str = f"{data['temperature']}°C" if data.get('temperature') is not None else "N/A"
            hum_str = f"{data['humidity']}%" if data.get('humidity') is not None else "N/A"
            
            print(f"Reading from {args.url} (Node {args.node})")
            print(f"Temperature: {temp_str}")
            print(f"Humidity: {hum_str}")

            if data.get('temperature') is None and data.get('humidity') is None:
                print("Could not find temperature or humidity in the JSON response.")
                print(f"Raw JSON response: {data.get('raw_response')}")
        else:
            print(f"Failed to retrieve or parse data from {args.url}")
        
        print("-" * 40)
        time.sleep(args.interval)
