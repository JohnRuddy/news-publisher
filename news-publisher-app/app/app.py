from flask import Flask, render_template, request, jsonify
from datetime import datetime
import redis
import requests
from urllib.parse import urlparse
import os

app = Flask(__name__)

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

@app.context_processor
def inject_current_year():
    """Inject the current year into templates."""
    return {'current_year': datetime.now().year}

def normalize_url(url):
    """Ensure the URL has a valid scheme (http or https)."""
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = "http://" + url
    return url

def is_valid_url(url):
    """Check if the URL is valid and reachable."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

@app.route('/', methods=['GET', 'POST'])
def home():
    """Render the home page and handle form submission."""
    if request.method == 'POST':
        url = request.form['url']
        category = request.form['category']
        reason = request.form['reason']
        comment = request.form.get('comment', '')

        # Normalize and validate the URL
        url = normalize_url(url)
        if not is_valid_url(url):
            return jsonify({'error': 'The provided URL is not valid or reachable.'}), 400

        # Save data to Redis
        submission_id = redis_client.incr('submission_id')  # Auto-increment ID
        redis_client.hmset(f'submission:{submission_id}', {
            'url': url,
            'category': category,
            'reason': reason,
            'comment': comment,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'message': 'Thank you for your submission!'})

    # Fetch all submissions from Redis
    submission_keys = redis_client.keys('submission:*')
    submissions = [
        redis_client.hgetall(key) for key in submission_keys
    ]

    # Get the last 10 sites added
    last_ten_sites = sorted(submissions, key=lambda x: x['timestamp'], reverse=True)[:10]

    # Count reports for each site
    report_counts = {}
    for submission in submissions:
        url = submission['url']
        report_counts[url] = report_counts.get(url, 0) + 1

    # Get sites ordered by number of reports
    most_
    reported_sites = sorted(report_counts.items(), key=lambda x: x[1], reverse=True)
    most_reported_sites = [{'url': url, 'report_count': count} for url, count in most_reported_sites]

    return render_template('index.html', last_ten_sites=last_ten_sites, most_reported_sites=most_reported_sites)

@app.route('/details/<path:url>')
def details(url):
    """Render the details page for a specific URL."""
    # Fetch all submissions for the given URL
    submission_keys = redis_client.keys('submission:*')
    submissions = [
        redis_client.hgetall(key) for key in submission_keys if redis_client.hget(key, 'url') == url
    ]

    # Sort submissions by timestamp (descending)
    submissions.sort(key=lambda x: x['timestamp'], reverse=True)

    return render_template('details.html', url=url, submissions=submissions)

if __name__ == '__main__':
    app.run(debug=True)