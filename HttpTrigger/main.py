# -*- coding: utf-8 -*-

import json
import logging
from logging.config import dictConfig
import secrets
import sys

from azure import functions as func
from os import environ as env
from pandevice import firewall as pan_fw
from pandevice import objects as pan_objs
from parse import *

APP_CONFIG = {
  'log_level': env.get('LOG_LEVEL', default='INFO'),
  'authorization_code': env.get('AUTH_CODE'),
  'fw_ip': env.get('FW_IP'),
  'api_key': env.get('API_KEY')
}

LOG_CONFIG = {
  "version": 1,
  "disable_existing_loggers": False,
  "formatters": {
    "default": {
      "format": "%(asctime)s [%(levelname)s] %(name)s %(message)s"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "formatter": "default",
      "level": APP_CONFIG['log_level']
    }
  },
  "loggers": {
    "": {
      "handlers": ["console"],
      "level": APP_CONFIG['log_level']
    }
  }
}

dictConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)

def temp_auth_code():
  return secrets.token_urlsafe(32)

def primary_private_ip(ip_configs):
  """ This function extracts primary, private ipaddress """
  return [ip['properties']['privateIPAddress']
    for ip in ip_configs if ip['properties']['primary']][0]

def palo_alto_tags(azure_dict, namespace='', delim='_'):
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
      "tags": palo_alto_tags(nic['tags'], namespace='nic_tags')
    }
  except:
    return {"ipAddress": None, "tags": None}

def pan_firewall(hostname='', api_key=''):
  try:
    fw = pan_fw.Firewall(hostname=hostname, api_key=api_key)
    version, platform, serial = parse(
      "SystemInfo(version='{}', platform='{}', serial='{}')",
      str(fw.refresh_system_info())).fixed
    logger.debug('FW version={}:FW platform={}: FW serial={}'.format(version, platform, serial))
    return fw
  except Exception as e:
    logger.error('Cannot connect to PAN:{}'.format(str(e)))
    return None

def pan_tags(pan_fw, tag_names=[]):
  """ Returns a list of PAN tag objects. It will take a list of tag names and add them to exising tags """
  current_tags = pan_objs.Tag.refreshall(pan_fw, add=False)
  current_tag_names= [t.name for t in current_tags]
  new_tags = list(
    set(tag_names).difference(set(current_tag_names)))
  logger.debug('Supplied tags:{}'.format(tag_names))
  new_pan_tags = [pan_objs.Tag(name=t) for t in new_tags]
  # Add current and new tag objects to pan_fw object
  if new_pan_tags:
    logger.debug('Found {:d}'.format(len(new_tags)))
    logger.debug('Adding tags:{}'.format(new_tags))
    tags_to_be_added = current_tags + new_pan_tags
    for pan_tag in tags_to_be_added:
      pan_fw.add(pan_tag)
    #tags_to_be_added[0].create_similar()
    #tags_to_be_added[0].apply_similar()
    return tags_to_be_added
  else:
    logger.debug('All supplied tags already exist; no new tags added')
    return current_tags

def pan_ips(pan_fw, azure_nic={"ipAddress": "", "tags": []}):
  """ Returns a list of PAN Address objects """
  logger.debug('IP address value: {}'.format(azure_nic['ipAddress']))
  current_ips = pan_objs.AddressObject.refreshall(pan_fw, add=False)
  for ip in current_ips: pan_fw.add(ip) # Re-add existing
  if azure_nic['ipAddress']:
    az_ip = pan_objs.AddressObject(
      name='ip_' + azure_nic['ipAddress'],
      value=azure_nic['ipAddress'],
      tag=azure_nic['tags'])
      # Adds or updates ip object in pan_fw
    logger.debug('Adding az_ip')
    pan_fw.add(az_ip)
    az_ip.create()
    az_ip.apply()
  if not [ip for ip in current_ips if ip.value == azure_nic['ipAddress']]:
    return current_ips + [az_ip]
  return current_ips

def azure_securityzone(azure_nic={"ipAddress": "", "tags": []}):
  """ Returns security zone from azure nic ipaddress """
  prefix = 'azure_SecurityZone'
  security_zone = [t for t in azure_nic['tags'] if '_SecurityZone_' in t]
  if security_zone:
    if '_High' in security_zone[0]:
      return f'{prefix}_High'
    elif '_Medium' in security_zone[0]:
      return f'{prefix}_Medium'
    elif '_Low' in security_zone[0]:
      return f'{prefix}_Low'
  return f'{prefix}_None'

def pan_addressgroup_memberships(pan_fw, ip_name=None):
  """ Returns a list current addressgroup memberships """
  if ip_name == None:
    return []
  current_addressgroups = pan_objs.AddressGroup.refreshall(pan_fw, add=False)
  return [ao.name for ao in current_addressgroups if ip_name in ao.static_value]

def pan_securityzone(pan_fw, ip_name=None, label='_SecurityZone_'):
  """ Returns security zone of a PAN AddressObject with ip_name """
  try:
    if ip_name:
      return [securityzone for securityzone in pan_addressgroup_memberships(pan_fw, ip_name=ip_name)
        if label in securityzone][0]
    else:
      return ''
  except Exception as e:
    return ''

