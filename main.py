import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
from termcolor import colored
import datetime
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
intentList = []
intentqList = []
MedimateWelcomeIntent = {
    "fulfillmentText": "Sorry,what was that?🤔 \n But you can always choose from the options below that i can help "
                       "you with"}
NewUseryes = {'fulfillmentMessages': [
    {'text': {'text': ['I did not get that. Could you try that again']}, 'platform': 'TELEGRAM'}, {
        'quickReplies': {'title': 'Please choose from these option 👇',
                         'quickReplies': ['Find Doctor', 'Emergency Contacts', 'Pharmacy Contact']},
        'platform': 'TELEGRAM'}]}
finddoc = {'fulfillmentMessages': [
    {'text': {'text': ['Sorry, maybe you mentioned a symptom, specialization or feature not covered under system. '
                       'Please could you try differently']}, 'platform': 'TELEGRAM'}, {
        'quickReplies': {'title': 'Please choose any option 👇',
                         'quickReplies': ['Find Doctor', 'Emergency Contacts', 'Pharmacy Contact']},
        'platform': 'TELEGRAM'}]}


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
    if userid != 'test':
        doc_reff = db.collection(u'UserHistory').document(session + '.' + userid)
        user_conversation = {
            'query': query,
            'reply': result,
            'intent': intent
        }
        if intent == 'finddoctors' or intent == 'pharmacyEmergency' or intent == 'emergencyInfo':
            intentConvo = doc_reff.collection('conversation').document('finddoctors')
            if intent == 'pharmacyEmergency' or intent == 'emergencyInfo':
                intentConvo2 = doc_reff.collection('conversation').document('requestNotes')
                intentConvo2.set({'query': '',
                                  'reply': '',
                                  'intent': ''})
        else:
            intentConvo = doc_reff.collection('conversation').document(intent)

        intentConvo.set(user_conversation)

    # print(result)
    # print(session)


def processRequest(req):
    # print(req)
    query_response = req.get("queryResult")
    intent = query_response.get("intent").get("displayName")
    intentList.append(intent)
    # print("The intent list is below")
    print(intentList)
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
        specialization.clear()
        checkListDocID.clear()
        language = ''
        retrieveLanguage = db.collection(u'Users').document(userID[-1]).get()
        if retrieveLanguage.exists:
            language = u'{}'.format(retrieveLanguage.to_dict()['preferredLanguage'])
        getDoctors, specout, docNo = getListofDoctors(req, language)
        specialization.append(specout)
        checkListDocID.append(docNo)
        saveConversations(query, req['queryResult']['parameters'].get('doctorspecialization'), session, userID[-1],
                          intent)

        if (len(docNo) > 0):
            res = createResponse(getDoctors)
        else:
            quickReplies = [
                "Go back to Find Doctor 🔍",
                "Exit❌"
            ]
            res = createResponseForAdditionalInfo(getDoctors, quickReplies)
        # return res

    elif intent == 'doctorInfo':
        docID.append(query)
        doctorInfo, name = provideDoctorDetails(query, specialization, checkListDocID)

        if (name == "INVALID"):
            quickReplies = [
                "Go back to Find Doctor 🔍",
                "Exit❌"
            ]
        else:
            quickReplies = [
                "Operational Hours",
                "Navigational Route",
                "Exit❌"
            ]

        res = createResponseForAdditionalInfo(doctorInfo, quickReplies)

        # res = createFollowUpResponse(doctorInfo,"additionalinfo")
        saveConversations(query, name, session, userID[-1], intent)

        print(res)

    elif intent == "doctorNumber":
        # print(checkListDocID[0])
        doctorInfo, name, doctorID = provideDocDetailNumber(query, specialization, checkListDocID)
        if (doctorID != 0):
            docID.append(doctorID)
            quickReplies = [
                "Operational Hours",
                "Navigational Route",
                "Exit❌"
            ]
            print(res)
        else:
            quickReplies = [
                "Go back to Find Doctor 🔍",
                "Exit❌"
            ]
        saveConversations(query, name, session, userID[-1], intent)
        res = createResponseForAdditionalInfo(doctorInfo, quickReplies)


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
        saveConversations(query, result, session, userID[-1], intent)
        # res = createCommonResponse(existingUser)
        # return res
    elif intent == 'requestNotes':
        notes = req['queryResult']['parameters']['notes']
        message = "Noted 👍." + '\n \nAs you already know I provide the following services,'
        textForQuickReplies = 'please choose any option 👇'
        quickReplies = ["Find Doctor 🔍",
                        "Emergency Contacts 🚨",
                        "Pharmacy Contacts"
                        ]
        res = createCommonResponse(message, quickReplies, textForQuickReplies)
        saveConversations(query, notes, session, userID[-1], intent)

    elif intent == 'enterLanguagePreference':
        res = saveUserLanguagePreference(req)
        # saveConversations(query, res, session, userID[-1], intent)

    elif intent == 'pharmacyEmergency':
        pharmacyDetail = providePharmacyDetails(req)
        textForQuickReplies = 'please choose any option 👇'
        quickReplies = [
            "Find Doctor 🔍",
            "Emergency Information 🚨",
            "Exit❌"
        ]
        res = createCommonResponse(pharmacyDetail, quickReplies, textForQuickReplies)
        saveConversations(query, "emergency", session, userID[-1], intent)
        print(res)
        # return res

    elif intent == 'emergencyInfo':
        emergencyDetail = provideEmergencyDetails(req)
        textForQuickReplies = 'The following services are offered, please choose any of the below options 👇'
        quickReplies = [
            "Find Doctor 🔍",
            "Pharmacy Emergency",
            "Exit❌"
        ]
        res = createCommonResponse(emergencyDetail, quickReplies, textForQuickReplies)
        saveConversations(query, "emergency", session, userID[-1], intent)
        print(res)

    elif intent == 'navigationalRoutes':
        navigationDetails = provideNavigationRoutes(docID, specialization)
        res = createResponseForNavigationalInfo(navigationDetails)
        print(res)

    elif intent == 'operationalHours':
        operationalDetails = provideOperationalHours(docID, specialization)
        res = createResponseForOpHoursInfo(operationalDetails)
        print(res)

    elif intent == 'fallback':
        if len(intentList) == 0:
            intentList.pop()
            res = createResponse("Please say Hi or Hello to start your conversation with MediMate Bot")
        elif len(intentList) >= 1:
            intentList.pop()
            if intentList[-1] == 'MedimateWelcomeIntent':
                res = MedimateWelcomeIntent
            elif intentList[-1] == 'New User - yes':
                res = NewUseryes
            elif intentList[-1] == 'New User - no':
                res = NewUseryes
            elif intentList[-1] == 'finddoctors':
                res = finddoc



    elif intent == 'exitConversation':
        quickReplies = [
            "Restart ↻"
        ]
        textForQuickReplies = "If you would like to start the conversation again with Medimate, please choose the option"
        res = createCommonResponse("Thank you for using Medimate. \nHope you get well soon 😀 ", quickReplies,
                                   textForQuickReplies)
        specialization.clear()
        checkListDocID.clear()

    print(res)
    # print("the query response is stored below")
    intentqList.append(res)
    # print(intentqList)
    # print(intentList)
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


