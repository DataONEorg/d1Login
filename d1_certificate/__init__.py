'''
grid_shib: helper for downloading client certificate from CILogon

'''

import os
import time
import logging
import webbrowser

import grid_shib
from certinfo import *

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
    os.chmod(fdest, 0700)
    
  fname = "x509up_u%d" % os.getuid()
  fdest = os.path.join(fdest, fname)
  return fdest


def login(openbrowser=None,
          service="https://cilogon.org/?skin=dataone", 
          downloadfile=os.path.expanduser(os.path.join('~', 'Downloads', 'shibCILaunchGSCA.jnlp')),
          overwrite=False,
          waitseconds=60,
          certdest=getDefaultCertificatePath()):
  '''Open a browser at the CILogon site and wait for the .jnlp file to be 
  downloaded. Note that this process is fragile because it relies on the 
  name of the file and its location to be consistent. Could probably rig up
  something with inotify or mdfind to improve this.
  
  @param openbrowser is an optional callback that if set, initiates a process 
    that logs in the user and initiates download of the .jnlp file. If None, 
    then the behavior is to open a web browser window to the service location.
  
  @param service: The URL of the service to contact for logging in
  
  @param downloadfile: The path and name of the file that is to be downloaded.
  
  @param overwrite: True if an existing file of that name should be replaced, 
    applies to the .jnlp file and the target certificate file.
  
  @param waitseconds: The number of seconds that the method will wait for the
    downloaded file to be available in the expected location.
    
  @param certdest: The path and filename of the location where the certificate
    will be placed after downloading. An existing file of that name will be 
    overwritten if overwrite is True.
    
  @return Path to the retrieved certificate
  '''
  if os.path.exists(downloadfile):
    if not overwrite:
      raise Exception("Download file exists and overwrite not specified. %s" % downloadfile)
    os.remove(downloadfile)
  if openbrowser is None:
    ui = webbrowser.open(service,new=1, autoraise=True)
  else:
    openbrowser()
  counter = 0
  increment = 2
  while not os.path.exists(downloadfile):
    time.sleep(increment)
    counter = counter + increment
    logging.info("Timer %d of %d seconds elapsed", counter, waitseconds)
    if counter > waitseconds:
      raise Exception("Timed out waiting for login to complete")
  res = grid_shib.retrieveCertificate(downloadfile, certdest)
  logging.info(res)
  return res
  

if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  login(overwrite=True)
