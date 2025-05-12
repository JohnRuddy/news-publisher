from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

@app.context_processor
def inject_current_year():
    """Inject the current year into templates."""
    return {'current_year': datetime.now().year}

@app.route('/')
def home():
    """Render the home page."""
    return render_template('base.html')

if __name__ == '__main__':
    app.run(debug=True)