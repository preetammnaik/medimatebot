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
docID = []
checkListDocID = []



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
    # sessionConvo = {'userID': userid, 'sessionId': session}
    # doc_reff.set(sessionConvo)
    intentConvo = doc_reff.collection('conversation').document(intent)
    intentConvo.set(user_conversation)
    # print(result)
    # print(session)


def processRequest(req):
    print(userID)
    query_response = req.get("queryResult")
    intent = query_response.get("intent").get("displayName")
    # print(query_response)
    res = ''
    query = query_response.get('queryText')
    result = query_response.get("fulfillmentText")
    session = query_response.get("outputContexts")[0].get("name").split("/")[-3]

    if intent == 'MedimateWelcomeIntent':
        # print("HIiii")
        saveConversations(query, result, session, userID[-1], intent)
        res = result

    elif intent == 'finddoctors':
        # print("HIiii")
        getDoctors, specout , docNo = getListofDoctors(req)
        specialization.append(specout)
        checkListDocID.append(docNo)
        saveConversations(query, req['queryResult']['parameters'].get('doctorspecialization'), session, userID[-1],
                          intent)
        res = createResponse(getDoctors)
        # return res

    elif intent == 'doctorInfo':
        docID.append(query)
        doctorInfo, name = provideDoctorDetails(query, specialization,checkListDocID)

        if (name == "INVALID"):
            quickReplies = [
                "Go back to Find Doctor",
                "Exit"
            ]
        else:
            quickReplies = [
                "Operational Hours",
                "Navigational Hours",
                "Exit"
            ]

        res = createResponseForAdditionalInfo(doctorInfo,quickReplies)




        #res = createFollowUpResponse(doctorInfo,"additionalinfo")
        saveConversations(query, name, session, userID[-1], intent)

        print(res)
        # return res

    elif intent == 'New User - yes':
        res = newUserDetails(req, session)
        saveConversations(query, result, session, userID[-1], intent)
        # saveConversations(query, result, session, userID[-1])
        print("i am coming till here :p")
        # res = createCommonResponse(newUser)
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
        # print('in here')
        res = existingUserDetail(req)
        # saveConversations(query, result, session, userID[-1], intent)
        # res = createCommonResponse(existingUser)
        # return res

    elif intent == 'pharmacyEmergency':
        pharmacyDetail = providePharmacyDetails(req)
        quickReplies = [
            "Find Doctor",
            "Emergency Information",
            "Exit"
        ]
        res = createCommonResponse(pharmacyDetail,quickReplies)
        saveConversations(query, result, session, userID[-1], intent)
        print(res)
        # return res

    elif intent == 'emergencyInfo':
        emergencyDetail = provideEmergencyDetails(req)
        quickReplies = [
            "Find Doctor",
            "Pharmacy Emergency",
            "Exit"
        ]
        res = createCommonResponse(emergencyDetail,quickReplies)
        saveConversations(query, result, session, userID[-1], intent)
        print(res)

    elif intent == 'navigationalRoutes':
        navigationDetails = provideNavigationRoutes(docID, specialization)
        res = createResponseForNavigationalInfo(navigationDetails)
        print(res)

    elif intent == 'operationalHours':
        operationalDetails = provideOperationalHours(docID, specialization)
        res = createResponseForOpHoursInfo(operationalDetails)
        print(res)



    elif intent == 'exitConversation':
        res = createFollowUpResponse("Exit", "Welcome")


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


def createCommonResponse(fulfilment_text, quickReplies):
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
                    "quickReplies": quickReplies
                },
                "platform": "TELEGRAM"
            }]
    }
    return fulfillmentMessages


# def createResponseForOldUser(fulfilment_text):
#     fulfillmentMessages = {
#         "fulfillmentMessages": [{
#             "text": {
#                 "text": [
#                     fulfilment_text
#                 ]
#             },
#             "platform": "TELEGRAM"
#         },
#             {
#                 "quickReplies": {
#                     "title": "Please choose any option 👇",
#                     "quickReplies": [
#                         "Notes",
#                         "Go to services menu"
#                     ]
#                 },
#                 "platform": "TELEGRAM"
#             }]
#     }
#     return fulfillmentMessages


def createFollowUpResponse(fulfilment_text, Event):
    serviceIntentCall = {
        "fulfillmentText": fulfilment_text,
        "followupEventInput": {
            "name": Event,
        }
    }
    # print(serviceIntentCall)
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

def createResponseForAdditionalInfo(fulfilment_text,quickReplies):
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
                    "title": "If you need any additional information, please choose one of the options 👇",
                    "quickReplies": quickReplies
                },
                "platform": "TELEGRAM"
            }]
    }
    return fulfillmentMessages

def createResponseForNavigationalInfo(fulfilment_text):
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
                    "title": "If you need any additional information, please choose one of the options 👇",
                    "quickReplies": [
                        "Operational Hours",
                        "Exit"
                    ]
                },
                "platform": "TELEGRAM"
            }]
    }
    return fulfillmentMessages

