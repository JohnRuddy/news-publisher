from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import redis
import requests
from urllib.parse import urlparse, urlunparse
import subprocess
import os
import imgkit

app = Flask(__name__)

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Directory to save screenshots
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

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

def capture_screenshot(url, submission_id):
    """Capture a screenshot of the URL's root page using imgkit."""
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{submission_id}.png")
    try:
        imgkit.from_url(url, screenshot_path)
        return screenshot_path
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        # Return an empty string or a placeholder value if the screenshot fails
        return ""

@app.route('/', methods=['GET', 'POST'])
def home():
    """Render the home page and handle form submission."""
    if request.method == 'POST':
        url = request.form['url']
        category = request.form['category']
        reason = request.form['reason']
        comment = request.form['comment']

        # Normalize and validate the URL
        url = normalize_url(url)
        if not is_valid_url(url):
            return jsonify({'error': 'The provided URL is not valid or reachable.'}), 400

        # Save data to Redis
        submission_id = redis_client.incr('submission_id')  # Auto-increment ID
        screenshot_path = capture_screenshot(url, submission_id) or ""  # Ensure a valid string
        redis_client.hmset(f'submission:{submission_id}', {
            'url': url,
            'category': category,
            'reason': reason,
            'comment': comment,
            'screenshot': screenshot_path,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'message': 'Thank you for your submission!'})

    # Fetch all submissions from Redis
    submission_keys = redis_client.keys('submission:*')
    submissions = [
        redis_client.hgetall(key) for key in submission_keys
    ]

    # Group submissions by URL
    grouped_submissions = {}
    for submission in submissions:
        url = submission['url']
        if url not in grouped_submissions:
            grouped_submissions[url] = []
        grouped_submissions[url].append(submission)

    return render_template('index.html', grouped_submissions=grouped_submissions)

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

    # Get the most recent submission's screenshot
    latest_screenshot = submissions[0]['screenshot'] if submissions and 'screenshot' in submissions[0] else None

    return render_template('details.html', url=url, submissions=submissions, latest_screenshot=latest_screenshot)

if __name__ == '__main__':
    app.run(debug=True)