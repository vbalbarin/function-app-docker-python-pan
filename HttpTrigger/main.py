import logging
import json
import secrets

from os import environ

import azure.functions as func

def temp_auth_code():
  return secrets.token_urlsafe(32)

def primary_private_ip(ip_configs):
  """ This function extracts primary, private ipaddress """
  return [ip['properties']['privateIPAddress']
    for ip in ip_configs if ip['properties']['primary']][0]

def palo_alto_tags(azure_dict, namespace='', delim='|'):
  """This function takes a dictionary of MS Azure tags and returns  a list
  of Palo Alto Networks formatted tags, takes an optional namespace for prefix for pan tag element"""
  prefix = 'azure'
  if len(namespace) != 0:
    prefix = prefix + delim + namespace
  pan_tags = []
  try:
    for tag, value in azure_dict.items():
      pan_tags.append(prefix + delim + tag + delim + value)
  except:
    pan_tags.append(prefix + delim + 'None')
  return pan_tags

def palo_alto_ip(post_req_data):
  """This function takes a JSON payload from the webhook and emits a dictionary of {"ip": []}"""
  try:
    nic = json.loads(post_req_data['properties']['responseBody'])
    return {
      primary_private_ip(nic['properties']['ipConfigurations']):
      palo_alto_tags(nic['tags'], namespace='nic|tags')
    }
  except:
    return {"": []}

def main(req: func.HttpRequest) -> func.HttpResponse:
  """ Azure Function App Execution Loop """

  logging.info('Python HTTP trigger function processed a request.')
  
  # Check for AUTH_CODE in OS environment
  AUTH_CODE = environ.get('AUTH_CODE')
  if AUTH_CODE is None:
    auth_code = temp_auth_code()
    logging.info('AUTH_CODE environment variable not found.')
    logging.info(f'Setting AUTH_CODE = {auth_code}')
    environ['AUTH_CODE'] = auth_code
    return func.HttpResponse(
      body=f'A new authorization code generated. Please record this value; it will be available only at this time: {auth_code}',
      status_code=200)
  
  logging.info('AUTH_CODE environment variable found.')
  
  code = req.params.get('code')
  logging.info('Checking for valid auth code supplied in query string.')
  # TODO: check for code in req.header.
  if not code:
    return func.HttpResponse(
      body='A valid authorization code must be supplied in the query string',
      status_code=401)
  elif code != AUTH_CODE:
    return func.HttpResponse(
      body='Authorization code is invalid',
      status_code=401)

  logging.info('Code supplied on query string matches AUTH_CODE.')
  
  try:
    req_body = req.get_json()
    response_body = json.loads(req_body['properties']['responseBody']) # responseBody of webhook is string
    ip_address = json.dumps(palo_alto_ip(req_body))
    return func.HttpResponse(
      body=ip_address,
      mimetype='application/json',
      status_code=200)
  except:
    pass