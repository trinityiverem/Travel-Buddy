import json
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import uuid
import requests as rq
mongo_db_uri = "mongodb+srv://trinityy239:temi123@cluster0.xzrenpi.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(mongo_db_uri);
db = client['Cluster0']
users = db.users
trips = db.trips

app = Flask(__name__)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)

def tripIdValidator(tripID, username):
    tripsList = db["trips"].find({})
    for trip in tripsList:
        if (trip["_id"] == tripID):
            if username in trip["attenders"]:
                return {"match":True, "user":True}
            else:
                return {"match":True, "user":False}
    return {"match":False, "user":False}

def loginValidation(username, password):
    user = db["users"].find_one({"username":username,"password":password})
    return user


@app.route('/', methods=['GET'])
def index():

    return

@app.route('/seeUsers', methods=['GET'])
def users():
    usersList = db["users"].find({})
    users = [user for user in usersList]  # Convert the cursor to a list of dictionaries
    return jsonify(users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle the form submission here and save the data to the database
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the username already exists in the database
        if users.find_one({"username": username}):
            return "User already exists. Please choose a different username."

        # Generate a unique ID for the user
        user_id = uuid.uuid4().hex

        # Create a new user document
        user_document = {
            "_id": user_id,
            "username": username,
            "password": password,
            "name": name
        }

        # Save the user document to the 'users' collection in MongoDB
        users.insert_one(user_document)

        # Save the data to the database (you can use your existing code for this)
        # Example: db["users"].insert_one({"username": username, "password": password})
        return f"Registered user: {username}"  # Return a simple success message
    return render_template('registration_form.html')

    #  body = request.get_json()
    #  if body:
    #    if(body.get("username") and body.get("password")):
    #        usersList = db["users"].find({})
    #      for user in usersList:
    #            if (user["username"] == body["username"]):
    #                return json.dumps({'Status': 'Error','Message': 'User exists'})
    #        new_user = db["users"].insert_one({"_id":uuid.uuid4().hex,"username":body["username"],"password":body["password"]})
    #       return json.dumps({'Status': 'OK','Message': 'User Created'})
    # return json.dumps({'Status': 'Error','Message': 'Missing Body'})


@app.route('/createTrip', methods=['GET', 'POST'])
def suggest_trip():
    if request.method == 'POST':
        country = request.form.get('Country')
        region = request.form.get('Region')
        city = request.form.get('City')
        username = request.form.get('username')
        password = request.form.get('password')
        attenders = request.form.get('attenders')
        trip_id = request.form.get('tripID')

        trip_document = {
            "_id": trip_id,
            "username": username,
            "password": password,
            "Country": country,
            "Region": region,
            "City": city,
            "attenders": [username]
        }

        trips.insert_one(trip_document)
        return f"Registered trip: {trip_id}"
    return render_template('suggestTrip_form.html')




@app.route('/seeTrips', methods=['GET'])
def see_trips():
    trips = db["trips"].find({})
    listList = [trip for trip in trips]
    return listList

@app.route('/seeMyTrips', methods=['GET'])
def see_my_trips():
    username = request.args.get("username")
    password = request.args.get("password")

    if username and password:
        tripID = request.args.get("tripID")  # Retrieve the tripID from query parameters
        trip = tripIdValidator(tripID, username)
        if trip["match"]:
            myTrips = []
            tripsList = db["trips"].find({})
            for trip in tripsList:
                if username in trip["attenders"]:
                    myTrips.append(trip)
            return jsonify(myTrips)  # Return the results as JSON
        else:
            return "User is not authorized to view this trip."
    return "Missing Parameters."


@app.route('/forecastApi', methods=['GET'])
def forecast_api():
    args = request.args
    if args:
        if(args.get("Country") and args.get("Region") and args.get("City")):
            Country = args["Country"]
            Region = args["Region"]
            City = args["City"]
            URL = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{Country}%20{Region}%20{City}%20Clifton?unitGroup=metric&key=KJK7F6X2JBTLY6BJYTP36MVVZ&contentType=json"
            r = rq.get(url = URL)
            if r.status_code==400:
                return "unvalid location"
            return r.json()
    return "missing parameters"

@app.route('/joinTrip', methods=['GET', 'POST'])
def join_to_trip():
    if request.method == 'POST':
        # Handle the join trip request here and add the user to the trip in the database
        tripID = request.form.get("tripIdInput")
        username = request.form.get("usernameInput")

        if username and tripID:
            # Check if the user exists in the database
            user = db["users"].find_one({"username": username})
            if user:
                match = tripIdValidator(tripID, username)
                if match["match"]:
                    if not match["user"]:
                        db["trips"].update_one({"_id": tripID}, {"$push": {"attenders": [username]}})
                        return "You are now among the attenders of that trip."
                    else:
                        return "You are already among the attenders of that trip."
                else:
                    return "Invalid trip ID."
            else:
                return "Username is Wrong."
        else:
            return "Missing parameters."

    # Fetch the trips and render the trips.html template
    tripsList = db["trips"].find({})
    return render_template('trips.html', trips=tripsList)



@app.route('/leaveTrip', methods=['POST', 'GET'])
def leave_trip():
    if request.method == 'POST':
        # Handle the join trip request here and add the user to the trip in the database
        tripID = request.form.get("removeTripIdInput")
        username = request.form.get("removeUsernameInput")

        if username and tripID:
            # Check if the user exists in the database
            user = db["users"].find_one({"username": username})
            if user:
                match = tripIdValidator(tripID, username)

                if match["user"]:
                    db["trips"].update_one({"_id": tripID}, {"$pull": {"attenders": [username]}})
                    return "You are now removed from that trip."
                else:
                    return "You are aren't a part of that trip."

            else:
                return "Username is Wrong."
        else:
            return "Missing parameters."

    # Fetch the trips and render the trips.html template
    tripsList = db["trips"].find({})
    return render_template('leavetrip_form.html', trips=tripsList)

app.run()


