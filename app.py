from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import uuid
import jwt

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')  # Default value for development

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Supabase setup
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase_jwt_secret = os.getenv('SUPABASE_JWT_SECRET')

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        try:
            # Validate UUID
            uuid.UUID(user_id)
        except ValueError:
            # Generate a valid UUID if the input is not a valid UUID
            user_id = str(uuid.uuid4())
        user = User(user_id)
        login_user(user)
        return redirect(url_for('weather'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def weather():
    weather_data = None
    if request.method == 'POST':
        location = request.form['location']
        user_id = current_user.id  # Get the current user's ID
        weather_data = get_weather(location, user_id)
    return render_template('index.html', weather_data=weather_data)

def get_weather(location, user_id):
    api_key = os.getenv('OPENWEATHER_API_KEY')
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()

    forecast = {}
    for item in data['list']:
        day = item['dt_txt'].split(' ')[0]
        forecast[day] = {
            'day_of_week': day,
            'icon': get_icon(item['weather'][0]['icon']),
            'formatted_date': item['dt_txt'],
            'temperature': item['main']['temp'],
            'humidity': item['main']['humidity'],
            'wind_speed': item['wind']['speed'],
        }
    save_to_supabase(location, forecast, user_id)
    return forecast

def get_icon(icon_code):
    icon_mapping = {
        '01d': 'wi-day-sunny',
        '02d': 'wi-day-cloudy',
        '03d': 'wi-cloud',
        '04d': 'wi-cloudy',
        '09d': 'wi-showers',
        '10d': 'wi-rain',
        '11d': 'wi-thunderstorm',
        '13d': 'wi-snow',
        '50d': 'wi-fog',
        '01n': 'wi-night-clear',
        '02n': 'wi-night-alt-cloudy',
        '03n': 'wi-night-alt-cloudy-high',
        '04n': 'wi-night-alt-cloudy-high',
        '09n': 'wi-night-alt-showers',
        '10n': 'wi-night-alt-rain',
        '11n': 'wi-night-alt-thunderstorm',
        '13n': 'wi-night-alt-snow',
        '50n': 'wi-night-fog'
    }
    return icon_mapping.get(icon_code, 'wi-na')

def save_to_supabase(location, forecast, user_id):
    data = {
        'user_id': user_id,
        'location': location,
        'forecast': forecast,
        'created_at': datetime.now().isoformat()  # Convert datetime to string
    }
    token = jwt.encode({"sub": user_id}, supabase_jwt_secret, algorithm="HS256")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": supabase_key
    }
    
    try:
        # Check for existing entries
        check_response = requests.get(
            f"{supabase_url}/rest/v1/weather?location=eq.{location}&user_id=eq.{user_id}",
            headers=headers
        )
        check_response.raise_for_status()
        existing_entries = check_response.json()

        if existing_entries:
            logging.debug(f'Duplicate entry found for location: {location} and user_id: {user_id}')
            return
        
        # Directly interact with the Supabase REST API using the requests library
        response = requests.post(
            f"{supabase_url}/rest/v1/weather",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        
        # Check if the response contains JSON data
        if response.content:
            logging.debug(f'Supabase response: {response.json()}')
        else:
            logging.debug('Supabase response: No content')
    except requests.exceptions.RequestException as e:
        logging.error(f'Error saving to Supabase: {e}')
        raise e

if __name__ == '__main__':
    app.run(debug=True)
