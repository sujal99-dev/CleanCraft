"""CleanCraft UI-only Flask preview.

This application displays the approved web design. It intentionally DOES NOT
upload, clean, generate, or model data; connect backend services later.
"""
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
@app.route('/index.html')
def home():
    return render_template('index.html', page='home')


@app.route('/generate')
@app.route('/generate.html')
def generate():
    return render_template('generate.html', page='generate')


@app.route('/upload')
@app.route('/upload.html')
def upload():
    return render_template('upload.html', page='upload')


@app.route('/analysis')
@app.route('/analysis.html')
def analysis():
    return render_template('analysis.html', page='analysis')


@app.route('/cleaning')
@app.route('/cleaning.html')
def cleaning():
    return render_template('cleaning.html', page='cleaning')


@app.route('/recommendations')
@app.route('/recommendations.html')
def recommendations():
    return render_template('recommendations.html', page='recommendations')


@app.route('/report')
@app.route('/report.html')
def report():
    return render_template('report.html', page='report')


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
