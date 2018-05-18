# -*- coding: utf-8 -*-

import logging
import json
import secrets

from azure import functions as func
from os import environ as env
from pandevice import firewall as pan_fw
from pandevice import objects as pan_objs

# Get AUTH_CODE in OS environment
AUTH_CODE = env.get('AUTH_CODE')

# Get FW_IP and API_KEY
FW_IP = env.get('FW_IP')
API_KEY = env.get('API_KEY')

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

def azure_nic(post_req_data):
  """This function takes a JSON payload from the webhook and emits a dictionary of {"ip": []}"""
  try:
    nic = json.loads(post_req_data['properties']['responseBody'])
    return {
      "ipAddress": primary_private_ip(nic['properties']['ipConfigurations']),
      "tags": palo_alto_tags(nic['tags'], namespace='nic|tags')
    }
  except:
    return {"ipAddress": None, "tags": None}

def main(req: func.HttpRequest) -> func.HttpResponse:
  """ Azure Function App Execution Loop """

  logging.info('Python HTTP trigger function processed a request.')
  

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
    nic = json.dumps(azure_nic(req_body))
    return func.HttpResponse(
      body=nic,
      mimetype='application/json',
      status_code=200)
  except:
    pass