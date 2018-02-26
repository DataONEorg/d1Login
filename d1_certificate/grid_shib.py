'''
Implements GridShib methods for retrieving a Client Certificate from CILogon.

This implementation borrows heavily from:

  https://cilogon.org/gridshib-ca/gridshibca-client.py

    ######################################################################
    #
    # This file is part of the GriShib-CA distribution.  Copyright
    # 2006-2010 The Board of Trustees of the University of
    # Illinois. Please see LICENSE at the root of the distribution.
    #
    ######################################################################
    GridShib-CA Credential Retriever Client
    
    Python client for GridShib-CA.
    
    Requires pyOpenSSL from https://launchpad.net/pyopenssl
    
    Credit to Tom Uram <turam at mcs.anl.gov> for Python MyProxy client.

The implementation was adjusted by DV:

- Simplify to work with DataONE assumptions
- Code formatting
- Added logging rather than stdout
- Switch to requests instead of urllib, urllib2 


'''
import sys
import os
import os.path
import getpass
import requests
from OpenSSL import crypto

import time
import logging
import xml.etree.ElementTree as ET
import webbrowser

######################################################################
# From: https://cilogon.org/gridshib-ca/gridshibca-client.py
#
class X509Credential:

  def __init__(self):
    self.privateKey = None
    self.certificate = None

  def generateRequest(self,
                      keyType = crypto.TYPE_RSA,
                      bits = 2048,
                      messageDigest = "sha1"):
    """Generate a request and return the PEM-encoded PKCS10 object."""
    logging.info("Generating private keys and certificate request.")
    self.request = crypto.X509Req()
    self.privateKey = crypto.PKey()
    self.privateKey.generate_key(keyType, bits)
    self.request.set_pubkey(self.privateKey)
    self.request.sign(self.privateKey, messageDigest)
    return crypto.dump_certificate_request(crypto.FILETYPE_PEM,
                                           self.request)
  
  
  def setCertificate(self, certificate):
    """Use given OpenSSL.crypto.X509 as certificate."""
    self.certificate = certificate


  def writeGlobusCredential(self, fpath):
    if self.privateKey is None:
      raise GridShibCAException("Attempt to write incomplete credential (private key is missing)")
    if self.certificate is None:
      raise GridShibCAException("Attempt to write incomplete credential (public key is missing)")
    certificatePEM = crypto.dump_certificate(crypto.FILETYPE_PEM,
                                             self.certificate)
    privateKeyPEM = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                           self.privateKey)
    if os.path.exists(fpath):
      os.remove(fpath)
    # O_EXCL|O_CREAT to prevent a race condition where someone
    # else opens the file first.
    fd = os.open(fpath, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    file = os.fdopen(fd, "wb")
    file.write(certificatePEM)
    file.write(privateKeyPEM)
    file.close()


######################################################################
# From: https://cilogon.org/gridshib-ca/gridshibca-client.py
#
class GridShibCAException(Exception):
  """Exception for GridShibCA-specific errors."""
  pass


######################################################################
# From: https://cilogon.org/gridshib-ca/gridshibca-client.py
#
# Modified to use requests instead of urllib2
class GridShibCAURL:

  VERSION="2.0.1"

  def __init__(self, url):
    global version
    assert url.lower().startswith("https://")
    self.url = url
    self.userAgent = "GridShibCA-Python/%s" % GridShibCAURL.VERSION


  def post(self, values):
    logging.debug("Postdata: %s", values)
    headers = { 'User-Agent' : self.userAgent }
    req = requests.post(self.url, data=values, headers=headers)
    req.raise_for_status()
    return req.content


######################################################################
# From: https://cilogon.org/gridshib-ca/gridshibca-client.py
# 
# Simplified, requires certificate to be retrieved within the lifetime.
class GridShibCACredentialIssuerURL(GridShibCAURL):

  def requestCertificate(self, actCode, lifetime):
    """Request certificate from GridShib-CA. Returns X509Credential object."""
    credential = X509Credential()
    requestPEM = credential.generateRequest()
    logging.debug("Request generated:\n%s", requestPEM)
    postFields = {
        "command" : "IssueCert",
        "lifetime" : lifetime,
        "GRIDSHIBCA_SESSION_ID" : actCode,
        "certificateRequest" : requestPEM,
        }
    logging.debug("Posting request")
    try:
      certificatePEM = self.post(postFields)
    except requests.exceptions.HTTPError as err:
      raise err
    logging.debug("Got response:\n%s", certificatePEM)
    try:
      certificateX509 = crypto.load_certificate(
          crypto.FILETYPE_PEM, certificatePEM)
    except:
      raise GridShibCAException("Error processing certificate from server")
    credential.setCertificate(certificateX509)
    return credential


######################################################################
# Following added by DV
#

def getPropertiesFromJNLP(fname):
  ''' The CILogon process returns a .jnlp file, which is really just badly 
  formatted xml. Clean it up and read the arguments to pass on to 
  the download tool. 
  
  fname = name of .jnlp file to parse
  '''
  res = {}
  xml = open(fname,'r', encoding='utf-8').read()
  jnlp = ET.fromstring(xml.strip())
  properties = jnlp.findall(".//argument")
  for property in properties:
    v = property.text
    parts = v.split("=")
    res[parts[0].strip()] = parts[1].strip()
  logging.debug(res)
  return res
  

def retrieveCertificate(fjnlp, fdest, lifetime_seconds=None):
  '''Download a client certificate from CILogon given the downloaded .jnlp file.
  
  fjnlp = full path to .jnlp file
  fdest = the name of hte file that the resulting private and public key 
          combination will be written to. Note that this should be secured since 
          the key provides access to potentially restricted resources.
  lifetime_seconds = requested lifetime in seconds of the certificate. The 
          default provided in the JNLP can be overridden to set whatever 
          duration is desired. 
  '''
  props = getPropertiesFromJNLP(fjnlp)
  credIssuer = GridShibCACredentialIssuerURL(props['WebAppURL'])
  if lifetime_seconds is None:
    lifetime_seconds = props['lifetime']
  credential = credIssuer.requestCertificate(props['AuthenticationToken'], lifetime_seconds)
  credential.writeGlobusCredential(fdest)
  return fdest
  
