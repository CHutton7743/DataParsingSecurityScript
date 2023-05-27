import json
import math

import pandas as pd
import requests
import http.client
import ssl

class HitrustControl:
    def __init__(self, control_function, control_category, control_name, control_description, nist_mappings):
        self.controlFunction = control_function
        self.controlCategory = control_category
        self.controlName = control_name
        self.controlDescription = control_description
        self.nistMappings = nist_mappings

    def __str__(self):
        data = {
            "controlFunction": self.controlFunction,
            "controlCategory": self.controlCategory,
            "controlName": self.controlName,
            "controlDescription": self.controlDescription,
            "mappings": str(self.nistMappings)
        }
        return json.dumps(data)

class NistControl:
    def __init__(self, control_function, control_category, control_name, control_description, hitrust_mappings):
        self.controlFunction = control_function
        self.controlCategory = control_category
        self.controlName = control_name
        self.controlDescription = control_description
        self.hitrustMappings = hitrust_mappings
    def __str__(self):
        data = {
            "controlFunction": self.controlFunction,
            "controlCategory": self.controlCategory,
            "controlName": self.controlName,
            "controlDescription": self.controlDescription,
            "mappings": str(self.hitrustMappings)
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


# Obtain access token
payload = "{\"client_id\":\"\",\"client_secret\":\"\",\"audience\":\"\",\"grant_type\":\"\"}"

headers = { 'content-type': "application/json" }

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

conn = http.client.HTTPSConnection("dev-....us.auth0.com", context=context)
conn.request('POST', '/oauth/token', payload, headers)

res = conn.getresponse()
data = res.read()

accessToken = json.loads(data.decode("utf-8"))['access_token']


# Make POST request with access token
headers = {'Authorization': 'Bearer ' + accessToken,
           'Content-Type': 'application/json'}


# insert entities into control table in the database loop through each row of the dataframe and ping each entity to the spring boot api
hitrust_controls = {}
nist_controls = {}
hitrust_ids = {}
nist_ids = {}

update_hitrust = 'http://localhost:8080/api/v1/hitrust_control/update/{id}'
update_nist = 'http://localhost:8080/api/v1/nist_control/update/{id}'
nistURL = 'http://localhost:8080/api/v1/nist_control/create'
hitrustURL = 'http://localhost:8080/api/v1/hitrust_control/create'

# Step 1: Process each row in the dataframe
for index, row in df.iterrows():
    nist_control_name = row['Subcategory ID']
    hitrust_control_name = row['Control Name']

    # Check if NIST control exists
    if nist_control_name in nist_controls:
        nist_control = nist_controls[nist_control_name]
    else:
        # def __init__(self, control_function, control_category, control_name, control_description, hitrust_mapping):
        nist_control = NistControl(row['Function'], row['Category'], nist_control_name, row['Subcategory Description'], [])
        nist_controls[nist_control_name] = nist_control

    # Check if HITRUST control exists
    if hitrust_control_name in hitrust_controls:
        hitrust_control = hitrust_controls[hitrust_control_name]
    else:
        # def __init__(self, control_function, control_category, control_name, control_description, nist_mapping):
        hitrust_control = HitrustControl(row['Function'], row['Category'], hitrust_control_name, row['Control Description'], [])
        hitrust_controls[hitrust_control_name] = hitrust_control

    # Update mappings for HITRUST control
    if nist_control_name in nist_controls:
        nist_mappings = hitrust_control.nistMappings
        if nist_control_name not in nist_mappings:
            nist_mappings.append(nist_control_name)
            hitrust_control.nistMappings = nist_mappings

    # Update mappings for NIST control
    if hitrust_control_name in hitrust_controls:
        hitrust_mappings = nist_control.hitrustMappings
        if hitrust_control_name not in hitrust_mappings:
            hitrust_mappings.append(hitrust_control_name)
            nist_control.hitrustMappings = hitrust_mappings

# Remove mappings from the copied control dictionaries
for nist_control_name, nist_control_copy in nist_controls.items():
    unique_hitrust_mappings = set()  # Initialize a set to store unique hitrust mappings
    for hitrust_mapping in nist_control_copy.hitrustMappings:
        unique_hitrust_mappings.add(hitrust_mapping)  # Add hitrust mapping to the set
    nist_control_copy.hitrustMappings = list(unique_hitrust_mappings)  # Convert set back to list

for hitrust_control_name, hitrust_control_copy in hitrust_controls.items():
    unique_nist_mappings = set()  # Initialize a set to store unique nist mappings
    for nist_mapping in hitrust_control_copy.nistMappings:
        unique_nist_mappings.add(nist_mapping)  # Add nist mapping to the set
    hitrust_control_copy.nistMappings = list(unique_nist_mappings)  # Convert set back to list

import copy
# Step 2: Create copies of the control dictionaries without mappings
nist_controls_copy = copy.deepcopy(nist_controls)
hitrust_controls_copy = copy.deepcopy(hitrust_controls)

# Remove mappings from copied control objects
for nist_control_name, nist_control_copy in nist_controls_copy.items():
    nist_control_copy.hitrust_mappings = None

for nist_control_name, hitrust_control_copy in hitrust_controls_copy.items():
    hitrust_control_copy.nist_mappings = None

# Step 3: Create entities without mappings
# Create NIST controls
for nist_control_name, nist_control_copy in nist_controls_copy.items():
    payload = json.dumps(nist_control_copy.__dict__)
    response = requests.post(nistURL, data=payload, headers=headers)
    nist_id = json.loads(response.text)['id']
    nist_ids[nist_control_name] = nist_id

# Create HITRUST controls
for hitrust_control_name, hitrust_control_copy in hitrust_controls_copy.items():
    payload = json.dumps(hitrust_control_copy.__dict__)
    response = requests.post(hitrustURL, data=payload, headers=headers)
    hitrust_id = json.loads(response.text)['id']
    hitrust_ids[hitrust_control_name] = hitrust_id

# Step 4: Update entities with mappings
# update NIST controls
# Update NIST controls
for nist_control_name, nist_control in nist_controls.items():
    id = nist_ids[nist_control_name]
    payload = json.dumps(nist_control.__dict__)
    response = requests.put(update_nist.format(id=id), data=payload, headers=headers)

    if response.status_code == 201:
        print(f"NIST control '{nist_control_name}' updated successfully.")
    else:
        print(f"Failed to update NIST control '{nist_control_name}': {response.text}")

# Update HITRUST controls
for hitrust_control_name, hitrust_control in hitrust_controls.items():
    id = hitrust_ids[hitrust_control_name]
    payload = json.dumps(hitrust_control.__dict__)
    response = requests.put(update_hitrust.format(id=id), data=payload, headers=headers)

    if response.status_code == 200:
        print(f"HITRUST control '{hitrust_control_name}' updated successfully.")
    else:
        print(f"Failed to update HITRUST control '{hitrust_control_name}': {response.text}")
print("done")





#  Testing scripts below this line
#  testing the get request for all categories and functions
# CHECK
# categories = set()
# categories = requests.get('http://localhost:8080/api/v1/categories', headers=headers).json()
#
# # CHECK
# functions = set()
# functions = requests.get('http://localhost:8080/api/v1/functions', headers=headers).json()
# #
# print('categories = '+str(categories))
# print('functions = '+str(functions))

# testing the get request for all nist controls
# CHECK
# controls = set()
# controls = requests.get('http://localhost:8080/api/v1/nist_control/get_all_controls', headers=headers).json()
#
# print('controls = '+str(controls))

# testing the get request for all hitrust controls
# CHECK
# controls = set()
# controls = requests.get('http://localhost:8080/api/v1/hitrust_control/get_all_controls', headers=headers).json()
#
# print('controls = '+str(controls))

# testing the get request for all nist controls by function /api/v1/nist_control/{control_function}
# CHECK
# controls = set()
# control_function = 'PROTECT(PR)'
# url = f'http://localhost:8080/api/v1/nist_control/by_function/{control_function}'
# controls = requests.get(url, headers=headers).json()
#
# print('controls = '+str(controls))

# testing the get request for all nist controls by category
# CHECK
# controls = set()
# control_category = 'Protect: Data Security (PR.DS)'
# url = f'http://localhost:8080/api/v1/nist_control/by_category/{control_category}'
# controls = requests.get(url, headers=headers).json()
#
# print('controls = '+str(controls))

# testing the get request for a single hitrust control
# CHECK
# control_id = 52
# url = f'http://localhost:8080/api/v1/hitrust_control/get_one/{control_id}'
# control = requests.get(url, headers=headers).json()
#
# print('control = '+str(control))


# testing the get request for a single nist control
# CHECK
# control_id = 900
# url = f'http://localhost:8080/api/v1/nist_control/get/{control_id}'
# control = requests.get(url, headers=headers).json()
#
# print('control = '+str(control))

# testing the get request for getting all hitrust controls by category
# CHECK
# controls = set()
# control_category = 'Protect: Awareness and Training (PR.AT)'
# url = f'http://localhost:8080/api/v1/hitrust_control/category/{control_category}'
# controls = requests.get(url, headers=headers).json()
#
# print('controls = '+str(controls))

# testing the get request for getting all hitrust controls by function
# CHECK
# controls = set()
# control_category = 'PROTECT(PR)'
# url = f'http://localhost:8080/api/v1/hitrust_control/function/{control_category}'
# controls = requests.get(url, headers=headers).json()
#
# print('controls = '+str(controls))

# testing the get request for finding all hitrust controls by nist mapping
# CHECK
# controls = set()
# nist_mapping = 'PR.AT-1'
# url = f'http://localhost:8080/api/v1/hitrust_control/mapping/{nist_mapping}'
# controls = requests.get(url, headers=headers).json()
#
# print('controls = '+str(controls))

#  test the get request for finding a nist control by hitrust mapping
# CHECK
# control = set()
# hitrust_mapping = '1442.09f2System.456'
# url = f'http://localhost:8080/api/v1/nist_control/mapping/{hitrust_mapping}'
# control = requests.get(url, headers=headers).json()
#
# print('control = '+str(control))

# testing the get request for getting all controls
# CHECK
# controls = set()
# url = f'http://localhost:8080/api/v1/control/get_all_controls'
# controls = requests.get(url, headers=headers).json()
#
# print('controls = '+str(controls))

# testing the get request for getting all
