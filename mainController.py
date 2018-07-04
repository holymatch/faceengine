import operator
from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask_jsonpify import jsonify
import base64
import face_recognition
from os import listdir, path, remove
from os.path import isfile, join, splitext
import tempfile
import timeit
import logging
import numpy

db_connect = create_engine('sqlite:///chinook.db')
app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/faceengine'
api = Api(app)
know_face_path = "D:/OpenFace/FaceDB/know_face"
# Cache the encoding
known_encodings = []
found_know_faces = []
logging.basicConfig(level=logging.INFO)
IDENTIFY_THRESHOLD = 0.4


class Tracks(Resource):
    def get(self):
        conn = db_connect.connect()
        query = conn.execute("select trackid, name, composer, unitprice from tracks;")
        result = {'data': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
        return jsonify(result)


class RecognizePerson(Resource):
    def post(self):
        if request.method == 'POST':
            start = timeit.default_timer()
            try:
                request_data = request.get_json()
                result = recognition(request_data["FaceData"])
            except Exception as e:
                result = {"ReturnCode": 500, "Message": e.message}
            end = timeit.default_timer()
            logging.info("Total execution time of recognize: %s", str(end - start))
            return jsonify(result)


class FaceController(Resource):

    def post(self):
        data = request.get_json()
        logging.debug("Is Json {0}".format(request.is_json) )
        logging.debug("Request is {0}, request.get_json() is {1}".format(request, request.get_json()))
        faces = encode_face(data['FaceData'])
        if len(faces) > 0:
            save_know_face_encode(data['FaceData'], data['Identify'])
            return jsonify({"ReturnCode": 200, "Message": "Known face added"})
        else:
            return {"ReturnCode": 404, "Message": "No face found in input image"}

    def delete(self, face_id):
        logging.debug("Delete face called. ")
        face_file = join(know_face_path, str(face_id)+'.dat.npy')
        logging.debug("File path: {0}".format(face_file))
        if path.exists(face_file):
            logging.debug("Delete file: {0}".format(face_file))
            try:
                remove(face_file)
                known_encodings[:] = []
                return "Ok", 200
            except OSError as e:
                return e.message, 500
        else:
            return "File Not Found", 500


def load_know_face(identify):
    with open(join(know_face_path, str(identify)+'.jpg'), "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string


def save_know_face(face_data, identify):
    with open(join(know_face_path, str(identify)+'.jpg'), "wb") as fh:
        fh.write(base64.b64decode(face_data))


def save_know_face_encode(face_data, identify):
    face = encode_face(face_data)[0]
    numpy.save(join(know_face_path, str(identify)+'.dat'), face, True)


def load_know_face_encode(identify):
    return numpy.load(join(know_face_path, str(identify)+'.dat.npy'))


def load_faces_from_base64_image(image_str):
    with tempfile.NamedTemporaryFile() as tf:
        tf.write(base64.b64decode(image_str))
        return face_recognition.load_image_file(tf)


def encode_face(image):
    start = timeit.default_timer()
    faces = face_recognition.face_encodings(load_faces_from_base64_image(image))
    end = timeit.default_timer()
    logging.info("Total process time of encode unknown faces: %s", str(end - start))
    return faces


def recognition(image):
    total_start = timeit.default_timer()
    unknown_faces = encode_face(image)
    if len(unknown_faces) > 0:
        image_to_test_encoding = unknown_faces[0]
    else:
        return {"ReturnCode": 404, "Message": "No face found in input image"}
    know_face_list = [f for f in listdir(know_face_path) if isfile(join(know_face_path, f)) and f.endswith(".dat.npy")]
    # if the know face size is change, reload the encoding list
    logging.debug("Len of know_face_list {0} and known_encodings {1}".format(len(know_face_list), len(known_encodings)))
    if len(know_face_list) != len(known_encodings):
        known_encodings[:] = []
        found_know_faces[:] = []
        start = timeit.default_timer()
        for (i, face_image) in enumerate(know_face_list):
            identify = splitext(splitext(face_image)[0])[0]
            face_encoding = load_know_face_encode(identify)
            logging.debug("face encoding: {}".format(face_encoding))
            known_encodings.append(face_encoding)
            found_know_faces.append(identify)
        logging.debug("Found know face {}".format(found_know_faces))
        logging.debug("Done loading know face")
        end = timeit.default_timer()
        logging.info("Total process time of encode faces: %s", str(end - start))
    # Check the distance of all face
    start = timeit.default_timer()
    logging.debug("known_encodings {} ".format(known_encodings))
    logging.debug("image_to_test_encoding {} ".format(image_to_test_encoding))
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
    if min_value < IDENTIFY_THRESHOLD:
        face_result = {"ReturnCode": 200,
                       "Message": "Find match face",
                       "Content": {"Identify": found_know_faces[min_index],
                                   "Score": min_value}}
    else:
        face_result = {"ReturnCode": 404,
                       "Message": "no known face found",
                       "Content": {"Identify": found_know_faces[min_index],
                                   "Score": min_value}}
    total_end = timeit.default_timer()
    logging.info("Total process time for total time: %s", str(total_end - total_start))
    return face_result


api.add_resource(Tracks, '/tracks')  # Route_2
api.add_resource(FaceController, '/face', '/face/<int:face_id>')
api.add_resource(RecognizePerson, '/recognize')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5002')