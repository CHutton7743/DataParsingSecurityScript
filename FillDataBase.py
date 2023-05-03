import json
import math

import pandas as pd
import requests
import http.client
import ssl

class HitrustControl:
    def __init__(self, control_function, control_category, control_name, control_description, nist_mapping):
        self.control_function = control_function
        self.control_category = control_category
        self.control_name = control_name
        self.control_description = control_description
        self.nist_mapping = nist_mapping

    # getters and setters
    def get_control_function(self):
        return self.control_function
    def set_control_function(self, control_function):
        self.control_function = control_function
    def get_control_category(self):
        return self.control_category
    def set_control_category(self, control_category):
        self.control_category = control_category
    def get_control_name(self):
        return self.control_name
    def set_control_name(self, control_name):
        self.control_name = control_name
    def get_control_description(self):
        return self.control_description
    def set_control_description(self, control_description):
        self.control_description = control_description
    def get_nist_mapping(self):
        return self.nist_mapping
    def set_nist_mapping(self, nist_mapping):
        self.nist_mapping = nist_mapping

    def __str__(self):
        data = {
            "control_function": self.control_function,
            "control_category": self.control_category,
            "control_name": self.control_name,
            "control_description": self.control_description,
            "nist_mapping": self.nist_mapping
        }
        return json.dumps(data)

class NistControl:
    def __init__(self, control_function, control_category, control_name, control_description, hitrust_mapping):
        self.control_function = control_function
        self.control_category = control_category
        self.control_name = control_name
        self.control_description = control_description
        self.hitrust_mapping = hitrust_mapping

    # getters and setters
    def get_control_function(self):
        return self.control_function
    def set_control_function(self, control_function):
        self.control_function = control_function
    def get_control_category(self):
        return self.control_category
    def set_control_category(self, control_category):
        self.control_category = control_category
    def get_control_name(self):
        return self.control_name
    def set_control_name(self, control_name):
        self.control_name = control_name
    def get_control_description(self):
        return self.control_description
    def set_control_description(self, control_description):
        self.control_description = control_description
    def get_hitrust_mapping(self):
        return self.hitrust_mapping
    def set_hitrust_mapping(self, hitrust_mapping):
        self.hitrust_mapping = hitrust_mapping

    def __str__(self):
        data = {
            "control_function": self.control_function,
            "control_category": self.control_category,
            "control_name": self.control_name,
            "control_description": self.control_description,
            "hitrust_mapping": self.hitrust_mapping
        }
        return json.dumps(data)

csvFile = '/Users/codeyhutton/Downloads/NIST-to-HITRUST-ffilled.csv'
# '/Users/codeyhutton/Downloads/NIST_CSF_-_HITRUST_mapping.csv' is the path to the csv file

# Create the dataframe filled with all the control data
df = pd.read_csv(csvFile)

# Define the regex pattern to extract the subcategory name and description
regex_sub = r'(\w+\.\w+-\d+):\s(.*)'

# Extract the subcategory name and description into separate columns
df[['Subcategory ID', 'Subcategory Description']] = df['Subcategory'].str.extract(regex_sub)

# Drop the original "Subcategory" column
df.drop('Subcategory', axis=1, inplace=True)

# Define the regex pattern to extract the category name and description
regex = r'(\d+\.\d+\w+\.\d+)\n(.*)\n'

# extract the control name and description from the 'Control Requirement' column
category = df['Control Requirement'].str.extract(regex)

# add the control name and description to the dataframe as seperate columns
df['Control Name'] = category[0]
df['Control Description'] = category[1]

# drop the original 'Control Requirement' column and all uneeded columns
df.drop('Control Requirement', axis=1, inplace=True)
df.drop("Status", axis=1, inplace=True)
df.drop("Status.1", axis=1, inplace=True)
df.drop("Status.2", axis=1, inplace=True)
df.drop("Unnamed: 0", axis=1, inplace=True)

# run through the entire dataframe and make sure there are no NaNs
df.fillna('', inplace=True)

nistURL = 'http://localhost:8080/api/v1/nist_control'
hitrustURL = 'http://localhost:8080/api/v1/hitrust_control'

# Obtain access token
payload = "{\"client_id\":\"gDlsZn8ocSc09nSbn3GWgds0gc34MqIY\",\"client_secret\":\"oDK8YufBhG0jynz9EGDnpTA_EfcV4vZXTgTxapv17PhyXX488BFtZtycvEtD8kKt\",\"audience\":\"Controlcognizant Bellevue College\",\"grant_type\":\"client_credentials\"}"

headers = { 'content-type': "application/json" }

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

conn = http.client.HTTPSConnection("dev-fdttbtxtdt0dkcxz.us.auth0.com", context=context)
conn.request('POST', '/oauth/token', payload, headers)

res = conn.getresponse()
data = res.read()

accessToken = json.loads(data.decode("utf-8"))['access_token']


# Make POST request with access token
headers = {'Authorization': 'Bearer ' + accessToken}


# insert entities into control table in the database loop through each row of the dataframe and ping each entity to the spring boot api
check = False
for index, row in df.iterrows():
    # def __init__(self, control_function, control_category, control_name, control_description, nist_mapping):
    hitrust_control = HitrustControl(row['Function'], row['Category'], row['Control Name'], row['Control Description'], row['Subcategory ID'])
    # def __init__(self, control_function, control_category, control_name, control_description, hitrust_mapping):
    nist_control = NistControl(row['Function'], row['Category'], row['Subcategory ID'], row['Subcategory Description'], row['Control Name'])
    # check if nist_control has the same name as the previous nist_control
    # if check == row['Subcategory ID']:
    #     response2 = requests.post(nistURL, json=json.loads(nist_control.__str__()), headers=headers)
    response1 = requests.post(hitrustURL, json=json.loads(hitrust_control.__str__()), headers=headers)
    # print("Hitrust Control Status: " + response1.text)
    # print("Nist Control Status: " + response2.text)
    check = row['Subcategory ID']
