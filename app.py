from flask import Flask, render_template
from markupsafe import escape

app = Flask(__name__)
app.debug = True

@app.route("/home")
def index():
    return render_template("index.html")

@app.route("/database")
def database():
    return render_template("database.html")

@app.route("/reviews")
def reviews():
    return render_template("reviews.html")

@app.route("/orders")
def orders():
    return render_template("orders.html")

@app.route("/hueta")
def hueta():
    return render_template("hueta.html")

if __name__ == "__main__":
    app.run(debug=True)