def createCommonResponse(fulfilment_text, quickReplies, textForQuickReplies):
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
                    "title": textForQuickReplies,
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


def createResponseForAdditionalInfo(fulfilment_text, quickReplies):
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
                        "Operational Hours ⏳",
                        "Go to services menu",
                        "Exit❌"
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
                        "Navigational Routes 📍",
                        "Go to services menu",
                        "Exit ❌"
                    ]
                },
                "platform": "TELEGRAM"
            }]
    }
    return fulfillmentMessages


def newUserDetails(req, session):
    ['name']
    userName = req['queryResult']['parameters']['user_name']['name']
    userEmail = req['queryResult']['parameters']['user_email']
    # zipCode = req['queryResult']['parameters']['user_zipCode']

    print(userID)
    print(userName)
    print(userEmail)

    if checkUserExistenceByEmail(userEmail.lower()):
        userId = saveUserDetail(session, userEmail.lower(), userName)
        message = "Hey there " + userName + ", welcome to MediMate 🙋‍♀️.\n Your USER ID is : \n" + userId + \
                  '\n \nI will be more than happy if you want to specify the language of the medical expert to speak(Only ONE Language) ' \
                  + '\n(Sorry 🤕, but only these languages are available for now ➡️  English, German , ' \
                          'French , Spanish or Italian) '

        # quickReplies = [
        #     "Find Doctor 🔍",
        #     "Emergency Room Contact 🚨",
        #     "Pharmacy Contact 💊"
        # ]
        textForQuickReplies = 'Please choose any of the below options 👇'
        quickReplies = [
            "It's fine",
            "I would like to specify language",
        ]
        res = createCommonResponse(message, quickReplies, textForQuickReplies)
    else:
        message = 'Ohh! 😕 I see that you are already registered with us. Can you please try again with a different ' \
                  'email Id '
        textForQuickReplies = 'Please choose any of the below options 👇'
        quickReplies = [
            "New user",
            "Existing User",
        ]
        res = createCommonResponse(message, quickReplies, textForQuickReplies)
    # docs = db.collection('Users').where('UserEmail', '==', userEmail).stream()
    # if userEmail in docs:
    #     for doc in docs:
    #         user = doc.to_dict()
    #         user_Id = user['userID']
    #     message = 'Looks like you are already registered with us, Your User Id is ' + user_Id
    #     return message

    return res


