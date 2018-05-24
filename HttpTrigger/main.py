# -*- coding: utf-8 -*-

import json
import logging
import secrets
import sys

from azure import functions as func
from os import environ as env
from pandevice import firewall as pan_fw
from pandevice import objects as pan_objs
from parse import *

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
  if namespace:
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

def pan_firewall(hostname='', api_key=''):
  try:
    fw = pan_fw.Firewall(hostname=hostname, api_key=api_key)
    version, platform, serial = parse(
      "SystemInfo(version='{}', platform='{}', serial='{}')",
      str(fw.refresh_system_info())).fixed
    logging.info('FW version={}:FW platform={}: FW serial={}'.format(version, platform, serial))
    return fw
  except Exception as e:
    logging.error('Cannot connect to PAN:{}'.format(str(e)))
    return None

def pan_tag_objs(pan_fw, tag_names=[]):
  """ Returns a list of PAN tag objects. It will take a list of tag names and add them to exising tags """
  current_tag_objects = pan_objs.Tag.refreshall(pan_fw, add=False)
  current_tag_names= [t.name for t in current_tag_objects]
  new_tags = list(
    set(tag_names).difference(set(current_tag_names)))
  logging.info('Supplied tags:{}'.format(tag_names))
  new_pan_tag_objects = [pan_objs.Tag(name=t) for t in new_tags]
  # Add current and new tag objects to pan_fw object
  if new_pan_tag_objects:
    logging.info('Found {:d}'.format(len(new_tags)))
    logging.info('Adding tags:{}'.format(new_tags))
    objs_to_be_added = current_tag_objects + new_pan_tag_objects
    for pan_tag_obj in objs_to_be_added:
      pan_fw.add(pan_tag_obj)
    objs_to_be_added[0].create_similar()
    objs_to_be_added[0].apply_similar()
  else:
    logging.info('All supplied tags already exist; no new tags added')
  current_tag_objects = pan_objs.Tag.refreshall(pan_fw, add=False)
  logging.info('Current tags:{}'.format([t.name for t in current_tag_objects]))
  return current_tag_objects

def pan_ip_obj(pan_fw, azure_nic={"ipAddress": "", "tags": []}):
  """ Returns a PAN ip object """
  current_ip_objects = pan_objs.AddressObject.refreshall(pan_fw, add=False)
  new_ip_obj = pan_objs.AddressObject(
    name='ip_' + azure_nic['ipAddress'],
    value=azure_nic['ipAddress'],
    tag=azure_nic['tags'])
  ip_objs_to_be_added = current_ip_objects + [new_ip_obj]
  for ip_obj in ip_objs_to_be_added:
    pan_fw.add(ip_obj)
  new_ip_obj.create()
  new_ip_obj.apply()
  return new_ip_obj

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

  fw = pan_firewall(hostname=FW_IP, api_key=API_KEY)
  
  try:
    req_body = req.get_json()
    nic = azure_nic(req_body)
    pan_tag_objs(pan_fw=fw, tag_names=nic['tags'])
    pan_ip_obj(pan_fw=fw, azure_nic=nic)
    return func.HttpResponse(
      body=json.dumps(nic),
      mimetype='application/json',
      status_code=200)
  except:
    pass