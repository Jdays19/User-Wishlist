from flask import Flask, render_template, request
import redis # in memory data structure, key-value db

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev'

from app.models import db, UserFavs

db.init_app(app)
with app.app_context():
    db.create_all()
    db.session.commit()

red = redis.Redis(host='redis', port=6379, db=0)

@app.route("/")
def main():
    return render_template("index.html")

@app.route("/save", methods=['POST'])
def save():
    username = str(request.form['username'])
    place =  str(request.form['place'])
    food = str(request.form['food'])

    # print("username:", username)
    # print("place:", place)
    # print("food:", food)

    if red.hgetall(username).keys():
        print("hget username:", red.hgetall(username))
        return render_template('index.html',user_exists=1, msg='(From Redis)', username=username, place=red.hget(username, "place").decode('utf-8'), food=red.hget(username, "food").decode('utf-8'))

    elif len(list(red.hgetall(username)))==0:
        record = UserFavs.query.filter_by(username=username).first()
        print("Records fetched from db:", record)

        if record:
            red.hset(username,"place", place)
            red.hset(username,"food", food)

            return render_template('index.html', user_exists=1, msg='(From Database)', username=username, place=record.place, food=record.food)

    new_record = UserFavs(username=username, place=place, food=food)
    db.session.add(new_record)
    db.session.commit()

    red.hset(username, "place", place)
    red.hset(username, "food", food)

    record = UserFavs.query.filter_by(username=username).first()
    print("Records fetched from db after insert:", record)

    print("key-values from redis after insert:", red.hgetall(username))

    return render_template('index.html', saved=1, username=username, place=red.hget(username, "place").decode('utf-8'), food=red.hget(username, "food").decode('utf-8'))

@app.route("/keys", methods=['GET'])
def keys():
    records = UserFavs.query.all()
    names = []
    for record in records:
        names.append(record.username)
    return render_template('index.html', keys=1, usernames=names)

@app.route("/get", methods=['POST'])
def get():
    username = request.form['username']
    print("Username:", username)
    user_data = red.hgetall(username)
    print("GET Redis:", user_data)
    
    if not user_data:
        record = UserFavs.query.filter_by(username=username).first()
        print("GET Record:", record)
        if not record:
            print("No data in redis or db")
            return render_template('index.html', no_record=1, msg=f"Record not yet defined for {username}")
        red.hset(username, "place", record.place)
        red.hset(username, "food", record.food)
        return render_template('index.html', get=1, msg="(From Database)",username=username, place=record.place, food=record.food)
    return render_template('index.html',get=1, msg="(From Redis)", username=username, place=user_data[b'place'].decode('utf-8'), food=user_data[b'food'].decode('utf-8'))
# if __name__ == "__main__":
#     # Only for debugging while developing
#     app.run(host='0.0.0.0', debug=True, port=80)
