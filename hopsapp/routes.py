"""Routes for flask app."""  # pylint: disable=cyclic-import
# import hashlib
from hopsapp import app
# from flask import render_template, request, redirect, url_for, flash
from flask import session, request, flash, url_for, redirect, render_template, abort ,g
from flask_sqlalchemy import SQLAlchemy
from hopsapp import db
from hopsapp.models import Beer, Brewery, Store, Customer, Storeowner
from math import cos, asin, sqrt
from sqlalchemy import desc, func
from flask_login import LoginManager, UserMixin, login_user , logout_user , current_user , login_required
from functools import wraps
from operator import itemgetter, attrgetter
# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def find_popular_beers():
    return Beer.query.order_by(desc(Beer.average_popularity)).limit(3)

def find_rare_beers():
    beer_r = Beer.query.order_by(func.random()).all()
    rare_beers = []
    for b in beer_r:
        if b.rarity == 'rare':
            rare_beers.append(b)
    return rare_beers[0:3]

#TODO: finish this to reduce code
# def new_rating(beer):
#     users = beer.total_users + 1 #int
#     ratings = beer.total_ratings + int(float(input_rating)) # int
#     new_average_popularity = ratings/users #float

#create a percentage of users that rate this beer
#if more than 50% of users have had the beer, it is considered common
#between 25% and 50% is considered uncommon
# less than 25% is consdiered rare
def rarity_system(beer):
    users = Customer.query.all()
    beer_users = beer.total_users
    total_users = users + beer_users
    #precent
    p = beer_users/total_users
    if 0.5 < p <= 1:
        return "common"
    elif 0.25 <= p <= 0.5 :
        return "uncommon"
    elif p < 0.25:
        return "rare"


def staff_beers():
    return Beer.query.limit(3)

def distance(lat1, lon1, lat2, lon2):
        conv_fac = 0.621371 # conversion factor
        p = 0.017453292519943295     #Pi/180
        a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
        kil_m = 12742 * asin(sqrt(a)) #2*R*asin...
        miles = kil_m * conv_fac
        miles = float("{0:.1f}".format(miles))
        return miles

def distance_from_user(beer, coord):

    coordinate = coord.split(' ')
    user_lat = float(coordinate[0])
    user_lon = float(coordinate[1])

    distances = []

    for store in beer.stores:
        d = distance(user_lat, user_lon, store.lat, store.lon)
        distances.append((beer,store,d))

    sorted_distances = sorted(distances, key=itemgetter(2))
    return sorted_distances

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login'))
    return wrap

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'GET':
        beers = Beer.query.order_by(Beer.brewery_id)
        beer_c = find_popular_beers()
        rare_beers = find_rare_beers()

        beer_s = staff_beers()
        return render_template("home.html", beers=beers, beer_c=beer_c, rare_beers=rare_beers, beer_s=beer_s)

        # return render_template("home.html", beers=beers, beer_c=beer_c, rare_beers=rare_beers)

    elif request.method == 'POST':
        if request.form['submit'] == 'browse':
            beer_list = []
            beer_type = request.form['style']
            # refer to the state of the brewery in which the beer originates
            state = request.form['state']
            rarity = request.form['rarity']
            seasonal = request.form['availability']
            if seasonal=="None":
                seasonal = None
            beers = Beer.query.join(Brewery).filter_by(state=state).all()
            for b in beers:
                if (b.beer_type == beer_type) and (b.rarity == rarity) and (b.seasonal == seasonal):
                    beer_list.append(b)
            beer_c = find_popular_beers()
            rare_beers = find_rare_beers()
            beer_s = staff_beers()
            return render_template("home.html", beers=beer_list, beer_c=beer_c, rare_beers=rare_beers, beer_s=beer_s)
        elif request.form['submit'] == 'search':
           searchtype = request.form['searchtype']
           text_search = request.form['text_search']
           # coordinates added
           coordinates = request.form['location']
           print(text_search)
           if searchtype == 'beer':
               return redirect(url_for('beerprofile', name=text_search, coord = coordinates))
           if searchtype == 'brewery':
               return redirect (url_for('breweryprofile', name=text_search))
           if searchtype == 'store':
               return (url_for('storeprofile', name=text_search))

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@login_manager.user_loader
def load_user(user_id):
    return Customer.query.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        customer = Customer.query.filter_by(email=email, password=password).first()
        if customer is None:
            error = 'Failed Login Attempt'
            return render_template('login.html', error=error)
        login_user(customer)
        flash('Logged in successfully')
        return redirect(url_for('home'))

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        if request.form['submit']=="register":
            if request.form['confirm_password'] != request.form['password']:
                flash('Passwords DO NOT Match')
                return render_template("register.html")
            name = request.form['name']
            phone = request.form['phone']
            email = request.form['email']
            password = request.form['password']
            new_customer = Customer(name=name, phone=phone, email=email, password=password)
            try:
                db.session.add(new_customer)
                db.session.commit()
                flash('Cheers! ' + name)
                return redirect(url_for('home'))
            except:
                error = 'Ooops! We apologize! There was an error in your attempt to register.'
                return redirect(url_for('home'))

