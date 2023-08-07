from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta
from flask_caching import Cache
import json

app = Flask(__name__)

# Configure caching with Flask-Caching
cache = Cache(app)

JOHN_DOE_API_BASE_URL = "http://20.244.56.144/train"
ACCESS_TOKEN = None


def get_access_token():
    auth_data = {
        "companyName": "Train Central",
        "clientID": "812a1155-2934-4854-b75a-cfaaaab40cf2",
        "clientSecret": "oUldbmBTePZsFmDZ",
        "ownerName": "krish",
        "ownerEmail": "krishnabathula19@gmail.com",
        "rollNo": "160120733058"
    }

    response = requests.post(f"{JOHN_DOE_API_BASE_URL}/auth", json=auth_data)
    access_data = response.json()
    return access_data.get('access_token')


@app.route('/trains', methods=['GET'])
# Cache the response for 10 minutes (adjust as needed)
def get_train_schedules():
    global ACCESS_TOKEN
    if not ACCESS_TOKEN:
        ACCESS_TOKEN = get_access_token()

    try:
        # Fetching real-time train schedules from the John Doe Railway Server
        response = requests.get(f"{JOHN_DOE_API_BASE_URL}/trains", headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
        response.raise_for_status()
        all_trains = response.json()

        if not isinstance(all_trains, list):
            raise ValueError("Unexpected response format: 'all_trains' must be a list of dictionaries.")

        # Filtering trains departing in the next 30 minutes
        current_time = datetime.now()
        thirty_minutes_from_now = current_time + timedelta(minutes=30)

        filtered_trains = [
            train for train in all_trains if isinstance(train, dict) and compare_time(train.get('departureTime', {}), thirty_minutes_from_now)
        ]

        # Calculate the delay for each train and format departure time
        for train in filtered_trains:
            delay = train.get('delayedBy', 0)
            train['departureTime']['Minutes'] += delay
            train['departureTime'] = f"{train['departureTime']['Hours']:02d}:{train['departureTime']['Minutes']:02d}"

        # Sorting the trains based on the specified criteria
        sorted_trains = sorted(filtered_trains, key=lambda x: (x['price']['sleeper'], -x['seatsAvailable']['sleeper'], x['departureTime']))

        return jsonify(sorted_trains)

    except requests.exceptions.RequestException as e:
        return {'error': 'Failed to fetch train schedules from the John Doe Railway Server.'}, 500
    except ValueError as e:
        return {'error': str(e)}, 500
    except requests.exceptions.HTTPError as e:
        # Handle invalid or expired access token
        if e.response.status_code == 401:
            ACCESS_TOKEN = get_access_token()
            return get_train_schedules()  # Retry fetching train schedules with the new access token
        return {'error': 'Failed to fetch train schedules from the John Doe Railway Server.'}, 500
    except Exception as e:
        return {'error': str(e)}, 500


def compare_time(time_dict, reference_time):
    hours = time_dict.get('Hours', 0)
    minutes = time_dict.get('Minutes', 0)
    total_minutes = hours * 60 + minutes
    reference_total_minutes = reference_time.hour * 60 + reference_time.minute
    return total_minutes > reference_total_minutes


if __name__ == '__main__':
    app.run(debug=True)  