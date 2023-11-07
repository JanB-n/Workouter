import uuid
import binascii
import os
import sys
import hashlib
from neo4j import GraphDatabase

class Database():
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password) )
        self.driver.verify_connectivity()
        self.database = database

    def close(self):
        self.driver.close()

    def register(self, request):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username:
            return {'username': 'This field is required.'}, 400
        if not password:
            return {'password': 'This field is required.'}, 400

        def get_user_by_username(tx, username):
            return tx.run(
                '''
                MATCH (user:User {username: $username}) RETURN user
                ''', {'username': username}
            ).single()
        
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_user_by_username, username)
            if result and result.get('user'):
                return {'username': 'username already in use'}, 409

        def create_user(tx, username, password):
            return tx.run(
                '''
                CREATE (user:User {id: $id, username: $username, password: $password, api_key: $api_key}) RETURN user
                ''',
                {
                    'id': str(uuid.uuid4()),
                    'username': username,
                    'password': hash_password(username, password),
                    'api_key': binascii.hexlify(os.urandom(20)).decode()
                    
                }
            ).single()
        
        with self.driver.session(database="neo4j") as session:
            results = session.write_transaction(create_user, username, password)
            user = results['user']
            print(user)
        
        return {'register': 'operation was a success!'}, 201

    def login(self, request):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username:
            return {'username': 'This field is required.'}, 400
        if not password:
            return {'password': 'This field is required.'}, 400

        def get_user_by_username(tx, username):
            return tx.run(
                '''
                MATCH (user:User {username: $username}) RETURN user
                ''', {'username': username}
            ).single()
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_user_by_username, username)

        try:
            user = result['user']
        except KeyError:
            return {'username': 'username does not exist'}, 400

        expected_password = hash_password(user['username'], password)
        if user['password'] != expected_password:
            return {'password': 'wrong password'}, 400
        return user['username'], 200
    
    def addTraining(self, request, username):
        data = request.get_json()
        training_name = data.get('training_name')
        if not training_name:
            return {'training_name': 'This field is required.'}, 400
        
        def add_training_for_user(tx, username, training_name):
            return tx.run(
                '''
                MATCH (user:User {username: $username})
                CREATE (t:Training {trainingname: $training_name}) 
                CREATE (user)-[:ADDED_TRAINING]->(t)
                ''', {'username': username, "training_name": training_name}
            )
        with self.driver.session(database="neo4j") as session:
            result = session.write_transaction(add_training_for_user, username, training_name)
        
        return {'training_name': 'operation was a success!'}, 201
    
    def getMyTrainings(self, username):
        def get_trainings_for_user(tx, username):
            result = tx.run(
                '''
                MATCH (user:User {username: $username})-[:ADDED_TRAINING]->(t:Training)
                RETURN ID(t), t.trainingname
                ORDER BY t.trainingname
                ''', {'username': username}
            )
            return list(result)
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_trainings_for_user, username)
            
        
        result = [row.data() for row in result]
        return result
    
    def getFollowed(self, username):
        def get_followed_for_user(tx, username):
            result = tx.run(
                '''
                MATCH (user:User {username: $username})-[:FOLLOWS]->(t:Training)
                RETURN ID(t), t.trainingname
                ORDER BY t.trainingname
                ''', {'username': username}
            )
            return list(result)
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_followed_for_user, username)
        
        result = [row.data() for row in result]
        return result
    
    def getOtherTrainings(self, username):
        def get_trainings_for_user(tx, username):
            result = tx.run(
                '''
                MATCH (user:User {username: $username})-[:FOLLOWS]->(excluded:Training)
                WITH collect(excluded) as excluded
                MATCH (user:User)-[:ADDED_TRAINING]->(t:Training)
                WHERE NOT user.username = $username
                WITH excluded, t, collect(t) as trainings
                WHERE NONE (t in trainings where t in excluded)
                RETURN ID(t), t.trainingname
                ORDER BY t.trainingname
                ''', {'username': username}
            )
            return list(result)
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_trainings_for_user, username)
            
        
        result = [row.data() for row in result]
        return result
    
    def addExercise(self, request, username):
        data = request.get_json()
        exercise_name = data.get('exercise_name')
        if not exercise_name:
            return {'exercise_name': 'This field is required.'}, 400
        
        def add_exercise_for_user(tx, username, exercise_name):
            return tx.run(
                '''
                MATCH (user:User {username: $username})
                CREATE (e:Exercise {exercisename: $exercise_name}) 
                CREATE (user)-[:ADDED_EXERCISE]->(e)
                ''', {'username': username, "exercise_name": exercise_name}
            )
        with self.driver.session(database="neo4j") as session:
            result = session.write_transaction(add_exercise_for_user, username, exercise_name)
        
        return {'exercise_name': 'operation was a success!'}, 201
    
    def getExercises(self, username):
        def get_exercises_for_user(tx, username):
            result = tx.run(
                '''
                MATCH (user:User {username: $username})-[:ADDED_EXERCISE]->(e:Exercise)
                RETURN ID(e), e.exercisename
                ORDER BY e.exercisename
                ''', {'username': username}
            )
            return list(result)
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_exercises_for_user, username)
        user_exercises = [row.data() for row in result]

        def get_base_exercises(tx):
            result = tx.run(
                '''
               MATCH (e:Exercise) 
               WHERE NOT ()-[:ADDED_EXERCISE]->(e) 
               RETURN ID(e), e.exercisename
               ORDER BY e.exercisename
                '''
            )
            return list(result)
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_base_exercises)
        base_exercises = [row.data() for row in result]
        return {'user_exercises': user_exercises, 'base_exercises': base_exercises}
    
    def getExercisesInTraining(self, training_id, username):
        def get_training_exercises(tx):
            result = tx.run(
                '''
               MATCH (n:Training)-[:INCLUDES]->(e:Exercise) 
               WHERE ID(n) = $training_id
               RETURN ID(e), e.exercisename
               ORDER BY e.exercisename
                ''', {'training_id': training_id}
            )
            return list(result)
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_training_exercises)
        exercises = [row.data() for row in result]
        return exercises
    
    def getUnaddedExercises(self, training_id, username):
        def get_unadded_exercises(tx, username, training_id):
            result = tx.run(
                '''
                MATCH (t:Training)-[:INCLUDES]->(excluded:Exercise)
                WHERE ID(t) = $training_id
                WITH collect(excluded) as excluded 
                MATCH (u:User {username: $username})-[:ADDED_EXERCISE]->(e:Exercise) 
                WITH excluded,e, u, collect(e) as exercises
                WHERE NONE (e in exercises where e in excluded)
                RETURN ID(e), e.exercisename
                ORDER BY e.exercisename
                UNION
                MATCH (t:Training)-[:INCLUDES]->(excluded:Exercise)
                WHERE ID(t) = $training_id
                WITH collect(excluded) as excluded 
                MATCH (e:Exercise) WHERE NOT ()-[:ADDED_EXERCISE]->(e)
                WITH excluded, e, collect(e) as exercises
                WHERE NONE (e in exercises where e in excluded)
                RETURN ID(e), e.exercisename
                ORDER BY e.exercisename
                ''', {'username': username, 'training_id': training_id}
            )
            return list(result)
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(get_unadded_exercises, username, training_id)
        exercises = [row.data() for row in result]
        return exercises
    
    def addExerciseToTraining(self, request, username):
        data = request.get_json()
        training_id = int(data.get('training_id'))
        exercise_id = int(data.get('exercise_id'))
        
        if not exercise_id:
            return {'exercise_id': 'This field is required.'}, 400
        
        if not training_id:
            return {'training_id': 'This field is required.'}, 400
        def add_exercise_for_user(tx, training_id, exercise_id):
            return tx.run(
                '''
                MATCH (t:Training) WHERE ID(t) = $training_id
                MATCH (e:Exercise) WHERE ID(e) = $exercise_id 
                CREATE (t)-[:INCLUDES]->(e)
                ''', {'training_id': training_id, "exercise_id": exercise_id}
            )
        with self.driver.session(database="neo4j") as session:
            result = session.write_transaction(add_exercise_for_user, training_id, exercise_id)
        
        return {'add_exercise_to_training': 'operation was a success!'}, 201
    
    def updateTraining(self, request, username):
        data = request.get_json()
        training_id = int(data.get('training_id'))
        exercise_id = int(data.get('exercise_id'))
        print(training_id, exercise_id)

        def update_training(tx, training_id, exercise_id):
            return tx.run(
                '''
                MATCH (t:Training)-[r:INCLUDES]->(e:Exercise)
                WHERE ID(t) = $training_id AND ID(e) = $exercise_id 
                DELETE r
                ''', {'training_id': training_id, "exercise_id": exercise_id}
            )
        with self.driver.session(database="neo4j") as session:
            result = session.write_transaction(update_training, training_id, exercise_id)
        
        return {'update_training': 'operation was a success!'}, 204
    
    def deleteExercises(self, username, exercise_id):
        def check_exercise_creator(tx, username, exercise_id):
            return tx.run(
                '''
                MATCH (u:User {username: $username})-[:ADDED_EXERCISE]->(e:Exercise)
                WHERE ID(e) = $exercise_id 
                return u
                ''', {'username': username, "exercise_id": exercise_id}
            ).single()
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(check_exercise_creator, username, exercise_id)
        
        if not result:
            return {'error': 'user is not the creator'}, 400
        else:
            def delete_exercise(tx, exercise_id):
                    return tx.run(
                    '''
                    MATCH (e:Exercise)
                    WHERE ID(e) = $exercise_id 
                    DETACH DELETE e
                    ''', {"exercise_id": exercise_id}
            )
            with self.driver.session(database="neo4j") as session:
                result = session.write_transaction(delete_exercise, exercise_id)
            
            return {'delete_exercise': 'operation was a success!'}, 200
    
    def deleteMyTraining(self, username, training_id):
        def check_training_creator(tx, username, training_id):
            return tx.run(
                '''
                MATCH (u:User {username: $username})-[:ADDED_TRAINING]->(t:Training)
                WHERE ID(t) = $training_id 
                return u
                ''', {'username': username, "training_id": training_id}
            ).single()
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(check_training_creator, username, training_id)
        
        if not result:
            return {'error': 'user is not the creator'}, 400
        else:
            def delete_my_training(tx, training_id):
                    return tx.run(
                    '''
                    MATCH (t:Training)
                    WHERE ID(t) = $training_id 
                    DETACH DELETE t
                    ''', {"training_id": training_id}
            )
            with self.driver.session(database="neo4j") as session:
                result = session.write_transaction(delete_my_training, training_id)
            
            return {'delete_my_training': 'operation was a success!'}, 200
        
    def followTraining(self, request, username):
        data = request.get_json()
        training_id = int(data.get('training_id'))
        def follow_training(tx, username, training_id):
            return tx.run(
                    '''
                    MATCH (u:User {username: $username}), (t:Training)
                    WHERE ID(t) = $training_id 
                    CREATE (u)-[:FOLLOWS]->(t)
                    ''', {"username": username, "training_id": training_id}
             )
        with self.driver.session(database="neo4j") as session:
                result = session.write_transaction(follow_training,username, training_id)
            
        return {'follow_training': 'operation was a success!'}, 200
    
    def unfollowTraining(self, request, username):
        data = request.get_json()
        training_id = int(data.get('training_id'))

        def unfollow_training(tx, training_id, username):
            return tx.run(
                '''
                MATCH (u:User {username: $username})-[r:FOLLOWS]->(t:Training)
                WHERE ID(t) = $training_id
                DELETE r
                ''', {'training_id': training_id, "username": username}
            )
        with self.driver.session(database="neo4j") as session:
            result = session.write_transaction(unfollow_training, training_id, username)
        
        return {'unfollow_training': 'operation was a success!'}, 204
    
    def checkOwner(self, request, username):
        data = request.get_json()
        training_id = int(data.get('training_id'))

        def check_training_owner(tx, training_id):
            return tx.run(
                '''
                MATCH (u:User)-[:ADDED_TRAINING]->(t:Training)
                WHERE ID(t) = $training_id
                RETURN u
                ''', {'training_id': training_id}
            ).single()
        with self.driver.session(database="neo4j") as session:
            result = session.read_transaction(check_training_owner, training_id)
        try:
            user = result['u']
        except KeyError:
            return '', 400
        
        return user['username'], 200

def hash_password(username, password):
    if sys.version[0] == 2:
        s = '{}:{}'.format(username, password)
    else:
        s = '{}:{}'.format(username, password).encode('utf-8')
    return hashlib.sha256(s).hexdigest()