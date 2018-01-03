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
import timeit
import logging

db_connect = create_engine('sqlite:///chinook.db')
app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/faceengine'
api = Api(app)
know_face_path = "D:/OpenFace/FaceDB/know_face"
# Cache the encoding
known_encodings = []
found_know_faces = []
logging.basicConfig(level=logging.DEBUG)


def load_know_face(identify):
    with open(join(know_face_path, str(identify)+'.jpg'), "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string


def save_know_face(face_data, identify):
    with open(join(know_face_path, str(identify)+'.jpg'), "wb") as fh:
        fh.write(base64.b64decode(face_data))


class Face(Resource):
    def post(self):
        data = request.get_json()
        save_know_face(data['FaceData'], data['Identify'])
        return jsonify({"ReturnCode": 200, "message": "Known face added"})
        # Fetches first column that is Employee ID


class Tracks(Resource):
    def get(self):
        conn = db_connect.connect()
        query = conn.execute("select trackid, name, composer, unitprice from tracks;")
        result = {'data': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
        return jsonify(result)


class KnowFace(Resource):
    def get(self, face_id):
        result = {"face": {"identify": face_id, "faceData": load_know_face(face_id)}}
        return jsonify(result.get("face "))


class RecognizePerson(Resource):
    def post(self):
        if request.method == 'POST':
            start = timeit.default_timer()
            try:
                request_data = request.get_json()
                result = recognition(request_data["FaceData"])
            except Exception as e:
                result = {"ReturnCode": 500, "message": e.message}
            end = timeit.default_timer()
            logging.info("Total execution time of recognize: %s", str(end - start))
            return jsonify(result)


def load_faces_from_base64_image(image_str):
    with tempfile.NamedTemporaryFile() as tf:
        tf.write(base64.b64decode(image_str))
        return face_recognition.load_image_file(tf)


def recognition(image):
    total_start = timeit.default_timer()
    start = timeit.default_timer()
    unknown_faces = face_recognition.face_encodings(load_faces_from_base64_image(image))
    end = timeit.default_timer()
    logging.info("Total process time of encode unknown faces: %s", str(end - start))
    if len(unknown_faces) > 0:
        image_to_test_encoding = unknown_faces[0]
    else:
        return {"ReturnCode": 404, "message": "No face found in input image"}
    know_face_list = [f for f in listdir(know_face_path) if isfile(join(know_face_path, f))]
    # if the know face size is change, reload the encoding list
    logging.debug("Len of know_face_list {0} and known_encodings {1}".format(len(know_face_list), len(known_encodings)))
    if len(know_face_list) != len(known_encodings):
        known_encodings[:] = []
        found_know_faces[:] = []
        start = timeit.default_timer()
        for (i, face_image) in enumerate(know_face_list):
            known_image = face_recognition.load_image_file(join(know_face_path, face_image))
            found_face = face_recognition.face_encodings(known_image)
            if len(found_face) > 0:
                face_encoding = face_recognition.face_encodings(known_image)[0]
                known_encodings.append(face_encoding)
                found_know_faces.append(splitext(face_image)[0])
            else:
                logging.debug("No face found in {}.".format(face_image))
        logging.debug("Found know face {}".format(found_know_faces))
        logging.debug("Done loading know face")
        end = timeit.default_timer()
        logging.info("Total process time of encode faces: %s", str(end - start))
    # Check the distance of all face
    start = timeit.default_timer()
    face_distances = face_recognition.face_distance(known_encodings, image_to_test_encoding)
    end = timeit.default_timer()
    logging.info("Total process time of check face distances: %s", str(end - start))
    logging.debug("face distances:")
    logging.debug("{}".format(face_distances))
    start = timeit.default_timer()
    min_index, min_value = min(enumerate(face_distances), key=operator.itemgetter(1))
    end = timeit.default_timer()
    logging.info("Total process time of check min index and value: %s", str(end - start))
    # print("min index", min_index)
    # print("min value", min_value)
    # print("know face", found_know_faces[min_index])
    if min_value < 0.4:
        face_result = {"ReturnCode": 200,
                       "message": "Find match face",
                       "Content": {"name": found_know_faces[min_index],
                                   "score": min_value}}
    else:
        face_result = {"ReturnCode": 404,
                       "message": "no known face found",
                       "Content": {"name": found_know_faces[min_index],
                                   "score": min_value}}
    total_end = timeit.default_timer()
    logging.info("Total process time for total time: %s", str(total_end - total_start))
    return face_result


api.add_resource(Face, '/face')  # Route_1
api.add_resource(Tracks, '/tracks')  # Route_2
api.add_resource(KnowFace, '/face/<face_id>')  # Route_3
api.add_resource(RecognizePerson, '/recognize')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5002')