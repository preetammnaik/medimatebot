import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
from flask import Flask, request, jsonify, make_response, render_template, json

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)

GeneralPhysicians = db.collection(u'GeneralPhysician').get()
for doctors in GeneralPhysicians:
    docName = u'{}'.format(doctors.to_dict()['Name'])
    print("Name of the doctor :", docName)
    docAddress = u'{}'.format(doctors.to_dict()['Address'])
    print("Address of the doctor :", docAddress)


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
        print("HIiii")
        getDoctors = getListofDoctors(req)
    else:
        getDoctors = "I do not understand"

    print(getDoctors)
    res = get_data(getDoctors)
    print(res)
    return res


def get_data(fulfilment_text):
    return {
        "fulfillmentText": fulfilment_text
    }


def getListofDoctors(req):
    result = ["Here is the list of doctors to choose from: "]
    i = 1

    parameters = req['queryResult']['parameters']
    print('Dialogflow parameters:')

    if parameters.get('doctorspecialization'):
        if str(parameters.get('doctorspecialization')) == str('general physician'):
            GeneralPhysicians = db.collection(u'GeneralPhysician').get()
            for doctors in GeneralPhysicians:
                docName = str(i)+'.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('gynaecologist'):
            Gynaecologist = db.collection(u'Gynaecologist').get()
            for doctors in Gynaecologist:
                docName = str(i)+'.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('ophthalmologist'):
            Gynaecologist = db.collection(u'Ophthalmologist').get()
            for doctors in Gynaecologist:
                docName = str(i)+'.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('cardiologist'):
            Gynaecologist = db.collection(u'Cardiologist').get()
            for doctors in Gynaecologist:
                docName = str(i)+'.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('emergency'):
            Gynaecologist = db.collection(u'Emergency').get()
            for doctors in Gynaecologist:
                docName = str(i)+'.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('pain'):
            Gynaecologist = db.collection(u'GeneralPhysician').get()
            for doctors in Gynaecologist:
                docName = str(i)+'.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        print(result)
        res = "\r\n".join(x for x in result) + '\n' + 'Please choose a doctor for more info:)'
        print(res)

        return res


if __name__ == "__main__":
    app.run(debug=True, port=5001)
