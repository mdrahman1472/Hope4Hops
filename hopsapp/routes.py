"""Routes for flask app."""  # pylint: disable=cyclic-import
import hashlib
from flask import render_template
from flask import request
from hopsapp import app


# @app.route('/', methods=['GET'])
@app.route('/')
def home():
    return render_template("home.html")  #insert name of template here

# @app.route('/about')
# def about():
#     return render_template("")  #insert name of template here

if __name__ == "__main__":
  app.run(debug=True)