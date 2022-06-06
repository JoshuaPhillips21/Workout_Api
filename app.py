from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow 
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.congif["SQLALCHEMY_TRACK_MODIFICATION"] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
CORS(app)

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    workout = db.relationship('Workout', backref='workout', cascade='all, delete, delete-orphan')

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Workout(db.Model):
    __tablename__ = 'workout'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String, nullable=False, unique=False)
    weight = db.Column(db.String, nullable=False, unique=False)
    reps = db.Column(db.String, nullable=False, unique=False)
    muscle = db.Column(db.String, nullable=False, unique=False)

    def __init__(self, user_id, title, weight, reps, muscle):
        self.user_id = user_id
        self.title = title
        self.weight = weight
        self.reps = reps
        self.muscle = muscle

class WorkoutSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'title', 'weight', 'reps', 'muscle')

workout_schema = WorkoutSchema()
multiple_workout_schema = WorkoutSchema(many=True)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'password', 'workout')
    workout = ma.Nested(multiple_workout_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

@app.route('/user/add', methods=['POST'])
def add_user(): 
    print(request.get_json(), 'TEST')

    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')
    possible_duplicate = db.session.query(User).filter(User.username == username).first()

    if possible_duplicate is not None:
        return jsonify('Error: the username is already in use.')

    encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username, encrypted_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify("Let's get SWOLE")

@app.route('/user/authenticate', methods=["POST"])
def authenticate_user():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')
    
    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    user = db.session.query(User).filter(User.username == username).first()

    if user is None:
        return jsonify('User NOT verified')
    if bcrypt.check_password_hash(user.password, password) == False:
        return jsonify('Password NOT verified')

    return jsonify('User has been verified')


@app.route('/users', methods=["GET"])
def get_users():
        all_users = db.session.query(User).all()
        return jsonify(multiple_user_schema.dump(all_users))

@app.route('/user/<id>', methods=["GET"])
def get_user(id):
    user = User.query.get(id)
    return user_schema.jsonify(user)

@app.route('/user/<id>', methods=["DELETE"])
def user_delete(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()

    return "User is no longer swole"

# Workouts
@app.route('/workout/add', methods=["POST"])
def add_workout():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()

    user_id = post_data.get('user_id')
    title = post_data.get('title')
    weight = post_data.get('weight')
    reps = post_data.get('reps')
    muscle = post_data.get('muscle')

    new_workout = Workout(user_id, title, weight, reps, muscle)

    db.session.add(new_workout)
    db.session.commit()


    return jsonify('A new workout has been created')

@app.route('/workout', methods=["GET"])
def get_workouts():
    all_workouts = db.session.query(Workout).all()

    return jsonify(multiple_workout_schema.dump(all_workouts))

@app.route('/workout/delete/<id>', methods=["DELETE"])
def delete_workout(id):
    workout = db.session.query(Workout).filter(Workout.id == id).first()
    db.session.delete(workout)
    db.session.commit()

    return jsonify('The workout has been deleted')

@app.route('/workout/update/<id>', methods={"PUT", "PATCH"})
def update_workout_by_id(id):
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    title = post_data.get('title')
    weight = post_data.get('weight')
    reps = post_data.get('reps')
    muscle = post_data.get('muscle')
    user_id = post_data.get('user_id')

    workout = db.session.query(Workout).filter(Workout.id == id).first()


    if title != None:
        workout.title = title
    if weight != None:
        workout.weight = weight
    if reps != None:
        workout.reps = reps

    db.session.commit()
    return jsonify('Your workout has been updated')

if __name__ == "__main__":
    app.run(debug=True)
