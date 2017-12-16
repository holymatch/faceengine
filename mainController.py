from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask_jsonpify import jsonify
import base64

db_connect = create_engine('sqlite:///chinook.db')
app = Flask(__name__)
api = Api(app)


def load_know_face(identify):
    with open("know_face/{0}.jpg".format(identify), "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string


def save_know_face(face_data, identify):
    with open("know_face/{0}.jpg".format(identify), "wb") as fh:
        fh.write(base64.b64decode(face_data))


class Face(Resource):
    def post(self):
        data = request.get_json()
        save_know_face(data['FaceData'], data['Identify'])
        return jsonify({"Name" : "Tester", "Detail" : "This is a testing person\nThis the second line of testing data", "Score" : 7.3})  # Fetches first column that is Employee ID


class Tracks(Resource):
    def get(self):
        conn = db_connect.connect()
        query = conn.execute("select trackid, name, composer, unitprice from tracks;")
        result = {'data': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
        return jsonify(result)


class KnowFace(Resource):
    def get(self, face_id):
        result ={"face": { "identify": face_id, "faceData": load_know_face(face_id)}}
        return jsonify(result.get("face "))


class RecognizePerson(Resource):
    def post(self):
        if request.method == 'POST':
            image = request.get_json()
            with open("imageToSave.jpg", "wb") as fh:
                fh.write(base64.b64decode(image))
            return jsonify({"Name" : "Tester", "Detail" : "This is a testing person\nThis the second line of testing data", "Score" : 7.3})


api.add_resource(Face, '/face')  # Route_1
api.add_resource(Tracks, '/tracks')  # Route_2
api.add_resource(KnowFace, '/face/<face_id>')  # Route_3
api.add_resource(RecognizePerson, '/recognize')


if __name__ == '__main__':
    app.run(port='5002')