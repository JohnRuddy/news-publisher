from flask import render_template, request, redirect, url_for
from . import app

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.get('data')
    # Process the data here
    return redirect(url_for('home'))