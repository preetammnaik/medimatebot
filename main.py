import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
from flask import Flask, request, jsonify, make_response, render_template, json

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)

db = firestore.client()

session: any = ''
query: any = ''
result: any = ''
userID = ['test']

app = Flask(__name__)

specialization = []


@app.route('/')
def start():
    return render_template('index.html')


@app.route('/chat', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        req = request.get_json(silent=True, force=True)
        res = processRequest(req)

        ress = json.dumps(res, indent=4)
        r = make_response(ress)
        r.headers['Content-Type'] = 'application/json'
        return r


def saveConversations(query, result, session, userid, intent):
    print('Im in save')
    doc_reff = db.collection(u'UserHistory').document(session)
    user_conversation = {
        'query': query,
        'reply': result
    }
    print(userid)
    sessionConvo = {'userID': userid}
    doc_reff.set(sessionConvo)
    intentConvo = doc_reff.collection('conversation').document(intent)
    intentConvo.set(user_conversation)
     # print(result)
    # print(session)


def processRequest(req):
    print(userID)
    query_response = req.get("queryResult")
    intent = query_response.get("intent").get("displayName")
    # print(query_response)
    res =''
    query = query_response.get('queryText')
    result = query_response.get("fulfillmentText")
    session = query_response.get("outputContexts")[0].get("name").split("/")[-3]

    if intent == 'finddoctors':
        # print("HIiii")
        getDoctors, specout = getListofDoctors(req)
        specialization.append(specout)
        saveConversations(query, result, session, userID[-1], intent)
        res = createResponse(getDoctors)
        # return res

    elif intent == 'doctorInfo':
        doctorInfo = provideDoctorDetails(query, specialization)
        res = createResponse(doctorInfo)
        saveConversations(query, result, session, userID[-1], intent)

        print(res)
        # return res

    elif intent == 'New User - yes':
        res = newUserDetails(req, session)
        saveConversations(query, result, session, userID[-1], intent)
        # saveConversations(query, result, session, userID[-1])
        print("i am coming till here :p")
        # res = createResponseForNewUser(newUser)
        print(res)
        # return res

    # elif intent == 'New User - no':
    #     existingUser = existingUserDetail(req)
    #     # if existingUser == '':
    #     #     existingUser = 'Looks like you are not registered'
    #     #     res = createResponse(existingUser)
    #     # else:
    #     #     res = createFollowUpResponse(existingUser)
    #
    #     return res

    elif intent == 'getUserId':
        print('in here')
        res = existingUserDetail(req)
        saveConversations(query, result, session, userID[-1], intent)
        # res = createResponseForNewUser(existingUser)
        # return res

    elif intent == 'pharmacy':
        pharmacyDetail = providePharmacyDetails(req)
        res = createResponse(pharmacyDetail)
        saveConversations(query, result, session, userID[-1], intent)
        print(res)
        # return res

    elif intent == 'emergency':
        emergencyDetail = provideEmergencyDetails(req)
        res = createResponse(emergencyDetail)
        saveConversations(query, result, session, userID[-1], intent)
        print(res)


    # elif intent == 'languagespecification':
    #     doctorName = filterLanguageSpoken(text, specialization)
    #     res = get_data(doctorName)
    #     return res


    return res


def createResponse(fulfilment_text):
    return {
        "fulfillmentText": fulfilment_text
    }
    # webhookresponse = fulfilment_text
    # return {
    #     "fulfillmentText": fulfilment_text,
    #     "fulfillmentMessages": [
    #         {
    #             "text": {
    #                 "text": [
    #                     webhookresponse,
    #                     "I provide the following services a>	Based on your symptoms, I can find a doctor for you "
    #                     "nearby,b>	I can provide emergency contacts for you c>	I can provide Pharmacy emergency "
    #                     "contacts d>  Follow-up of previous doctor's appointments "
    #                 ]
    #
    #             }
    #         },
    #         {
    #             "text": {
    #                 "text": [
    #                     "I provide the following services a>	Based on your symptoms, I can find a doctor for you "
    #                     "nearby,b>	I can provide emergency contacts for you c>	I can provide Pharmacy emergency "
    #                     "contacts d>  Follow-up of previous doctor's appointments "
    #                 ]
    #             }
    #         },
    #         {"payload": {"rawPayload": "true", "sendAsMessage": "true"}}
    #     ]
    # }
    #


def createResponseForNewUser(fulfilment_text):
    fulfillmentMessages = {
        "fulfillmentMessages": [{
            "text": {
                "text": [
                    fulfilment_text
                ]
            },
            "platform": "TELEGRAM"
        },
            {
                "quickReplies": {
                    "title": "Please choose any option 👇",
                    "quickReplies": [
                        "Find Doctor",
                        "Emergency Room Contact",
                        "Pharmacy Contact"
                    ]
                },
                "platform": "TELEGRAM"
            }]
    }
    return fulfillmentMessages


def createFollowUpResponse(fulfilment_text):
    serviceIntentCall = {
        "fulfillmentText": fulfilment_text,
        "followupEventInput": {
            "name": "ServiceEvent",
        }
    }
    print(serviceIntentCall)
    return serviceIntentCall
    # webhookresponse = fulfilment_text
    # return {
    #     "fulfillmentText": fulfilment_text,
    #     "fulfillmentMessages": [
    #         {
    #             "text": {
    #                 "text": [
    #                     webhookresponse
    #                 ]
    #
    #             }
    #         },
    #         {
    #             "text": {
    #                 "text": [
    #                     "I provide the following services a>	Based on your symptoms, I can find a doctor for you "
    #                     "nearby,b>	I can provide emergency contacts for youc>	I can provide Pharmacy emergency "
    #                     "contacts d>  Follow-up of previous doctor's appointments "
    #                 ]
    #             }
    #         },
    #         {"payload": {"rawPayload": "true", "sendAsMessage": "true"}}
    #     ]
    # }


def newUserDetails(req, session):
    userName = req['queryResult']['parameters']['user_name']
    userEmail = req['queryResult']['parameters']['user_email']
    zipCode = req['queryResult']['parameters']['user_zipCode']

    print(userID)
    print(userName)
    print(userEmail)

    if checkUserExistenceByEmail(userEmail):
        userId = saveUserDetail(session, userEmail, userName, zipCode)
        message = "Hello, " + userName + " welcome to MediMate. Your userID is : " + userId
        res = createResponseForNewUser(message)
    else:
        message = 'Looks like this email id is already registered with us, please try a different email Id'
        res = createResponse(message)

    # docs = db.collection('Users').where('UserEmail', '==', userEmail).stream()
    # if userEmail in docs:
    #     for doc in docs:
    #         user = doc.to_dict()
    #         user_Id = user['userID']
    #     message = 'Looks like you are already registered with us, Your User Id is ' + user_Id
    #     return message

    return res


def saveUserDetail(session, userEmail, userName, zipCode):
    userIDsplit = userEmail.split("@")
    userId = userIDsplit[0] + "@"
    userID.append(userId)
    doc_ref = db.collection(u'Users').document(userId)
    my_data = {'UserName': userName, 'UserEmail': userEmail, 'userID': userId, 'userZipcode': zipCode}
    doc_userhistory = db.collection(u'UserHistory').document(session)
    my_userHistory = {'userID': userId}
    print(my_data)
    print(doc_userhistory)

    doc_userhistory.set(my_userHistory)
    doc_ref.set(my_data)

    return userId


def checkUserExistenceByEmail(userEmail):
    user_doc_ref = db.collection(u'Users').where(u'UserEmail', u'==', userEmail).stream()
    print("okayyyyyyyyyy")
    documents = [d for d in user_doc_ref]
    if len(documents):
        for document in documents:
            print(u'Not empty')
            return False
    else:
        print(u'empty query')
        return True


def existingUserDetail(req):
    userId = req['queryResult']['parameters']['user_Id']
    # print(userId)

    userName = checkUserExistence(userId)


    if (userName == "") or (userName is None):
        message = "Looks like you are not registered with us yet \n Please write 'register' to save your details"
        res = createResponse(message)
    else:
        message = "Welcome back " + str(userName)
        fetchPreviousConversation(userId)
        res = createResponseForNewUser(message)

    return res


def fetchPreviousConversation(userId):
    docs = db.collection('UserHistory').where('userID', '==', userId).stream()
    for doc in docs:
        user = doc.to_dict()
        previous_convo = user['conversation']
        # for convo in previous_convo:
        #     if convo['intent' == 'finddoctors']:
        #         previousReply = convo['reply']

        print(user_name)


def checkUserExistence(userId):
    docs = db.collection('Users').where('userID', '==', userId).stream()
    for doc in docs:
        user = doc.to_dict()
        user_name = user['UserName']
        print(user_name)

        return user_name


def getListofDoctors(req):
    result = ["Here is the list of doctors to choose from: "]
    i = 1

    parameters = req['queryResult']['parameters']
    # print('Dialogflow parameters:')
    specialization = str(parameters.get('doctorspecialization'))
    language = str(parameters.get('language')).lower()
    print(language)

    if parameters.get('doctorspecialization'):
        if str(parameters.get('doctorspecialization')) == str('general physician'):
            specialization1 = "GeneralPhysician"
            GeneralPhysicians = processLanguage(specialization1, language)
            for doctors in GeneralPhysicians:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                docName = str(i) + '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('gynaecologist'):
            Gynaecologist = processLanguage(specialization, language)
            for doctors in Gynaecologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                docName = str(i) + '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('ophthalmologist'):
            Ophthalmologist = processLanguage(specialization, language)
            for doctors in Ophthalmologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                docName = str(i) + '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('cardiologist'):
            Cardiologist = processLanguage(specialization, language)
            for doctors in Cardiologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                docName = str(i) + '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('pain'):
            pain = processLanguage(specialization, language)
            for doctors in pain:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                docName = str(i) + '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        print(result)
        res = "\r\n".join(x for x in result) + "\n" + 'Please enter the ID of a doctor for more info:)'
        print(res)

        return res, specialization


def provideDoctorDetails(options, specialization):
    options = options.upper()
    print(options)
    if specialization[-1] != "general physician":
        Specialization = specialization[-1].capitalize()

    else:
        Specialization = "GeneralPhysician"

    detailedInfo = db.collection(Specialization).document(options)
    info = detailedInfo.get()
    print(info)

    res = ""
    if info.exists:
        name = "Name : " + u'{}'.format(info.to_dict()['Name'])
        address = "Address : " + u'{}'.format(info.to_dict()['Address'])
        phone = "Phone : " + u'{}'.format(info.to_dict()['Telephone'])
        res = name + "\n" + address + "\n" + phone
    else:
        res = 'Please make sure to enter the correct Doctor ID'

    print(res)

    return res


def processLanguage(specialization, language):
    if (specialization != "GeneralPhysician"):
        Specialization = specialization.capitalize()
        print(Specialization)
    else:
        Specialization = specialization
    doctors = db.collection(Specialization).where(u'languageSpoken', u'array_contains', language).get()
    return doctors


def provideEmergencyDetails(req):
    pass


def providePharmacyDetails(req):
    pass


if __name__ == "__main__":
    app.run(debug=True, port=5000)
