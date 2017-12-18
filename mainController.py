import operator
from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask_jsonpify import jsonify
import base64
import face_recognition
from os import listdir
from os.path import isfile, join, splitext
import tempfile

db_connect = create_engine('sqlite:///chinook.db')
app = Flask(__name__)
api = Api(app)
know_face_path = "D:/OpenFace/FaceDB/know_face"


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
            #image = base64.b64decode()
            #print(image)
            recognition(request.get_json())
            return jsonify({"Name" : "Tester", "Detail" : "This is a testing person\nThis the second line of testing data", "Score" : 7.3})


def load_faces_from_base64_image(image_str):
    with tempfile.NamedTemporaryFile() as tf:
        tf.write(base64.b64decode(image_str))
        return face_recognition.load_image_file(tf)


def recognition(image):
    unknown_faces = face_recognition.face_encodings(load_faces_from_base64_image(image))
    if len(unknown_faces) > 0:
        image_to_test_encoding = unknown_faces[0]
    else:
        return "No face found in input image"
    know_face_list = [f for f in listdir(know_face_path) if isfile(join(know_face_path, f))]
    known_encodings = []
    found_know_faces = []
    for (i, face_image) in enumerate(know_face_list):
        print i, face_image
        known_image = face_recognition.load_image_file(join(know_face_path, face_image))
        found_face = face_recognition.face_encodings(known_image)
        if len(found_face) > 0:
            face_encoding = face_recognition.face_encodings(known_image)[0]
            known_encodings.append(face_encoding)
            found_know_faces.append(splitext(face_image)[0])
        else:
            print("No faec found in {}.".format(face_image))
    print("Found know face ", found_know_faces)
    print("Done loading know face")

    face_distances = face_recognition.face_distance(known_encodings, image_to_test_encoding)
    print("face fistances:")
    print(face_distances)
    min_index, min_value = min(enumerate(face_distances), key=operator.itemgetter(1))
    print("min index", min_index)
    print("min value", min_value)
    print("know face", found_know_faces[min_index])
    return min_index;


api.add_resource(Face, '/face')  # Route_1
api.add_resource(Tracks, '/tracks')  # Route_2
api.add_resource(KnowFace, '/face/<face_id>')  # Route_3
api.add_resource(RecognizePerson, '/recognize')


if __name__ == '__main__':
    app.run(port='5002')