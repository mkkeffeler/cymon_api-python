#!/az/arcsight/counteract_scripts/env/bin/python
#Miclain Keffeler
#6/8/2017
#This script pulls the most recent events/malware/URLs that have been submitted as suspicious or malicious from cymon.io. Eventually this information will be automatically parsed and stored so that if a new malware tried to enter a network it could be searched quickly in this up-to-date table and potentially stopped from entering. 
import requests
import sys
import json
from optparse import OptionParser
import hashlib
import base64
import socket
from sqlalchemy import Column, Text, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import types
from sqlalchemy import exists
import dateutil.parser
from sqlalchemy.sql.expression import literal_column
from cef_event import generate_cef_event
import os
from configparser import ConfigParser
import getpass
import codecs
import datetime


config = ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '../config.ini'))
HOST = config.get('DEFAULT', 'HOST')                          #Get Hostname and Port to send CEF event to from Config.INI file
PORT = config.get('DEFAULT', 'PORT')
token = config.get('DEFAULT', 'TOKEN')                          #Get API Key and Password from Config.INI file
proxies = config.get('DEFAULT','Proxies')

if(proxies == ""):
    auth = ""
else:
    proxies = {"https": 'https://' + proxies}


last_filename = ""
filename = "recent_feed-" + str(datetime.datetime.now().strftime('%FT%TZ')) + ".json"

with open(os.path.join(os.path.dirname(__file__), '.namelastcall')) as f:   #Get the name of last feed that was pulled 
    lines = f.readlines()
    if( not lines):
        last_filename = "None"
    else:
        for line in lines: 
            last_filename = line
    f.close()

output = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),filename),"w")   #Open file for writing 
link = "https://cymon.io/api/dashboard/v1/recent-objects/"
response1 = ""
if(proxies == ""): #If a proxy has been specified in config
    response = requests.get(link,headers = {'Authorization': token,'content-type':"application/json"},proxies=proxies)
else:
    response = requests.get(link,headers = {'Authorization': token,'content-type':"application/json"}, proxies=proxies)
all_json = response.json()
output.write(json.dumps(all_json,indent=4,sort_keys=True))

past_filename = last_filename

def which_field(category):   #get the appropriate field for parsing threat intel json
    if(category == 'recent_domains'):
        return 'name'
    if(category == 'recent_ips'):
        return 'addr'
    if(category == 'recent_urls'):
        return 'location'

engine = create_engine('sqlite:///IP_Report.db')
DBSession = sessionmaker(bind = engine)
session = DBSession()

CONFIG = {}
def syslog(message, level=5, facility=5, host=HOST, port=int(PORT)):   #Used to send the CEF event to the provided host and port specified in config.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = '<%d>%s' % (level + facility*8, message)
        sock.sendto(data.encode(), (host, (port)))
        sock.close()

CONFIG['FACILITY'] = {
        'kern': 0, 'user': 1, 'mail': 2, 'daemon': 3,
        'auth': 4, 'syslog': 5, 'lpr': 6, 'news': 7,
        'uucp': 8, 'cron': 9, 'authpriv': 10, 'ftp': 11,
        'local0': 16, 'local1': 17, 'local2': 18, 'local3': 19,
        'local4': 20, 'local5': 21, 'local6': 22, 'local7': 23,
}

CONFIG['LEVEL'] = {
        'emerg': 0, 'alert':1, 'crit': 2, 'err': 3,
        'warning': 4, 'notice': 5, 'info': 6, 'debug': 7
}
#Array of event_types global
event_types = ['recent_domains','recent_ips','recent_urls']

def date_parse(date_string):          #This function parses the date that comes from the raw JSON output and puts it in a Month/Day/Year format

    parsed_date = dateutil.parser.parse(date_string).strftime("%x")
    return parsed_date


if __name__ == "__main__":
    found_match=0
    if(last_filename == "None"):  #If this is the first run of the script locally
        for category in event_types:
            feed_data = all_json['data'][category]
            for entry in feed_data:
                event = generate_cef_event(category,entry[which_field(category)],entry['updated'])
                syslog(event)
                print(event)
    else:  #Otherwise, load old json to compare to 
        past_json = json.load(open(os.path.join(os.path.dirname(__file__), last_filename.strip('\n')),'r'))
        for category in event_types:
            past_feed_data = past_json['data'][category]
            feed_data = all_json['data'][category]
            for entry in feed_data:
                for past_entry in past_feed_data:
                    print ("PAST: " + past_entry[which_field(category)] + " CUR: " + entry[which_field(category)])
                    if(entry[which_field(category)] == past_entry[which_field(category)]):
                        print ("NO GO")
                        found_match = 1
                        break
                    else:
                        found_match = 0
                if(found_match == 0):
                    print ("PUSHED")
                    event = generate_cef_event(category,entry[which_field(category)],entry['updated'])
                    syslog(event)
                    got_pushed = 1
            got_pushed = 0
            found_match = 0
    if(last_filename == "None"):   
        checked = 0
    else:   #Be sure to remove old file so we don't take up diskspace
        os.remove(os.path.join(os.path.dirname(os.path.abspath(__file__)),last_filename[:-1]))
with open(os.path.join(os.path.dirname(__file__), '.namelastcall'),'w') as f:   #Set new name of file for next run
    f.write(filename)
    f.close()
