'''Extract information from a DataONE Client Certificate
'''

import sys
import os
import logging
import argparse
from OpenSSL import crypto
from pyasn1.error import PyAsn1Error
from pyasn1.codec.ber import decoder
from lxml import etree


NAMESPACES = {
  "d1" : "http://ns.dataone.org/service/types/v1",
  "d1_1": "http://ns.dataone.org/service/types/v1.1",
  "d1_2": "http://ns.dataone.org/service/types/v2.0",
  }


def getSubjectFromName(xName):
  '''Given a DN, returns a DataONE subject
  TODO: This assumes that RDNs are in reverse order...
  
  @param 
  '''
  parts = xName.get_components()
  res = []
  for part in parts:
    res.append(str("%s=%s" % (str(part[0], encoding='utf-8').upper(), str(part[1], encoding='utf-8'))))
  res.reverse()
  return ",".join(res)


def dumpExtensions(x509):
  decoder.decode.defaultErrorState = decoder.stDumpRawValue
  nExt = x509.get_extension_count()
  logging.debug("There are %d extensions in this certificate" % nExt)
  for i in range(0, nExt):
    ext = x509.get_extension(i)
    logging.debug("Extension %d:" % i)
    logging.debug("  Name: %s" % ext.get_short_name())
    try:
      v = decoder.decode(ext.get_data())
      logging.debug("  Value: %s" % str(v))
    except PyAsn1Error as err:
      logging.warning(err)
      logging.debug("  Value: %s" % str(ext.get_data()))
  

def getMatchingSubjectInfoFromCert(x509):
  '''Retrieve a list of strings from the x509 extensions that contain 
  the string "subjectInfo".
  '''
  # This is a huge hack, though it works nicely - iterate through the extensions 
  # looking for a UTF8 object that contains the string "subjectInfo". The 
  # extension has no name, and the OpenSSL lib currently has no way to retrieve 
  # the extension by OID which is 1.3.6.1.4.1.34998.2.1 for the DataONE 
  # subjectInfo extension.
  #
  # A caller should check that the returned data is a valid subjectInfo 
  # structure
  decoder.decode.defaultErrorState = decoder.stDumpRawValue
  nExt = x509.get_extension_count()
  res = []
  for i in range(0, nExt):
    ext = x509.get_extension(i)
    sv = decoder.decode(ext.get_data())
    if str(sv).find("subjectInfo") >= 0:
      res.append( sv[0] )
  return res


def getSubjectInfoFromCert(x509):
  matches = getMatchingSubjectInfoFromCert(x509)
  for match in matches:
    try:
      #Verify the thing is valid XML
      logging.debug("Loading xml structure")
      doc = etree.fromstring( bytes(match) )
      #Is this a subject info structure?
      logging.debug("Looking for subjectInfo element...")
      for ns in NAMESPACES:
        test = "{%s}subjectInfo" % NAMESPACES[ns]
        if doc.tag == test:
          logging.debug("Match on %s" % test)
          return match.prettyPrint()
    except Exception as e:
      logging.exception( e )
      pass
  return None


def getSubjectFromCertFile(certFileName):
  status = True
  certf = open(certFileName, "rb")
  x509 = crypto.load_certificate(crypto.FILETYPE_PEM, certf.read())
  certf.close()
  #dumpExtensions(x509)
  if x509.has_expired():
    logging.warning("Certificate has expired!")
    status = False
  else:
    logging.info("Certificate OK")
    status = True
  logging.info("Issuer: %s" % getSubjectFromName(x509.get_issuer()))
  logging.info("Not before: %s" % str(x509.get_notBefore(), encoding='utf-8'))
  logging.info("Not after: %s"  % str(x509.get_notAfter(), encoding='utf-8'))
  return {'subject': getSubjectFromName(x509.get_subject()),
          'subject_info': getSubjectInfoFromCert(x509),
          'not_before': str(x509.get_notBefore(), encoding='utf-8'),
          'not_after': str(x509.get_notAfter(), encoding='utf-8'),
          'status': status, 
          }