def createResponseForOpHoursInfo(fulfilment_text):
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
                    "title": "If you need any additional information, please choose one of the options 👇",
                    "quickReplies": [
                        "Navigational Routes",
                        "Exit"
                    ]
                },
                "platform": "TELEGRAM"
            }]
    }
    return fulfillmentMessages

def newUserDetails(req, session):
    userName = req['queryResult']['parameters']['user_name']
    userEmail = req['queryResult']['parameters']['user_email']
    zipCode = req['queryResult']['parameters']['user_zipCode']

    # print(userID)
    # print(userName)
    # print(userEmail)

    if checkUserExistenceByEmail(userEmail):
        userId = saveUserDetail(session, userEmail, userName, zipCode)
        message = "Hello, " + userName + " welcome to MediMate. Your userID is : " + userId
        quickReplies = [
            "Find Doctor",
            "Emergency Room Contact",
            "Pharmacy Contact"
        ]
        res = createCommonResponse(message, quickReplies)
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
    global userID
    userIDsplit = userEmail.split("@")
    userId = userIDsplit[0] + "@"
    userID.append(userId)

    doc_ref = db.collection(u'Users').document(userId)
    my_data = {'UserName': userName, 'UserEmail': userEmail, 'userID': userId, 'userZipcode': zipCode}
    doc_ref.set(my_data)

    # print(my_data)
    # print(doc_userhistory)
    doc_userhistory = db.collection(u'UserHistory').document(session)
    my_userHistory = {'userID': userId, 'sessionId': session}
    doc_userhistory.set(my_userHistory)

    return userId


def checkUserExistenceByEmail(userEmail):
    user_doc_ref = db.collection(u'Users').where(u'UserEmail', u'==', userEmail).stream()
    # print("okayyyyyyyyyy")
    documents = [d for d in user_doc_ref]
    if len(documents):
        for document in documents:
            # print(u'Not empty')
            return False
    else:
        # print(u'empty query')
        return True


def existingUserDetail(req):
    userId = req['queryResult']['parameters']['user_Id']
    # print(userId)

    userName = checkUserExistence(userId)
    userID.append(userId)

    if (userName == "") or (userName is None):
        message = "Looks like you are not registered with us yet \n " \
                  "Please write 'register' to save your details. \n \n Or would you like to re-enter your user-Id"
        res = createResponse(message)
    else:
        message, doesConvoExist = fetchPreviousConversation(userId)
        response = "Welcome back " + str(userName) + '. ' + message
        if doesConvoExist:
            quickReplies = [
                "Notes",
                "Go to services menu"
            ]
            res = createCommonResponse(response, quickReplies)
        else:
            res = createResponse(response)
    return res


def fetchPreviousConversation(userId):
    global session
    message = ''
    specialist = ''
    docName = ''
    docs = db.collection('UserHistory').where('userID', '==', userId).stream()
    documents = [d for d in docs]
    if len(documents):
        for doc in documents:
            user = doc.to_dict()
            # print("session", user)
            session = user['sessionId']
        collections = db.collection('UserHistory').document(session).collections()
        for collection in collections:
            for doc in collection.stream():
                print(f'{doc.id} => {doc.to_dict()}')
                if doc.id == 'finddoctors':
                    specialist = doc.to_dict()['reply']
                    # message += 'Looks like, you were looking for a ' + doc.to_dict()['reply'] + '. \n'
                    # print(message)
                if doc.id == 'doctorInfo':
                    docName = doc.to_dict()['reply']
                    # message += 'I hope your appointment went well with ' + doc.to_dict()['reply'] + \
                    #           '.\n Do you want me to create a note about the appointment?'
                    # print(message)
            return '\n Looks like, you were looking for a ' + specialist + '. \n I hope your appointment went well with ' + docName + \
                   '.\n Do you want me to create a note about the appointment?', True
    else:
        # print(u'empty query')
        return "", False

    # if docs is not None:

    # else:
    #     message = ''

    #
    # user = doc.to_dict()
    # print(user)
    # previous_convo = user['conversation']
    # # for convo in previous_convo:
    # #     if convo['intent' == 'finddoctors']:
    # #         previousReply = convo['reply']
    #
    # # print(user_name)


def checkUserExistence(userId):
    docs = db.collection('Users').where('userID', '==', userId).stream()
    documents = [d for d in docs]
    if len(documents):
        for doc in documents:
            user = doc.to_dict()
            user_name = user['UserName']
            print(user_name)

            return user_name
    else:
        # print(u'empty query')
        return ""