@app.route('/beerprofile', methods=['GET', 'POST'])
#value for new rating is new_rating
def beerprofile():
    if request.method == 'GET':
        search = request.args['name']
        beer = Beer.query.filter_by(name=search).first()
        coord = request.args['coord']

        # print('coord from beerprofile: '+ str(coord))
        # store_component = distance_from_user(beer)
        # change made hare
        # return render_template("beerprofile.html",beer=beer,all_component=store_component)
        #distances = distance_from_user(beer)
        distances = distance_from_user(beer, coord)
        return render_template("beerprofile.html",beer=beer,distances=distances)

    elif request.method == 'POST':
        if request.form['submit']=="rating":
            search = request.args['name']
            beer = Beer.query.filter_by(name=search).first()
            coord = request.args['coord']
            distances = distance_from_user(beer, coord)

            input_rating = request.form['new_rating']

            users = beer.total_users + 1 #int
            ratings = beer.total_ratings + int(float(input_rating)) # int
            new_average_popularity = ratings/users #float


            beer.total_users=users
            beer.total_ratings=ratings
            beer.average_popularity = new_average_popularity
            beer.rarity = rarity_system(beer)

            #TODO: fix this line so that we don't need all these lines of code
            # beer.average_popularity = new_rating(beer)

            db.session.commit()

            return render_template("beerprofile.html", beer=beer, distances=distances)

        elif request.form['submit']== "search":
            searchtype = request.form['searchtype']
            text_search = request.form['text_search']
            coordinates = request.form['location']
            if searchtype == 'beer':
                return redirect(url_for('beerprofile', name=text_search, coord = coordinates))
            if searchtype == 'brewery':
                return redirect(url_for('breweryprofile', name=text_search))
            if searchtype == 'store':
                return redirect(url_for('storeprofile', name=text_search))

@app.route('/breweryprofile', methods=['GET', 'POST'])
def breweryprofile():
    if request.method == 'GET':
        search = request.args['name']
        brewery = Brewery.query.filter_by(name=search).first()
        return render_template("breweryprofile.html", brewery=brewery)
    elif request.method == 'POST':
        searchtype = request.form['searchtype']
        text_search = request.form['text_search']
        coordinates = request.form['location']
        if searchtype == 'beer':
            return redirect(url_for('beerprofile', name=text_search, coord = coordinates))
        if searchtype == 'brewery':
            return redirect(url_for('breweryprofile', name=text_search))
        if searchtype == 'store':
            return redirect(url_for('storeprofile', name=text_search))

@app.route('/storeprofile', methods=['GET', 'POST'])
def storeprofile():
    if request.method == 'GET':
        search = request.args['name']
        store = Store.query.filter_by(name=search).first()
        return render_template("storeprofile.html", store=store)
    elif request.method == 'POST':
        searchtype = request.form['searchtype']
        text_search = request.form['text_search']
        coordinates = request.form['location']
        if searchtype == 'beer':
            return redirect(url_for('beerprofile', name=text_search, coord = coordinates))
        if searchtype == 'brewery':
            return redirect(url_for('breweryprofile', name=text_search))
        if searchtype == 'store':
            return redirect(url_for('storeprofile', name=text_search))

#Error handler
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(405)
def not_found_error(error):
    return render_template('405.html'), 405

@app.errorhandler(400)
def not_found_error(error):
    return render_template('400.html'), 400


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(debug=True)
