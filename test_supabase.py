from dotenv import load_dotenv
import os
from supabase import create_client, Client
import logging

# Load environment variables from .env file
load_dotenv()

# Print environment variables to debug
print("SUPABASE_URL:", os.getenv('SUPABASE_URL'))
print("SUPABASE_KEY:", os.getenv('SUPABASE_KEY'))
print("OPENWEATHER_API_KEY:", os.getenv('OPENWEATHER_API_KEY'))

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Supabase setup
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def test_supabase():
    data = {
        'location': 'test_location',
        'forecast': {
            'day': 'Monday',
            'temperature': 25,
            'humidity': '50%',
            'wind_speed': '5 m/s'
        }
    }
    try:
        response = supabase.table('weather').insert(data).execute()
        logging.debug(f'Supabase response: {response}')
    except Exception as e:
        logging.error(f'Error saving to Supabase: {e}')
        raise e

if __name__ == '__main__':
    test_supabase()