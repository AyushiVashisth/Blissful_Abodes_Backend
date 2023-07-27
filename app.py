from flask import Flask, request, jsonify, session
from pymongo import MongoClient
from flask_cors import CORS
from bson.objectid import ObjectId
import bcrypt

app = Flask(__name__)
CORS(app) 
app.secret_key = "ayushi"  
app.config['SESSION_TYPE'] = 'filesystem'  

MONGO_URI = "mongodb+srv://ayushi:ayushivashisth@cluster0.xzliwxo.mongodb.net/?retryWrites=true&w=majority"  
DB_NAME = "blissful_abodes"  

# MongoDB setup
def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

# Utility functions for password hashing and verification
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(stored_hash, password):
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

# Property class
class Property:
    def __init__(self, name, hostingSince, status, about, description, price, image, profile, property_name, availability,rating, city, state, date):
        self._id = ObjectId()
        self.name = name
        self.hostingSince=hostingSince
        self.about = about
        self.description = description
        self.price = price
        self.status = status
        self.image = image
        self.profile=profile
        self.property_name=property_name
        self.availability=availability
        self.rating=rating
        self.city=city
        self.state=state
        self.date=date

# Booking class
class Booking:
    def __init__(self,property_img, property_id, property_name, price, property_city, checkInDate, checkOutDate):
        self._id = ObjectId()
        self.property_id = property_id
        self.property_name = property_name
        self.property_price = price
        self.property_city = property_city
        self.property_image=property_img,
        self.checkInDate = checkInDate
        self.checkOutDate = checkOutDate

# Routes
@app.route("/")
def index():
    return "Server running"

@app.route('/signup/host', methods=['POST'])
def host_signup():
    # implementation for host signup
    db = get_db()
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if db.hosts.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 400
    hashed_password = hash_password(password)

    host_id = db.hosts.insert_one({
        "email": email,
        "password": hashed_password,
    }).inserted_id

    return jsonify({"host_id": str(host_id)}), 201

@app.route('/signup/guest', methods=['POST'])
def guest_signup():
    # implementation for guest signup
    db = get_db()
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if db.guests.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = hash_password(password)

    guest_id = db.guests.insert_one({
        "email": email,
        "password": hashed_password,
    }).inserted_id

    return jsonify({"guest_id": str(guest_id)}), 201

