from flask import Flask, jsonify, request
import gevent
from gevent import monkey
import requests

monkey.patch_all()

app = Flask(__name__)

TIMEOUT_SECONDS = 0.5

def fetch_numbers(url):
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            data = response.json()
            if 'numbers' in data:
                return data['numbers']
    except:
        pass
    return []

@app.route('/numbers', methods=['GET'])
def get_numbers():
    urls = request.args.getlist('url')

    if not urls:
        return jsonify(error='Missing "url" query parameter'), 400

    jobs = [gevent.spawn(fetch_numbers, url) for url in urls]
    gevent.joinall(jobs)

    aggregated_numbers = set()

    for job in jobs:
        numbers = job.value
        aggregated_numbers.update(numbers)

    sorted_numbers = sorted(aggregated_numbers)
    
    return jsonify(numbers=sorted_numbers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)


