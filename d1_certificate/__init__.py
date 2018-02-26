'''
grid_shib: helper for downloading client certificate from CILogon

'''

import os
import time
import logging
import webbrowser

from . import grid_shib
from .certinfo import *

LOGIN_SERVICE = {
  'production':'https://cilogon.org/?skin=dataone',
  'stage':'https://cilogon.org/?skin=dataonestage',
  'stage-2':'https://cilogon.org/?skin=dataonestage2',
  'sandbox':'https://cilogon.org/?skin=dataonesandbox',
  'sandbox-2':'https://cilogon.org/?skin=dataonesandbox2',
  'dev':'https://cilogon.org/?skin=dataonedev',
  'dev-2':'https://cilogon.org/?skin=dataonedev2',
}


def getDefaultCertificatePath():
  '''Return the default path for a user certificate, creating the expected
  location if necessary.
  
  Default client certificate path:
  
    ${HOME}/.dataone/certificates
    
  Default client certificate name:
  
    x509up_u + uid
  '''
  fdest = os.path.expanduser(os.path.join("~", ".dataone", "certificates"))
  if not os.path.exists(fdest):
    logging.info("Certificate folder %s does not exist. Creating...", fdest)
    os.makedirs(fdest)
    os.chmod(fdest, 0o700)
    
  fname = "x509up_u%d" % os.getuid()
  fdest = os.path.join(fdest, fname)
  return fdest


def defaultBrowserAction(service):
  '''Open a web browser at the URL service.
  '''
  ui = webbrowser.open(service, new=1, autoraise=True)
  return ui


def login(openbrowser=defaultBrowserAction,
          service=LOGIN_SERVICE['dev'], 
          downloadfile=os.path.expanduser(os.path.join('~', 'Downloads', 'shibCILaunchGSCA.jnlp')),
          overwrite=False,
          waitseconds=60,
          certdest=getDefaultCertificatePath(),
          lifetime_seconds=None):
  '''Open a browser at the CILogon site and wait for the .jnlp file to be 
  downloaded. Note that this process is fragile because it relies on the 
  name of the file and its location to be consistent. Could probably rig up
  something with inotify or mdfind to improve this.
  
  @param openbrowser is an optional callback that if set, initiates a process 
    that logs in the user and initiates download of the .jnlp file. If None, 
    then it is assumed that some other mechanism will cause the .jnlp
    to be present in the expected location.
  
  @param service: The URL of the service to contact for logging in
  
  @param downloadfile: The path and name of the file that is to be downloaded.
  
  @param overwrite: True if an existing file of that name should be replaced, 
    applies to the .jnlp file and the target certificate file.
  
  @param waitseconds: The number of seconds that the method will wait for the
    downloaded file to be available in the expected location.
    
  @param certdest: The path and filename of the location where the certificate
    will be placed after downloading. An existing file of that name will be 
    overwritten if overwrite is True.
    
  @param lifetime_seconds: Certificate lifetime in seconds. If None, then the 
    default value specified in the downloaded .jnlp file will be used (64800)
    
  @return Path to the retrieved certificate
  '''
  if not openbrowser is None:
    openbrowser(service)
  if os.path.exists(certdest) and not overwrite:
    raise IOError("Certificate file exists and overwrite not specified.")
  counter = 0
  increment = 2
  while not os.path.exists(downloadfile):
    time.sleep(increment)
    counter = counter + increment
    logging.info("Timer %d of %d seconds elapsed", counter, waitseconds)
    if counter > waitseconds:
      raise Exception("Timed out waiting for login to complete")
  res = grid_shib.retrieveCertificate(downloadfile, 
                                      certdest, 
                                      lifetime_seconds=lifetime_seconds)
  os.remove(downloadfile)
  logging.info(res)
  return res
  