def getListofDoctors(req):
    result = ["Here is the list of doctors to choose from: "]
    i = 1
    doctorID =[]

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
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('gynaecologist'):
            Gynaecologist = processLanguage(specialization, language)
            for doctors in Gynaecologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('ophthalmologist'):
            Ophthalmologist = processLanguage(specialization, language)
            for doctors in Ophthalmologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('cardiologist'):
            Cardiologist = processLanguage(specialization, language)
            for doctors in Cardiologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('pain'):
            pain = processLanguage(specialization, language)
            for doctors in pain:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + u'{}'.format(doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        print(result)
        if len(result)==1:
            res = "Unfortunately, there are no doctors with your requirement. Please try again with a different language of communication. "
        else:
            res = "\r\n".join(x for x in result) + "\n" + 'Please enter the ID of a doctor for more info:)'
        print(res)

        return res, specialization,doctorID


def provideDoctorDetails(options, specialization,checkListofDocs):

    options = options.upper()
    if options in checkListofDocs[0]:
        if specialization[-1] != "general physician":
            Specialization = specialization[-1].capitalize()

        else:
            Specialization = "GeneralPhysician"

        detailedInfo = db.collection(Specialization).document(options)
        info = detailedInfo.get()
        print(info)

        res = ""
        if info.exists:
            name = "🩺 Name : " + u'{}'.format(info.to_dict()['Name'])
            address = "📌 Address : " + u'{}'.format(info.to_dict()['Address'])
            phone = "📞 Phone : " + u'{}'.format(info.to_dict()['Telephone'])
            res = name + "\n" + address + "\n" + phone
        else:
            res = 'Please make sure to enter the correct Doctor ID'

        print(res)

    else:
        res = "The Doctor ID may be valid but does not meet your language requirements."
        name = "INVALID"

    return res, name


def processLanguage(specialization, language):
    if (specialization != "GeneralPhysician"):
        Specialization = specialization.capitalize()
        print(Specialization)
    else:
        Specialization = specialization
    doctors = db.collection(Specialization).where(u'languageSpoken', u'array_contains', language).get()
    return doctors


def provideEmergencyDetails(req):
    emergencyDetails = "Here is a list of Emergency numbers : "+"\n"
    emergency = db.collection(u'Emergency').get()
    print(emergency)
    i = 1
    for emergencyInfo in emergency:
        name =  "🩺 Name : " + "0"+str(i)+ " : "+ u'{}'.format(emergencyInfo.to_dict()['Name'])
        address = "📌 Address "+ "0"+str(i)+ " : " + u'{}'.format(emergencyInfo.to_dict()['Address'])
        phone = "📞 Phone " +"0"+ str(i)+ " : " + u'{}'.format(emergencyInfo.to_dict()['Telephone'])
        emergencyDetails += name+"\n"+ address + "\n" + phone +"\n"
        i=i+1

    print(emergencyDetails)
    return emergencyDetails




def providePharmacyDetails(req):
    pharmacyDetails = "Here is a list of Pharmacy Emergency numbers : "+"\n"
    pharmacy = db.collection(u'Pharmacy').get()
    i = 1
    for pharmacyInfo in pharmacy:
        address = "📌 Address" + str(i) + " : " + u'{}'.format(pharmacyInfo.to_dict()['Address'])
        phone = "📞 Phone" + str(i) + " : " + u'{}'.format(pharmacyInfo.to_dict()['Phone'])
        pharmacyDetails += address + "\n" + phone + "\n"

    print(pharmacyDetails)
    return pharmacyDetails

def provideNavigationRoutes(docID,specialization):
    doctorID = docID[-1].upper()
    route =""

    if (specialization[-1] != "general physician"):
        Specialization = specialization[-1].capitalize()

    else:
        Specialization = "GeneralPhysician"

    detailedInfo = db.collection(Specialization).document(doctorID)
    info = detailedInfo.get()
    if info.exists:
        navigation =  u'{}'.format(info.to_dict()['Navigation'])
        navigation = navigation.replace("[","")
        navigation = navigation.replace("]", "")
        delim = navigation.split(",")
        i=1
        for routes in delim:
            route += str(i) + "." + routes + "\n"
            i += 1
    else:
        route = 'Unfortunately, the routes are not available for this Doctor ID. '



    print(route)
    return route

def provideOperationalHours(docID,specialization):
    doctorID = docID[-1].upper()
    hours=""
    if (specialization[-1] != "general physician"):
        Specialization = specialization[-1].capitalize()

    else:
        Specialization = "GeneralPhysician"

    detailedInfo = db.collection(Specialization).document(doctorID)
    info = detailedInfo.get()
    if info.exists:
        OperationalHours = u'{}'.format(info.to_dict()['OperationalHours'])
        OperationalHours = OperationalHours.replace("{", "")
        OperationalHours = OperationalHours.replace("}", "")
        delim = OperationalHours.split(",")
        i = 1
        for opHrs in delim:
            hours += str(i) + "." + opHrs + "\n"
            i += 1
    else:
        OperationalHours = 'Unfortunately, the working timings are not available for this Doctor ID. '
##pleaseworknowpppppsssss
    print(hours)
    return hours



if __name__ == "__main__":
    app.run(debug=True, port=5002)