def pan_addressgroup_members(pan_fw, name=''):
  """ Returns a list of addressgroup members """
  try:
    if name:
      return [ao.static_value for ao in pan_objs.AddressGroup.refreshall(pan_fw, add=False)
        if ao.name == name][0]
  except Exception as e:
    return []

def pan_addressgroup(pan_fw, address_group_name='', ip_address=None):
  """ Returns a PAN static IP address group object """
  current_ips = pan_objs.AddressObject.refreshall(pan_fw, add=False)
  ip_address_names = [ip.name for ip in current_ips if ip.value == ip_address]
  if not ip_address_names:
    logging.warn('IP Address {} does not exist'.format(ip_address))
    return None
  ip_name = ip_address_names[0]
  current_addressgroups = pan_objs.AddressGroup.refreshall(pan_fw, add=False)  
  current_addressgroup = [ao for ao in current_addressgroups if ao.name == address_group_name]
  if not current_addressgroup:
    logging.warn('PAN AddressGroup {} does not exist'.format(address_group_name))
    return None
  logger.debug('Found PAN AddressGroup {}'.format(address_group_name))
  current_addressgroup_static_values = set(current_addressgroup[0].static_value)
  addressgroup = pan_objs.AddressGroup(
    name=address_group_name,
    static_value=current_addressgroup_static_values.union(set([ip_name])))
  pan_fw.add(addressgroup)
  return addressgroup

def main(req: func.HttpRequest) -> func.HttpResponse:
  """ Azure Function App Execution Loop """
  logger.info('Python HTTP trigger function processed a request.')
  if APP_CONFIG['authorization_code'] is None:
    auth_code = temp_auth_code()
    logger.info('AUTH_CODE environment variable not found.')
    logger.info(f'Setting AUTH_CODE = {auth_code}')
    environ['AUTH_CODE'] = auth_code
    return func.HttpResponse(
      body=f'A new authorization code generated. Please record this value; it will be available only at this time: {auth_code}',
      status_code=200)
  logger.info('AUTH_CODE environment variable found.')
  code = req.params.get('code')
  logger.info('Checking for valid auth code supplied in query string.')
  # TODO: check for code in req.header.
  if not code:
    return func.HttpResponse(
      body='A valid authorization code must be supplied in the query string',
      status_code=401)
  elif code != APP_CONFIG['authorization_code']:
    return func.HttpResponse(
      body='Authorization code is invalid',
      status_code=401)
  logger.info('Code supplied on query string matches AUTH_CODE.')
  fw = pan_firewall(hostname=APP_CONFIG['fw_ip'], api_key=APP_CONFIG['api_key'])
  try:
    req_body = req.get_json()
    nic = azure_nic(req_body)
    tags = pan_tags(pan_fw=fw, tag_names=nic['tags'])
    if tags:
      logger.info('Updating PAN Tags')
      tags[0].create_similar()
      tags[0].apply_similar()
      logger.info('Updated PAN Tags')
    ips = pan_ips(pan_fw=fw, azure_nic=nic)
    if ips:
      logger.info('Updating PAN AddressObjects')
      for ip in ips: logger.debug(ip.name)
      logger.info('Updated PAN AddressObjects')
    az_ip_securityzone = azure_securityzone(azure_nic=nic)
    logger.info('Security Zone for Azure {}={}'.format(nic['ipAddress'], az_ip_securityzone))
    pan_ip_securityzone = pan_securityzone(pan_fw=fw, ip_name='ip_' + nic['ipAddress'])
    logger.info('Security Zone for PAN {}={}'.format('ip_' + nic['ipAddress'], pan_ip_securityzone))
    if pan_ip_securityzone:
      if pan_ip_securityzone != az_ip_securityzone:
        logger.debug('Removing {} from {}'.format('ip_' + nic['ipAddress'], pan_ip_securityzone))
        static_value_members = pan_addressgroup_members(pan_fw=fw, name=pan_ip_securityzone)
        logger.debug('Current static_value: {}'.format(static_value_members))
        s = set(static_value_members)
        s.discard('ip_' + nic['ipAddress'])
        new_static_value_members = list(s)
        logger.debug('New static_value: {}'.format(new_static_value_members))
        former_addressgrp = pan_objs.AddressGroup(
          name=pan_ip_securityzone,
          static_value=new_static_value_members)
        new_addressgrp = pan_addressgroup(
          pan_fw=fw, 
          address_group_name=az_ip_securityzone,
          ip_address=nic['ipAddress'])
        fw.add(former_addressgrp)
        fw.add(new_addressgrp)
        addressgrps = [former_addressgrp] + [new_addressgrp]
        logger.info('AddressGroups modified')
      else:
        logger.info('AddressGroups unmodified')
        addressgrps = []
    else:
      new_addressgrp = pan_addressgroup(
        pan_fw=fw, 
        address_group_name=az_ip_securityzone,
        ip_address=nic['ipAddress'])
      fw.add(new_addressgrp)
      addressgrps = [new_addressgrp]
    if addressgrps:
      logger.info('Updating PAN AddressGroups: {}'.format(addressgrps))
      for ag in addressgrps:
        ag.create()
        ag.apply()
        logger.info('Updated PAN AddressGroup: {}'.format(ag.name))
    return func.HttpResponse(
      body=json.dumps(nic),
      mimetype='application/json',
      status_code=200)
  except:
    pass