from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///water_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Water Intake Model
class WaterIntake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    glasses = db.Column(db.PickleType, default=[])  # List of empty glasses
    liters = db.Column(db.Float, default=0.0)

    user = db.relationship('User', backref=db.backref('water_intakes', lazy=True))

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Welcome to the Water Drinking Tracker API!"

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    if not email and not phone:
        return jsonify({"message": "Email or phone number is required"}), 400

    # Check if user exists already
    if User.query.filter((User.email == email) | (User.phone == phone)).first():
        return jsonify({"message": "User already exists"}), 400

    user = User(email=email, phone=phone, password=password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    identifier = data.get('identifier')  # email or phone
    password = data.get('password')

    # Check for valid identifier
    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()

    if not user or user.password != password:
        return jsonify({"message": "Invalid credentials"}), 400

    return jsonify({"message": "Login successful", "user_id": user.id}), 200

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    phone = data.get('phone')
    new_password = data.get('new_password')

    user = User.query.filter_by(phone=phone).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    user.password = new_password
    db.session.commit()

    return jsonify({"message": "Password reset successful"}), 200

@app.route('/get_water_intake', methods=['POST'])
def get_water_intake():
    data = request.get_json()
    user_id = data.get('user_id')
    date_str = data.get('date')

    try:
        # Clean date string and convert to date object
        date_str_clean = date_str.split("T")[0]
        date = datetime.strptime(date_str_clean, "%Y-%m-%d").date()

        # Query for the user's water intake for the given date
        water_intake = WaterIntake.query.filter_by(user_id=user_id, date=date).first()

        if not water_intake:
            # If no data exists, return empty/default glasses
            glasses_data = [{"isEmpty": False, "amount": "250ml"} for _ in range(8)]
            return jsonify({"glasses": glasses_data, "liters": 0.0}), 200

        # Return saved data
        return jsonify({
            "glasses": water_intake.glasses,
            "liters": water_intake.liters
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Failed to fetch water intake", "error": str(e)}), 500

@app.route('/update_water_intake', methods=['POST'])
def update_water_intake():
    data = request.get_json()
    user_id = data.get('user_id')
    date_str = data.get('date')
    glasses = data.get('glasses')
    liters = data.get('liters')

    try:
        # Clean date string and convert to date object
        date_str_clean = date_str.split("T")[0]
        date = datetime.strptime(date_str_clean, "%Y-%m-%d").date()

        # Check if a record already exists
        water_intake = WaterIntake.query.filter_by(user_id=user_id, date=date).first()

        if water_intake:
            # Update existing record
            water_intake.glasses = glasses
            water_intake.liters = liters
        else:
            # Create a new record
            new_intake = WaterIntake(user_id=user_id, date=date, glasses=glasses, liters=liters)
            db.session.add(new_intake)

        db.session.commit()
        return jsonify({"message": "Water intake updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Failed to update water intake", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, debug=True)
