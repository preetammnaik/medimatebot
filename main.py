import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
from flask import Flask, request, jsonify, make_response, render_template, json

cred = credentials.Certificate("serviceAccountKey.json")

default_app = firebase_admin.initialize_app(cred, {
    'databaseURL': "https://medimate-dtaq-default-rtdb.firebaseio.com"
})

app = Flask(__name__)


@app.route('/')
def start():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def index():
    if request.method == "POST":
        req = request.get_json(silent=True, force=True)
        res = processRequest(req)

        ress = json.dumps(res, indent=4)
        r = make_response(ress)
        r.headers['Content-Type'] = 'application/json'
        return r


def processRequest(req):
    query_response = req.get("queryResult")
    print(query_response)
    text = query_response.get('queryText', None)
    intent = query_response.get("intent").get("displayName")

    if intent == 'finddoctors':
        getDoctors = getListofDoctors(req)
    else:
        getDoctors = "I do not understand"

    res = get_data(getDoctors)
    print(res)
    return res


def get_data(fulfilment_text):
    return {
        "fulfillmentText": fulfilment_text
    }


def getListofDoctors(req):
    parameters = req['queryResult']['parameters']
    print(parameters)
    ref = db.reference("Doctors")
    doctor_specialization = ref.get()

    if parameters.get('doctorspecialization'):
        if str(parameters.get('doctorspecialization')) == str('ophthalmologist'):
            result = 'Here is a Ophthalmologist Dr. Charlie Thiel' + ' ' + ' and Address is 221 Ernst Lehmann Str., 39106, Magdeburg, Germany'
        if str(parameters.get('doctorspecialization')) == str('gynaecologist'):
            result = 'Here is a Gynaecologist Dr. Rose Soren' + ' ' + ' and Address is 221 otto von guericke Str.,39104 Magdeburg, Germany'
        if str(parameters.get('doctorspecialization')) == str('Orthopedic'):
            result = 'Here is Orthopedic Dr. Maria Sanchez' + ' ' + 'and Address is Johaness Gottileb Str., 39106 Magdeburg, Germany'
        if str(parameters.get('doctorspecialization')) == str('pain'):
            result = 'Here is a General Doctor Dr. Charlie Thiel' + ' ' + 'and Address is 221 Ernst Lehmann Str., 39106, Magdeburg, Germany'

    print(result)
    return result


if __name__ == "__main__":
    app.run(debug=True, port=5001)