def saveUserDetail(session, userEmail, userName):
    global userID
    userIDsplit = userEmail.split("@")
    userId = userIDsplit[0] + "@"
    userId = userId.lower()
    userID.append(userId)

    doc_ref = db.collection(u'Users').document(userId)
    my_data = {'UserName': userName, 'UserEmail': userEmail, 'userID': userId, 'preferredLanguage': ''}
    doc_ref.set(my_data)

    # print(my_data)
    # print(doc_userhistory)
    doc_userhistory = db.collection(u'UserHistory').document(session + '.' + userId)
    my_userHistory = {'userID': userId, 'sessionId': session + '.' + userId}
    doc_userhistory.set(my_userHistory)

    return userId


def saveUserLanguagePreference(request):
    print(userID)
    preferredLanguage = request['queryResult']['parameters']['languageSpecification']

    doc_ref = db.collection(u'Users').document(userID[-1])
    doc_ref.update({u'preferredLanguage': preferredLanguage})

    message = "Understood! \n I would keep in mind while performing the tasks that you prefer " + preferredLanguage
    textForQuickReplies = 'I provide the following services, please choose any option 👇'
    quickReplies = ["Find Doctor 🔍",
                    "Emergency Contacts 🚨",
                    "Pharmacy Contact"
                    ]
    res = createCommonResponse(message, quickReplies, textForQuickReplies)
    return res


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
    userId = userId.lower()
    # print(userId)
    userName = checkUserExistence(userId)
    userID.append(userId)

    if (userName == "") or (userName is None):
        message = "What?? Seems that you are not registered with ME 🙁\n " \
                  "\n Do you now want to register or you would like to re-enter your user-Id to try again?"
        textForQuickReplies = 'Please choose any option 👇'
        quickReplies = [
            "Re-enter",
            "Exit❌"
        ]
        res = createCommonResponse(message, quickReplies, textForQuickReplies)
    else:
        message, doesConvoExist, doesNoteExist = fetchPreviousConversation(userId)
        response = "Welcome back " + str(userName) + ' 🙋‍♀️. \n\n' + message
        if doesConvoExist:
            if doesNoteExist:
                textForQuickReplies = 'Please choose any option 👇'
                quickReplies = [
                    "Exit❌",
                    "Change Language",
                    "Go to services menu"
                ]
                res = createCommonResponse(response + ' \n \nHow would you like to proceed now?', quickReplies,
                                           textForQuickReplies)
            else:
                textForQuickReplies = 'Please choose any option 👇'
                quickReplies = [
                    "Notes📄",
                    "Change Language",
                    "Go to services menu"
                ]
                res = createCommonResponse(response, quickReplies, textForQuickReplies)
        else:
            textForQuickReplies = 'You can choose any from the following'
            quickReplies = [
                "Exit❌",
                "Change Language",
                "Go to services menu",

            ]
            res = createCommonResponse(response, quickReplies, textForQuickReplies)
    return res


def fetchPreviousConversation(userId):
    global session
    message = ''
    specialist = ''
    docName = ''
    note = ''
    emergency = ''
    pharmacy = ''
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
                # print(f'{doc.id} => {doc.to_dict()}')
                if doc.id == 'finddoctors':
                    if doc.to_dict()['intent'] == 'finddoctors':
                        specialist = doc.to_dict()['reply']
                    if doc.to_dict()['intent'] == 'emergencyInfo':
                        emergency = doc.to_dict()['reply']
                    if doc.to_dict()['intent'] == 'pharmacyEmergency':
                        pharmacy = doc.to_dict()['reply']
                if doc.id == 'doctorInfo' or doc.id == 'doctorNumber':
                    docName = doc.to_dict()['reply'].split(':')[1]
                if doc.id == 'requestNotes':
                    note = doc.to_dict()['reply']
                # if doc.id == 'emergencyInfo':
                #     emergency = doc.to_dict()['reply']
                # if doc.id == 'pharmacyEmergency':
                #     pharmacy = doc.to_dict()['reply']
            if note != '':
                return 'You wanted me to remind you the following from your last appointment:\n' \
                       '🔸 Specialist: ' + specialist + ' \n🩺 Name: ' + docName + '\n\n 🎗️ Notes:  ' + note, True, True
            else:
                if specialist != '' and docName != '':
                    return 'Looks like, you were looking for a 🔸' + specialist + '. \nI hope your appointment went ' \
                                                                                  'well with 🩺' + docName + \
                           '.\n\nDo you want me to create a note about the appointment?', True, False
                elif emergency != '':
                    return "You had an EMERGENCY last time, I hope you are better now.\n" \
                           "\nDo you want me to create a note about the appointment?'", True, False
                elif pharmacy != '':
                    return "You had an PHARMACY EMERGENCY last time, I hope you are better now.\n" \
                           "\nDo you want me to create a note about the appointment?'", True, False
                else:
                    return "You had no prior appointments.\n", False, False
    else:
        return "You had no prior appointments.\n", False, False

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
            # print(user_name)

            return user_name
    else:
        # print(u'empty query')
        return ""


