import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
from flask import Flask, request, jsonify, make_response, render_template, json
import re

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)

specialization = []


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
    print("1sada")
    query_response = req.get("queryResult")
    print(query_response)
    text = query_response.get('queryText', None)
    intent = query_response.get("intent").get("displayName")
    print(intent)

    if intent == 'finddoctors':
        print("HIiii")
        getDoctors, specout = getListofDoctors(req)
        specialization.append(specout)
        res = get_data(getDoctors)
        return res

    elif intent == 'doctorInfo':
        doctorInfo = provideDoctorDetails(text, specialization)
        res = get_data(doctorInfo)
        return res

    elif intent == 'New User - yes':
        newUser = newUserDetails(req)
        res = get_data2(newUser)
        print(res)
        return res

    elif intent == 'New User - no':
        collectUserDetails(req)


def get_data(fulfilment_text):
    return {
        "fulfillmentText": fulfilment_text
    }


def get_data2(fulfilment_text):
    serviceIntentCall= {
        "fulfillmentText": fulfilment_text,
        "followupEventInput": {
            "name": "ServiceEvent",
        }
    }
    print(serviceIntentCall)
    return serviceIntentCall
    # return {
    #     "fulfillmentText": fulfilment_text,
    #     "fulfillmentMessages": [
    #         {
    #             "text": {
    #                 "text": [
    #                     "I provide the following services a>	Based on your symptoms, I can find a doctor for you "
    #                     "nearby,b>	I can provide emergency contacts for youc>	I can provide Pharmacy emergency "
    #                     "contacts d>  Follow-up of previous doctor's appointments "
    #                 ]
    #             }
    #         }
    #     ]
    # }

def newUserDetails(req):
    userName = req['queryResult']['parameters']['user_name']
    userEmail = req['queryResult']['parameters']['user_email']

    userIDsplit = userEmail.split("@")
    userID = userIDsplit[0]

    print(userID)

    print(userName)
    print(userEmail)

    doc_ref = db.collection(u'Users').document()
    my_data = {'UserName': userName, 'UserEmail': userEmail, 'userID': userID}
    doc_reff = db.collection(u'UserHistory').document(userID)

    print(my_data)
    doc_ref.set(my_data)
    message = "Hello, " + userName + " welcome to MediBuddy. Your userID is : " + userID
    return message


def collectUserDetails(req):
    pass


def getListofDoctors(req):
    result = ["Here is the list of doctors to choose from: "]
    i = 1

    parameters = req['queryResult']['parameters']
    print('Dialogflow parameters:')
    specialization = str(parameters.get('doctorspecialization'))

    if parameters.get('doctorspecialization'):
        if str(parameters.get('doctorspecialization')) == str('general physician'):
            GeneralPhysicians = db.collection(u'GeneralPhysician').get()
            for doctors in GeneralPhysicians:
                docName = str(i) + '.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('gynaecologist'):
            Gynaecologist = db.collection(u'Gynaecologist').get()
            for doctors in Gynaecologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                docName = str(i) + '.' + u'{}'.format(doctors.to_dict()['Name']) + " " + "ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('ophthalmologist'):
            Ophthalmologist = db.collection(u'Ophthalmologist').get()
            for doctors in Ophthalmologist:
                docName = str(i) + '.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('cardiologist'):
            Cardiologist = db.collection(u'Cardiologist').get()
            for doctors in Cardiologist:
                docName = str(i) + '.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('emergency'):
            Emergency = db.collection(u'Emergency').get()
            for doctors in Emergency:
                docName = str(i) + '.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('pain'):
            pain = db.collection(u'GeneralPhysician').get()
            for doctors in pain:
                docName = str(i) + '.' + u'{}'.format(doctors.to_dict()['Name'])
                i = i + 1
                result.append(docName)
        # print(result)
        res = "\r\n".join(x for x in result) + '\n' + 'Please choose a doctor for more info:)'
        # print(res)

        return res, specialization


def provideDoctorDetails(options, specialization):
    options = options.upper()
    print(options)
    Specialization = specialization[-1].capitalize()
    print(Specialization)

    detailedInfo = db.collection(Specialization).document(options)
    info = detailedInfo.get()
    print(info)

    details = []
    if info.exists:
        name = "Name : " + u'{}'.format(info.to_dict()['Name'])
        address = "Address : " + u'{}'.format(info.to_dict()['Address'])
        phone = "Phone : " + u'{}'.format(info.to_dict()['Telephone'])
        details.append(name)
        details.append(address)
        details.append(phone)
    else:
        details = 'Please make sure to enter the correct Doctor ID'

    print(details)

    return details


if __name__ == "__main__":
    app.run(debug=True, port=5001)
