import requests
from datetime import datetime
from config.settings import OPENWEATHER_BASE_URL, API_TIMEOUT


def get_current_temperature(city_name, api_key):
    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }
    try:
        response = requests.get(OPENWEATHER_BASE_URL, params=params, timeout=API_TIMEOUT)
        if response.status_code == 401:
            return {
                'success': False,
                'error': 'invalid_key',
                'message': response.json().get('message', 'Invalid API key')
            }
        
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'temp_min': data['main']['temp_min'],
            'temp_max': data['main']['temp_max'],
            'pressure': data['main']['pressure'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed'],
            'timestamp': datetime.fromtimestamp(data['dt'])
        } 
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': 'request_error',
            'message': str(e)
        }
