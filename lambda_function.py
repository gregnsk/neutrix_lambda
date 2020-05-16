"""
This skill is loosely based on examples from the Amazon Alexa Skills Kit.

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import json, requests

neutrix_user = "ALEXA@infinidat.com"

#Add the actual token below:
neutrix_token = ""

neutrix_urls = {"East": {"url": "https://ims-dc.infinidat.com:5002", "availability_zone": "East"}, \
        "West": {"url": "https://ims-sv.infinidat.com:5002", "availability_zone": "West"}}
neutrix_url = neutrix_urls['East']['url']
#neutrix_url = neutrix_urls['West']['url']
cookies = None

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def continue_dialog(session_attributes):
    message = {}
    message['shouldEndSession'] = False
    message['directives'] = [{'type': 'Dialog.Delegate'}]
    return build_response(session_attributes, message)

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to new tricks cloud automation. " \
                    "Please give me a credit card number so I can " \
                    "hire some knuckleheads to finish this skill"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "What do you want?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying new tricks. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def summarize_datasets(intent, session, type=None):
    session_attributes = {}
    reprompt_text = None

    print("summarize_datasets called with type %r" % type)
    # get a list of datasets
    get_auth_token()
    r = requests.get("%s/api/dataset" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I was unable to get a list of datasets"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

    datasets = json.loads(r.text)['objects']
    print("got %d datasets from API query" % len(datasets))

    total_size = 0
    count = 0
    for dataset in datasets:
        print("comparing type %s to %s" % (type, dataset['dataset_type'])) 
        if not type or type == dataset['dataset_type']:
            print("got a type match on %r" % dataset)
            total_size += dataset['size_gb']
            count += 1
    if total_size > 2048:
       size_string = "%.1f terabytes" % float(total_size/1000.0)
    else:
       size_string = "%d gigabytes" % total_size
    
    typestring = "datasets" if not type else "%ss" % type   
    speech_output = "You have %d %s with a combined capacity of %s" % \
        (count, typestring, size_string)
    print("SPEAK: %s" % speech_output)
    
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

def list_accounts(intent, session):
    session_attributes = {}
    reprompt_text = None

    # get a list of accounts
    get_auth_token()
    r = requests.get("%s/api/billing" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I got a status %d while querying accounts" % r.status_code
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

    results = json.loads(r.text)
    accounts = len(results['objects'])
    speech_output = "I found %d %s" % (accounts, "account. " if accounts == 1 else "accounts. " )
    for account in results['objects']:
        speech_output += "Account %s is connected to " % account['name']
        clouds = ""
        for connection in account["connections"]:
             if len(clouds):
                 clouds += ", %s" % connection["cloud"]
             else:
                 clouds += "%s" % connection["cloud"]
        # patch up end of string for english syntax
        if len(clouds) > 1:
            clouds = ' and'.join(clouds.rsplit(',', 1))
        speech_output += clouds

    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

def list_arrays(intent, session):
    session_attributes = {}
    reprompt_text = None

    
    # get a list of on-premise storage arrays
    get_auth_token()
    r = requests.get("%s/api/box" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I got a status %d while querying arrays" % r.status_code
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    
    results = json.loads(r.text)
    if len(results['objects']) == 0:
        speech_output = "No on premise eye boxes found"
    elif len(results['objects']) == 1:
        array = results['objects'][0]
        speech_output = "There is one on premise ibox; %s" \
                % (array['name'])
    else:
        speech_output = "I found %d eye boxes; " % len(results['objects'])
        arrays = ""
        for array in results['objects']:
            if len(arrays):
                arrays += ", %s" % array['name']
            else:
                arrays += "%s" % array['name'  ]
        if len(results['objects']) > 1: 
            arrays = ' and'.join(arrays.rsplit(',', 1))
        speech_output += arrays
    
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    
def get_auth_token():
    global cookies
    headers = {"Content-Type": "application/json"}
    payload = {"username": neutrix_user, \
        "password": neutrix_token, "version": "2.1.0"}
    r = requests.post("%s/api/user/login" % neutrix_url, \
        verify=False, data=json.dumps(payload), headers=headers)
        
    # 200 means good login
    if not r.status_code == 200:
        speech_output = "I was unable to login to the new tricks cloud server"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

    cookies = r.cookies

def list_connections(intent_request, session):
    session_attributes = {}
    reprompt_text = None
    intent = intent_request['intent']
    
    if 'dialogState' in intent_request.keys():
        dialog_state = intent_request['dialogState']
        if dialog_state in ("STARTED", "IN_PROGRESS"):
            return continue_dialog(session_attributes)
    
    get_auth_token()
    
    # get a list of accounts
    r = requests.get("%s/api/billing" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I got a status %d while querying account data" % r.status_code
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

    results = json.loads(r.text)
    accounts = {}
    for account in results['objects']:
       accounts[account['name']] = account

    speech_output = "I found %d %s" % (len(accounts), "account. " if len(accounts) == 1 else "accounts. ")
    for account in results['objects']:
        if account['name'] == "AWSdemoEC":
            accname = "Neutrix Demo East Coast"
        else:
            accname = account['name']
        speech_output = "%s is connected to " % accname
        clouds = ""
        for connection in account["connections"]:
             if connection["cloud"]=="vmcaws":
                 cloudconnection="Vee Am Ware on AWS"
             else:
                 cloudconnection=connection["cloud"]
             if len(clouds):
                 clouds += ", %s" % cloudconnection
             else:
                 clouds += "%s" % cloudconnection
        # patch up end of string for english syntax
        if len(clouds) > 1:
            clouds = ' and'.join(clouds.rsplit(',', 1))
        speech_output += clouds + ". "

    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

def query_volume(request, session, type=None):
    session_attributes = {}
    intent = request['intent']

    if 'dialogState' in request.keys():
        dialog_state = request['dialogState']
        if dialog_state in ("STARTED", "IN_PROGRESS"):
            return continue_dialog(session_attributes)
        else:
            print("REQUEST STATE: %r" % request)
            
    volume_id = int(intent['slots']['volume_id']['value'])
    return list_datasets(intent, session, id=volume_id)
    
def list_datasets(intent, session, type=None, id=None):
    session_attributes = {}
    reprompt_text = None

    print("list_datasets called with type %r" % type)
    # get a list of datasets
    get_auth_token()
    r = requests.get("%s/api/dataset" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I was unable to get a list of datasets"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

    datasets = json.loads(r.text)['objects']
    print("got %d datasets from API query" % len(datasets))

    dslist = ""
    total_size = 0
    nodesc_count = 0
    count = 0
    for dataset in datasets:
        if id:
            if int(dataset['id']) == id:
                total_size += dataset['size_gb']
                break
        elif not type or type == dataset['dataset_type']:
            count += 1
            print("got a type match on %r" % dataset)
            total_size += dataset['size_gb']
            if dataset['description']:
                if len(dslist):
                    dslist += ", %s" % dataset["description"]
                else:
                    dslist += "%s" % dataset["description"]
            else:
                nodesc_count += 1
    
    # short-circuit path if we're searching for a specific id
    if id: 
        if int(dataset['id']) == id:
            if 'host_mappings' in dataset.keys():
                maps = ""
                for map in dataset['host_mappings']:
                    print("MAP: %r" % map)
                    maps += ", %s" % map['name'] if len(maps) else map['name']
                if len(dataset['host_mappings']) > 1: 
                    map_verbage = "is mapped to %s" % \
                         ', and'.join(dslist.rsplit(',', 1))
                else:
                    map_verbage = "is mapped to %s" % maps
            else:
                map_verbage = "is not mapped to any hosts"
            speech_output = "Volume %s is %s gigabytes and %s" % \
                    (id, dataset['size_gb'], map_verbage)
        else:
            speech_output = "I didn't find volume %s in the system" % id
    else:
        if nodesc_count:
            dslist += ", %d %s%s without a description" % (nodesc_count, 
                    "data sets" if not type else type, 
                    "s" if nodesc_count > 1 else "")
                
        # patch up end of string for english syntax
        if count >= 1:
            speech_output = ', and'.join(dslist.rsplit(',', 1))


    print("SPEAK: %s" % speech_output)
    
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

def list_hosts(intent, session):
    session_attributes = {}
    reprompt_text = None

    # get a list of datasets
    get_auth_token()
    r = requests.get("%s/api/host" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I was unable to get a list of datasets"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

    hosts = json.loads(r.text)['objects']
    print("got %d hosts from API query" % len(hosts))
    all_hosts = ""
    nodesc_count = 0
    count = len(hosts)
    for host in hosts:
        if host['name']:
            if len(all_hosts):
                all_hosts += ", %s" % host["name"]
            else:
                all_hosts += "%s" % host["name"]
        else:
            nodesc_count += 1
    if nodesc_count:
        if count == nodesc_count:
            all_hosts += "You have %d host%s, and none of them have a description." % \
                    (count, "s" if count > 1 else "")
        else:
            all_hosts += "%s, and %d host%s without a description" % \
                    ("," if count > nodesc_count else "", nodesc_count, 
                        "s" if nodesc_count > 1 else "")

    # patch up end of string for english syntax
    if count >= 1:
            speech_output = 'There are '+str(count) + ' hosts found. Host names are '+', and'.join(all_hosts.rsplit(',', 1))

    print("SPEAK: %s" % speech_output)
    
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))
        
def create_dataset(request, session, type):      
    intent = request['intent']
    session_attributes = {}
    headers = {"Content-Type": "application/json"}

    reprompt_text = None
    
    if 'dialogState' in request.keys():
        dialog_state = request['dialogState']
        if dialog_state in ("STARTED", "IN_PROGRESS"):
            return continue_dialog(session_attributes)
        else:
            print("REQUEST STATE: %r" % request)
            
    size_gb = int(intent['slots']['size_gb']['value'])

    get_auth_token()
    obj_type = None
    if type == 'VOLUME':
        obj_type = 'vol'
    elif type == 'FILESYSTEM':
        obj_type = 'fs'
    else:
        speech_output = "Bad dataset type passed to create dataset function"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
                intent['name'], speech_output, reprompt_text, should_end_session))
    data = {"obj_type":obj_type,"size_gb":size_gb,"description":"Alexa demo volume"} 
    print("PAYLOAD: %s" % json.dumps(data))            
    r = requests.post("%s/api/dataset" % neutrix_url, \
        verify=False, json=data, headers=headers, cookies=cookies)
    print("URL: %s/api/dataset" % neutrix_url)
    print("STATUS CODE: %d" % r.status_code)
    if r.status_code == 201:
        results = json.loads(r.text)
        speech_output = "%s ID %d has been created with %d gigabytes of space" % (type, results["id"], size_gb)
        data = {"obj_type":obj_type,"uuid": results["uuid"],"description":"Alexa demo " + obj_type + " "+str(results["id"])}
        print("PAYLOAD: %s" % json.dumps(data))
        puturl = neutrix_url + "/api/dataset/" + results["uuid"]
        r = requests.put(puturl, \
            verify=False, json=data, headers=headers, cookies=cookies)    
        print("URL: %s" % puturl)
        print("STATUS CODE: %d" % r.status_code)
    else:
        speech_output = "The REST A.P.I. command returned status code %s"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))


def destroy_dataset(request, session, type):      
    intent = request['intent']
    session_attributes = {}
    headers = {"Content-Type": "application/json"}

    reprompt_text = None
    
    if 'dialogState' in request.keys():
        dialog_state = request['dialogState']
        if dialog_state in ("STARTED", "IN_PROGRESS"):
            return continue_dialog(session_attributes)
        else:
            print("REQUEST STATE: %r" % request)
            
    volume_id = int(intent['slots']['volume_id']['value'])

    # get a list of datasets and try to find the specified volume ID
    get_auth_token()
    r = requests.get("%s/api/dataset" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I was unable to get a list of datasets"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    print("AUTHENTICATION: success!")
    
    dataset = None
    datasets = json.loads(r.text)['objects']
    for tdataset in datasets:
        if tdataset['id'] == volume_id:
            print("DATASET: %r" % tdataset)
            dataset = tdataset
            break

    if not dataset:
        speech_output = "I didn't find a volume with id %s" % volume_id
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    
    # destroy the dataset using it's uuid
    url = "%s/api/dataset/%s" % (neutrix_url,dataset['uuid'])
    r = requests.delete(url, verify=False, cookies=cookies) 
    if r.status_code == 204:
        speech_output = "OK, volume %d has been DESTROYED!!!" % volume_id
    else:
        speech_output = "REST response code %d" % r.status_code
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

    
def unmap_volume(request, session):
    print("CALL: unmap_volume()")
    return map_volume(request, session, unmap=True)
    
def map_volume(request, session, unmap=False):   
    intent = request['intent']
    session_attributes = {}
    headers = {"Content-Type": "application/json"}
    command = "map" if not unmap else "unmap"
    print("CALL: map_volume(%s)" % command)

    reprompt_text = None
    
    if 'dialogState' in request.keys():
        dialog_state = request['dialogState']
        if dialog_state in ("STARTED", "IN_PROGRESS"):
            return continue_dialog(session_attributes)
        else:
            print("REQUEST STATE: %r" % request)

    # get a list of datasets and try to find the specified volume ID
    get_auth_token()
    r = requests.get("%s/api/dataset" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I was unable to get a list of datasets"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    print("AUTHENTICATION: success!")
    
    dataset = None
    datasets = json.loads(r.text)['objects']
    for tdataset in datasets:
        if tdataset['id'] == int(intent['slots']['volume_id']['value']):
            print("DATASET: %r" % tdataset)
            dataset = tdataset
            break
    print("DATASET GET: success!")

    if not dataset:
        speech_output = "I didn't find a volume with id %s" % int(intent['slots']['volume_id']['value'])
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    
    # get a list of hosts and find a match for our request
    r = requests.get("%s/api/host" % neutrix_url, verify=False, cookies=cookies)
    if not r.status_code == 200:
        speech_output = "I was unable to get a list of hosts"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    
    host = None
    hosts = json.loads(r.text)['objects']
    for thost in hosts:
        if thost['name'].lower() == intent['slots']['host']['value'].lower():
            print("HOST: %r" % thost)
            host = thost
            break
    
    if not host:
        speech_output = "I didn't find a host named %s" % intent['slots']['host']['value']
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    payload = {command: dataset['uuid'], "name": host['name']}
    url = "%s/api/host/%s" % (neutrix_url,host['name'])
    print("PUT: %s" % url)
    print("PAYLOAD: %s" % json.dumps(payload))
    r = requests.put(url, json=payload, verify=False, cookies=cookies) 
    print("STATUS: %s" % r.text)
    
    if r.status_code == 200:
        if not unmap:
          speech_output = "OK, I mapped volume %s to host %s" % (dataset['id'], host['name'])
        else:
          speech_output = "OK, I unmapped volume %s from host %s" % (dataset['id'], host['name'])
    else:
        speech_output = "The REST API operation returned a status code of %d, with the text, %s" % (r.status_code, r.text)
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    print("INTENT: %s" % intent_request['intent']['name'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "ListAccounts":
        return list_accounts(intent, session)
    elif intent_name == "ListConnections":
        return list_connections(intent_request, session)
    elif intent_name == "ListArrays":
        return list_arrays(intent, session)
    elif intent_name == "ListHosts":
        return list_hosts(intent, session)
    elif intent_name == "ListVolumes":
        return list_datasets(intent, session, type='VOLUME')
    elif intent_name == "ListFilesystems":
        return list_datasets(intent, session, type='FILESYSTEM')
    elif intent_name == "ListDatasets":
        return list_datasets(intent, session)
    elif intent_name == "QueryVolume":
        return query_volume(intent_request, session)
    elif intent_name == "DatasetSummary":
        return summarize_datasets(intent, session)
    elif intent_name == "VolumeSummary":
        return summarize_datasets(intent, session, type='VOLUME')
    elif intent_name == "FilesystemSummary":
        return summarize_datasets(intent, session, type='FILESYSTEM')
    elif intent_name == "CreateVolume":
        return create_dataset(intent_request, session, type='VOLUME')
    elif intent_name == "DestroyVolume":
        return destroy_dataset(intent_request, session, type='VOLUME')
    elif intent_name == "CreateFilesystem":
        return create_dataset(intent_request, session, type='FILESYSTEM')
    elif intent_name == "MapVolume":
        return map_volume(intent_request, session)
    elif intent_name == "UnmapVolume":
        return unmap_volume(intent_request, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        print("We got intent %s" % intent_name)
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

