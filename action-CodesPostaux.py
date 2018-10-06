#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
import simplejson
import requests

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error) as e:
        return dict()

def subscribe_intent_callback(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    action_wrapper(hermes, intentMessage, conf)


def action_wrapper(hermes, intentMessage, conf):
    """ Write the body of the function that will be executed once the intent is recognized. 
    In your scope, you have the following objects : 
    - intentMessage : an object that represents the recognized intent
    - hermes : an object with methods to communicate with the MQTT bus following the hermes protocol. 
    - conf : a dictionary that holds the skills parameters you defined. 
      To access global parameters use conf['global']['parameterName']. For end-user parameters use conf['secret']['parameterName'] 
     
    Refer to the documentation for further details. 
    """
    ville = intentMessage.slots.ville.first().value
    print "Intent {}".format(intentMessage.intent)
    response = requests.get("https://public.opendatasoft.com/api/records/1.0/search/?dataset=correspondance-code-insee-code-postal&q="+ville+"&facet=insee_com&facet=nom_dept&facet=nom_region&facet=statut")
    json_data = simplejson.loads(response.text)
    if (intentMessage.intent.intent_name == "codepostal"):
        codepostal = json_data['records'][0]['fields']['postal_code'] 
        result_sentence ="Le code postal de {} est {}.".format(ville,str(codepostal))
    if (intentMessage.intent.intent_name == "departement"):
        departement = json_data['records'][0]['fields']['nom_dept'] 
        numdep = json_data['records'][0]['fields']['code_dept'] 
        result_sentence ="Le département de {} est {} avec le numéro {}.".format(ville,str(departement),str(numdep))

    
    current_session_id = intentMessage.session_id
    hermes.publish_end_session(current_session_id, result_sentence)
    


if __name__ == "__main__":
    with Hermes("localhost:1883") as h:
        h.subscribe_intent("roozeec:codepostal", subscribe_intent_callback) \
         .subscribe_intent("roozeec:departement", subscribe_intent_callback) \
         .start()

