import requests
from bs4 import BeautifulSoup
import re
import time
import argparse

def get_sensor_data(url):
    """
    Fetches temperature and humidity from the specified URL.
    Parses common HTML patterns for sensor data.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        temp = None
        humidity = None
        
        # Search for temperature patterns (e.g., "Temp: 23.5°C", "Temperature=22.1")
        temp_patterns = [
            r'temp(?:erature)?[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)[°cC]?\s*(?:temp|°C)',
            r'"temp"[:\s]*"?(\d+(?:\.\d+)?)'
        ]
        
        # Search for humidity patterns (e.g., "Humidity: 45%", "RH=52")
        hum_patterns = [
            r'humidity|rh[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*%?\s*(?:hum|RH|humidity)',
            r'"humidity"[:\s]*"?(\d+(?:\.\d+)?)'
        ]
        
        text_content = soup.get_text()
        
        for pattern in temp_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                temp = float(match.group(1))
                break
        
        for pattern in hum_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                humidity = float(match.group(1))
                break
        
        return {
            'temperature': temp,
            'humidity': humidity,
            'raw_html_preview': response.text[:1000]
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return None
    except Exception as e:
        print(f"Parsing error: {e}")
        return None

# Usage example with continuous monitoring
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HVAC sensor data reader.")
    parser.add_argument(
        '--url',
        type=str,
        default='http://192.168.1.44/nodeconfig.html',
        help='URL of the sensor node page.'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Polling interval in seconds.'
    )
    args = parser.parse_args()

    while True:
        data = get_sensor_data(args.url)
        if data:
            temp_str = f"{data['temperature']}°C" if data['temperature'] is not None else "N/A"
            hum_str = f"{data['humidity']}%" if data['humidity'] is not None else "N/A"
            print(f"Reading from {args.url}")
            print(f"Temperature: {temp_str}")
            print(f"Humidity: {hum_str}")

            if data['temperature'] is None and data['humidity'] is None:
                print("Could not parse sensor data. Raw HTML preview:")
                print(data['raw_html_preview'])
        else:

            print(f"Failed to retrieve data from {args.url}")
        
        print("-" * 40)
        time.sleep(args.interval)
