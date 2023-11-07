from flask import Flask, render_template, request, jsonify, Response
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, JWTManager, set_access_cookies, set_refresh_cookies
from flask_cors import CORS
from database import Database
from datetime import timedelta

import json

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
jwt = JWTManager(app)
#CORS(app)
CORS(app)


def connect():
    neo4j_uri = 'neo4j+ssc://6b38eb4f.databases.neo4j.io:7687'
    neo4j_user = 'neo4j'
    neo4j_password = 'nZxbso28ztGPFeq2_kfTUZ26LvrvZLhky-3ePAZFISY'
    database = 'neo4j'
    return Database(neo4j_uri, neo4j_user, neo4j_password, database)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login", methods=["GET"])
def login_get():
    return render_template('login.html')

@app.route("/login", methods=["POST"])
def login_post():
    try:
        db = connect()
        username, status = db.login(request)
        if status == 200:
            print(username)
            access_token = create_access_token(identity=username)
            return Response(status=200, response=json.dumps({'access_token': access_token}), mimetype='application/json')
            #return jsonify({'access_token': access_token})
    except:
        return Response(status=400)

@app.route("/register", methods=["GET"])
def register_get():
    return render_template('register.html')

@app.route("/register", methods=["POST"])
def register_post():
    try:   
        db = connect()
        message, status = db.register(request)
        return Response(status=status, mimetype='application/json')
    except:
        return Response(status=400)
    

@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
    

@app.route("/mytrainings", methods=["GET"])
def mytrainings_get():
    return render_template("mytrainings.html") 

@app.route("/mytrainings_protected", methods=["GET"])
@jwt_required()
def mytrainings_get_protected():
    try:
        db = connect()
        username = get_jwt_identity()
        myTrainings = db.getMyTrainings(username)
        followed = db.getFollowed(username)
        print(myTrainings, followed)
        return Response(status=200, response=json.dumps({'myTrainings': myTrainings, 'followed': followed}), mimetype='application/json') 
    except:
        return Response(status=400)

@app.route("/mytrainings", methods=["POST"])
@jwt_required()
def mytrainings_post():
    try:
        db = connect()
        username = get_jwt_identity()
        message, status = db.addTraining(request, username)
        return Response(status=status)
    except:
        return Response(status=400)
    
@app.route("/mytrainings/delete/<int:id>", methods=["DELETE"])
@jwt_required()
def mytainings_delete(id):
    try:
        db = connect()
        username = get_jwt_identity()
        db.deleteMyTraining(username, id)
        return Response(status=200)
    except:
        return Response(status=400)
    
@app.route("/othertrainings", methods=["GET"])
def othertrainings_get():
    return render_template('othertrainings.html')

@app.route("/othertrainings_protected", methods=["GET"])
@jwt_required()
def othertrainings_get_protected():
    try:
        db = connect()
        username = get_jwt_identity()
        otherTrainings = db.getOtherTrainings(username)
        
        print(otherTrainings)
        return Response(status=200, response=json.dumps({'otherTrainings': otherTrainings}), mimetype='application/json') 
    except:
        return Response(status=400)

@app.route("/exercises", methods=["GET"])
def exercises_get():
    return render_template('exercises.html')

@app.route("/exercises", methods=["POST"])
@jwt_required()
def exercises_post():
    try:
        db = connect()
        username = get_jwt_identity()
        message, status = db.addExercise(request, username)
        return Response(status=status)
    except:
        return Response(status=400)
    
@app.route("/exercises_protected", methods=["GET"])
@jwt_required()
def exercises_get_protected():
    try:
        db = connect()
        username = get_jwt_identity()
        exercises = db.getExercises(username)
        
        return Response(status=200, response=json.dumps(exercises), mimetype='application/json') 
    except:
        return Response(stats=400)

@app.route("/exercises/delete/<int:id>", methods=["DELETE"])
@jwt_required()
def exercises_delete(id):
    try:
        db = connect()
        username = get_jwt_identity()
        db.deleteExercises(username, id)
        return Response(status=200)
    except:
        return Response(status=400)

@app.route("/training/<int:id>", methods=["GET"])
def training_get(id):
    return render_template('training.html', training_id = id)

@app.route("/training/exercises/<int:id>", methods=["GET"])
@jwt_required()
def training_get_protected(id):
    try:
        db = connect()
        username = get_jwt_identity()
        exercises = db.getExercisesInTraining(id, username)
        print(exercises)
        return Response(status=200, response=json.dumps(exercises), mimetype='application/json')
    except:
        return Response(status=400)

@app.route("/training/exercisesUnadded/<int:id>", methods=["GET"])
@jwt_required()
def training_unadded_get_protected(id):
    try:
        db = connect()
        username = get_jwt_identity()
        exercises = db.getUnaddedExercises(id, username)
        print(exercises)
        return Response(status=200, response=json.dumps(exercises), mimetype='application/json')
    except:
        return Response(status=400)

@app.route("/training", methods=["POST"])
@jwt_required()
def training_post():
    try:
        db = connect()
        username = get_jwt_identity()
        message, status = db.addExerciseToTraining(request, username)
        return Response(status=status)
    except:
        return Response(status=400)

@app.route("/training/update/", methods=["PUT"])
@jwt_required()
def training_exercise_put():
    try:
        db = connect()
        username = get_jwt_identity()
        message, status = db.updateTraining(request, username)
        return Response(status=status)
    except:
        return Response(status=400)
    
@app.route("/follow", methods=["POST"])
@jwt_required()
def follow_post():
    try:
        db = connect()
        username = get_jwt_identity()
        message, status = db.followTraining(request, username)
        return Response(status=status)
    except:
        return Response(status=400)

@app.route("/unfollow", methods=["PUT"])
@jwt_required()
def unfollow():
    try:
        db = connect()
        username = get_jwt_identity()
        message, status = db.unfollowTraining(request, username)
        return Response(status=status)
    except:
        return Response(status=400)
    
@app.route("/checkowner", methods=["POST"])
@jwt_required()
def checkowner():
    try:
        db = connect()
        username = get_jwt_identity()
        owner_username, status = db.checkOwner(request, username)
        if username == owner_username:
            return Response(status=status, response=json.dumps({'IsOwner': True}), mimetype='application/json')
        else:
            return Response(status=status, response=json.dumps({'IsOwner': False}), mimetype='application/json')
    except:
        return Response(status=400)
    