def getListofDoctors(req, language):
    i = 1
    doctorID = []
    noDoctorFlag = ""

    parameters = req['queryResult']['parameters']
    # print('Dialogflow parameters:')
    specialization = str(parameters.get('doctorspecialization'))
    language = language.lower()
    print(language)

    result = ["Here is the list of " + specialization + "s" + " to choose from:"]

    if parameters.get('doctorspecialization'):
        if str(parameters.get('doctorspecialization')) == str('general physician'):
            specialization1 = "GeneralPhysician"
            GeneralPhysicians = processLanguage(specialization1, language)
            for doctors in GeneralPhysicians:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + str(i) + '. ' + u'{}'.format(
                    doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('gynaecologist'):
            Gynaecologist = processLanguage(specialization, language)
            for doctors in Gynaecologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + str(i) + '. ' + u'{}'.format(
                    doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('ophthalmologist'):
            Ophthalmologist = processLanguage(specialization, language)
            for doctors in Ophthalmologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + str(i) + '. ' + u'{}'.format(
                    doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('cardiologist'):
            Cardiologist = processLanguage(specialization, language)
            for doctors in Cardiologist:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + str(i) + '. ' + u'{}'.format(
                    doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('dermatologist'):
            pain = processLanguage(specialization, language)
            for doctors in pain:
                docID = u'{}'.format(doctors.to_dict()['DocID'])
                doctorID.append(str(docID))
                # str(i) +
                docName = '👉' + str(i) + '. ' + u'{}'.format(
                    doctors.to_dict()['Name']) + "\n" + "Doctor ID: " + docID + "\n"
                i = i + 1
                result.append(docName)
        elif str(parameters.get('doctorspecialization')) == str('otherdoctors'):
            noDoctorFlag = "yes"

        # print(result)
        if len(result) == 1 and noDoctorFlag == "":
            res = "🙁 Unfortunately, there are no doctors with your requirement. Please try again with a different " \
                  "language of communication. "
            doctorID = []
        elif noDoctorFlag == "yes":
            res = "🙁 Unfortunately, I do not have any doctors for your required specialization in our system / " \
                  "Magdeburg. I request you to seek help from the nearest available doctor outside of Magdeburg. " \
                  "Hope you get well soon. "
            doctorID = []
        else:
            res = "\r\n".join(x for x in result) + "\n" + 'Please enter the ID of a doctor for more info ℹ️'
        print(res)

        return res, specialization, doctorID


def provideDoctorDetails(options, specialization, checkListofDocs):
    options = options.upper()
    url = ''
    hours = ""
    workingHours = ""
    now = datetime.datetime.now()
    currentDay = now.strftime("%A")

    if options in checkListofDocs[0]:
        if specialization[-1] != "general physician":
            Specialization = specialization[-1].capitalize()

        else:
            Specialization = "GeneralPhysician"

        detailedInfo = db.collection(Specialization).document(options)
        info = detailedInfo.get()
        print("prinitng to test okay?")
        print(info)
        OperationalHours = u'{}'.format(info.to_dict()['OperationalHours'])
        OperationalHours = OperationalHours.replace("{", "")
        OperationalHours = OperationalHours.replace("}", "")
        delim = OperationalHours.split(",")
        i = 1
        for opHrs in delim:
            hours += str(i) + "." + opHrs + "\n"
            i += 1

        if hours.find(currentDay) == -1:
            workingHours = "\n\nIt looks like this doctor is not Open on " + currentDay + "s" + '\n'
        else:
            workingHours = "\n\nThis doctor is Open today from " + u'{}'.format(
                info.to_dict()['OperationalHours'][currentDay]) + '\n'

        res = ""
        name = ""
        if info.exists:
            name = "👨‍⚕️ Name : " + u'{}'.format(info.to_dict()['Name'])
            address = "📌 Address : " + u'{}'.format(info.to_dict()['Address'])
            phone = "📞 Phone : " + u'{}'.format(info.to_dict()['Telephone'])

            if 'URL' in info.to_dict():
                url += "🌐 Visit the Doctor's URL : " + u'{}'.format(info.to_dict()['URL'])

            res = name + "\n" + address + "\n" + phone + '\n' + url + '\n' + workingHours

        else:
            res = 'Please make sure to enter the correct Doctor ID 😥'

        print(res)

    else:
        res = "The Doctor ID may be valid but does not meet your language requirements. 😥\n\n You can also try the following website:\n" \
              "https://www.tk-aerztefuehrer.de/TK/englische-suche.htm"
        name = "INVALID"

    return res, name


def processLanguage(specialization, language):
    if (specialization != "GeneralPhysician"):
        Specialization = specialization.capitalize()
        print(Specialization)
    else:
        Specialization = specialization
    if (language != ""):
        doctors = db.collection(Specialization).where(u'languageSpoken', u'array_contains', language).get()
    else:
        doctors = db.collection(Specialization).get()
    return doctors


def provideEmergencyDetails(req):
    emergencyDetails = "Here is a list of Emergency numbers : " + "\n\n"
    emergency = db.collection(u'Emergency').get()
    print(emergency)
    i = 1
    for emergencyInfo in emergency:
        name = " 👨‍⚕ Name : " + " : " + u'{}'.format(emergencyInfo.to_dict()['Name'])
        address = " 📌 Address " + " : " + u'{}'.format(emergencyInfo.to_dict()['Address'])
        phone = " 📞 Phone " + " : " + u'{}'.format(emergencyInfo.to_dict()['Telephone'])
        emergencyDetails += name + "\n" + address + "\n" + phone + "\n\n"
        i = i + 1

    print(emergencyDetails)
    return emergencyDetails


def providePharmacyDetails(req):
    pharmacyDetails = "Here is a list of Pharmacy Emergency numbers : " + "\n\n"
    pharmacy = db.collection(u'Pharmacy').get()
    i = 1
    for pharmacyInfo in pharmacy:
        address = " 📌 Address" + " : " + u'{}'.format(pharmacyInfo.to_dict()['Address'])
        phone = "📞 Phone" + " : " + u'{}'.format(pharmacyInfo.to_dict()['Phone'])
        pharmacyDetails += address + "\n" + phone + "\n\n"
        i = i + 1

    print(pharmacyDetails)
    return pharmacyDetails


def provideNavigationRoutes(docID, specialization):
    print(docID)
    doctorID = docID[-1].upper()
    route = ""

    if (specialization[-1] != "general physician"):
        Specialization = specialization[-1].capitalize()

    else:
        Specialization = "GeneralPhysician"

    detailedInfo = db.collection(Specialization).document(doctorID)
    info = detailedInfo.get()
    if info.exists:
        navigation = u'{}'.format(info.to_dict()['Navigation'])
        navigation = navigation.replace("[", "")
        navigation = navigation.replace("]", "")
        delim = navigation.split(",")
        i = 1
        for routes in delim:
            route += "📍" + str(i) + "." + routes + "\n"
            i += 1
    else:
        route = 'Unfortunately, the routes are not available for this Doctor ID. 😟 '

    print(route)
    return route


def provideOperationalHours(docID, specialization):
    doctorID = docID[-1].upper()
    hours = ""
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
        OperationalHours = OperationalHours.replace("'", "")
        delim = OperationalHours.split(",")
        i = 1
        for opHrs in delim:
            hours += "⌛ " + str(i) + "." + opHrs + "\n"
            i += 1
    else:
        OperationalHours = 'Unfortunately, the working timings are not available for this Doctor ID. 😟'
    ##pleaseworknowpppppsssss
    print(hours)
    return hours


def provideDocDetailNumber(number, specialization, checkListDocID):
    number = int(number)
    print(number)
    # print(len(checkListDocID[0]))
    if (number <= len(checkListDocID[0]) and number != 0):
        doctorInfo, name = provideDoctorDetails(checkListDocID[0][number - 1], specialization, checkListDocID)
        doctorID = checkListDocID[0][number - 1]
    else:
        doctorInfo = "The number you have chosen is INVALID 😟"
        name = "INVALID"
        doctorID = 0

    return doctorInfo, name, doctorID


if __name__ == "__main__":
    app.run(debug=True, port=5004)