@app.route('/login/host', methods=['POST'])
def host_login():
    # implementation for host login
    db = get_db()
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    host = db.hosts.find_one({"email": email})

    if not host:
        return jsonify({"error": "Invalid credentials"}), 401

    if not verify_password(host['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session['user_role'] = 'host'

    return jsonify({"message": "Host login successful", "host_id": str(host["_id"])}), 200

@app.route('/login/guest', methods=['POST'])
def guest_login():
    # implementation for guest login
    db = get_db()
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    guest = db.guests.find_one({"email": email})

    if not guest:
        return jsonify({"error": "Invalid credentials"}), 401

    if not verify_password(guest['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session['user_role'] = 'guest'

    return jsonify({"message": "Guest login successful"}), 200

@app.route('/logout', methods=['POST'])
def logout():
    # implementation for logout
    session.pop('user_role', None)
    return jsonify({"message": "Logout successful"}), 200

@app.route("/properties", methods=["GET"])
def get_all_properties():
    db = get_db()
    # implementation for getting all properties
    sort_by = request.args.get('sort_by', 'price')
    sort_order = int(request.args.get('sort_order', 1))
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 9))
    title_filter = request.args.get('property_name', '')
    property_name_filter = request.args.get('property_name', '')
    state_filter = request.args.get('state', '')  # Get the state filter from the query parameters
    availability_filter = request.args.get('availability', '')

    filter_query = {}
    if title_filter:
        filter_query['property_name'] = {'$regex': title_filter, '$options': 'i'}
    if property_name_filter:
        filter_query['propertyType'] = property_name_filter
    if state_filter:
        filter_query['state'] = state_filter

    if availability_filter == 'true':  # Filter based on availability being True
        filter_query['availability'] = True
    elif availability_filter == 'false':  # Filter based on availability being False
        filter_query['availability'] = False

    total_properties = db.properties.count_documents(filter_query)

    total_pages = (total_properties - 1) // per_page + 1

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    skip = (page - 1) * per_page
    limit = per_page

    if skip < 0:
        skip = 0

    properties = db.properties.find(filter_query).skip(skip).limit(limit)

    if sort_by:
        properties = properties.sort(sort_by, sort_order)

    res = []
    for property in properties:
        res.append({
            "id": str(property["_id"]),
            "name": str(property['name']),
            "state": str(property['state']),
            "hostingSince": str(property['hostingSince']),
            "about": str(property['about']),
            "description": str(property['description']),
            "price": str(property['price']),
            "status": str(property['status']),
            "image": str(property['image']),
            "profile": str(property['profile']),
            "property_name": str(property['property_name']),
            "availability": str(property['availability']),
            "rating": str(property['rating']),
            "city": str(property['city']),
            "state": str(property['state']),
            "date": str(property['date']),
        })

    return jsonify(res)

@app.route("/properties/<string:property_id>", methods=["GET"])
def get_property(property_id):
    #  implementation for getting a specific property
    db = get_db()
    property = db.properties.find_one({"_id": ObjectId(property_id)})
    if property:
        res = {
            "id": str(property["_id"]),
            "name": str(property['name']),
            "state": str(property['state']),
            "hostingSince": str(property['hostingSince']),
            "about": str(property['about']),
            "description": str(property['description']),
            "price": str(property['price']),
            "status": str(property['status']),
            "image": str(property['image']), 
            "profile": str(property['profile']),
            "property_name": str(property['property_name']),
            "availability": str(property['availability']),
            "rating": str(property['rating']),
            "city": str(property['city']),
            "state": str(property['state']),
            "date": str(property['date']) 
            
        }
        return jsonify(res)
    return jsonify({"message": "Property not found"}), 404

@app.route("/properties", methods=["POST"])
def create_property():
    #  implementation for creating a property
    db = get_db()
    data = request.get_json()
    # Convert the availability value to a boolean
    # availability = "Available" if bool(data["availability"]) else "Not Available"
    property = Property(
        name=data["name"],
        hostingSince=data["hostingSince"],
        about=data["about"],
        description=data["description"],
        price=data["price"],
        status=data["status"],
        image=data["image"],
        profile=data["profile"],
        property_name=data["property_name"],
        availability=data["availability"],
        rating=data["rating"],
        city=data["city"],
        state=data["state"],
        date=data["date"],
    )
    db.properties.insert_one(property.__dict__)
    return jsonify({"message": "Property created successfully"}), 201


@app.route("/properties/<string:property_id>", methods=["PUT"])
def update_property(property_id):
    db = get_db()
    data = request.get_json()
    # Convert the availability value to a boolean
    data["availability"] = bool(data["availability"])
    db.properties.update_one({"_id": ObjectId(property_id)}, {"$set": data})
    return jsonify({"message": "Property updated successfully"})

@app.route("/properties/<string:property_id>", methods=["DELETE"])
def delete_property(property_id):
    #  implementation for deleting a property
    db = get_db()
    result = db.properties.delete_one({"_id": ObjectId(property_id)})
    if result.deleted_count > 0:
        return jsonify({"message": "Property deleted successfully"})
    return jsonify({"message": "Property not found"}), 404

@app.route("/properties/book", methods=["POST"])
def post_property_to_book_collection():
    #  implementation for posting a property to the book collection
    db = get_db()
    data = request.get_json()
    property_id = data.get('property_id')
    property_name = data.get('property_name')
    property_price = data.get('property_price')
    property_state = data.get('property_state')
    property_image = data.get('property_image') 
    checkInDate = data.get('checkInDate')
    checkOutDate = data.get('checkOutDate')

    booking = Booking(
        property_id=property_id,
        property_name=property_name,
        property_price=property_price,
        property_state=property_state,
        property_image=property_image,  
        checkInDate=checkInDate,
        checkOutDate=checkOutDate
    )
    booking_id = db.book.insert_one(booking.__dict__).inserted_id

    if property_id:
        db.properties.update_one({"_id": ObjectId(property_id)}, {"$set": {"status": False}})

    return jsonify({"booking_id": str(booking_id)}), 201

@app.route("/properties/book", methods=["GET"])
def get_all_book_data():
    #  implementation for getting all booking data
    db = get_db()
    book_data = db.book.find()
    res = []
    for book_entry in book_data:
        res.append({
            "booking_id": str(book_entry["_id"]),
            "property_id": str(book_entry.get("property_id")),
            "property_name": str(book_entry.get("property_name")),
            "property_price": str(book_entry.get("property_price")),
            "property_state": str(book_entry.get("property_state")),
            "property_image":str(book_entry.get("property_image")),
            "checkInDate": str(book_entry.get("checkInDate")),
            "checkOutDate": str(book_entry.get("checkOutDate"))
        })
    return jsonify(res)

@app.route("/properties/book/<string:booking_id>", methods=["GET"])
def get_book_data(booking_id):
    #  implementation for getting a specific booking data
    db = get_db()
    book_entry = db.book.find_one({"_id": ObjectId(booking_id)})
    if book_entry:
        res = {
            "booking_id": str(book_entry["_id"]),
            "property_id": str(book_entry.get("property_id")),
            "property_name": str(book_entry.get("property_name")),
            "property_price": str(book_entry.get("property_price")),
            "property_state": str(book_entry.get("property_state")),
            "property_image":str(book_entry.get("property_image")),
            "checkInDate": str(book_entry.get("checkInDate")),
            "checkOutDate": str(book_entry.get("checkOutDate"))
        }
        return jsonify(res)
    return jsonify({"message": "Booking data not found"}), 404

@app.route("/properties/book/<string:booking_id>", methods=["DELETE"])
def delete_book_data(booking_id):
    # implementation for deleting a booking data
    db = get_db()
    book_entry = db.book.find_one({"_id": ObjectId(booking_id)})
    if book_entry:
        property_id = book_entry.get("property_id")

        result = db.book.delete_one({"_id": ObjectId(booking_id)})
        if result.deleted_count > 0:
            if property_id:
                db.properties.update_one({"_id": ObjectId(property_id)}, {"$set": {"status": True}})
            return jsonify({"message": "Booking data deleted successfully"})
    return jsonify({"message": "Booking data not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)