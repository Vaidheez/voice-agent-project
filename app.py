from flask import Flask, render_template

# Initialize the Flask app
app = Flask(__name__)

# Define a route for the home page
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Run the app in debug mode so it reloads automatically
    app.run(debug=True)