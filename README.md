# d1Login
Python helper for authenticating in a DataONE environment.

The d1_certificate library offers some routines to assist with authenticating for interactions with DataONE services. Authentication requires a web browser UI, and so is not suitable for use on headless systems. The basic process is:

1. A web browser is opened to select an identity provider
2. Credentials are entered into the selected IDP
3. A certificate signing request is created and token information is retieved from CILogon
4. The certificate is signed and moved to a consistent location.

Caveats:

1. A web browser is required
2. It is assumed that the file downloaded by the web browser is located in ${HOME}/Downloads
3. The generated certificate is placed into ${HOME}/.dataone/certificates
4. The subject mapping and group info in the certificate is static. Be aware that the certificate will need to be regenerated if your user id mapping or group membership needs to change.

## Example

```python
>>> import d1_certificate
>>> service = d1_certificate.LOGIN_SERVICE['dev']
>>> certpath = d1_certificate.login(overwrite=True, service=service)
# Browser window opens for authentication

>>> print certpath
/Users/vieglais/.dataone/certificates/x509up_u501

>>> d1_certificate.getSubjectFromCertFile( certpath )
{'not_after': '20151216225323Z',
 'not_before': '20151216044823Z',
 'status': True,
 'subject': 'CN=Dave Vieglais A34511,O=Google,C=US,DC=cilogon,DC=org',
 'subject_info': None}

```

On OS X, the certificate can then be imported into the keychain for browser interactions with nodes in the authenticated environment. For example:

```bash
CERT=/Users/vieglais/.dataone/certificates/x509up_u501
openssl x509 -outform der -in ${CERT} -out "${CERT}.der"
security add-certificates "${CERT}.der"
```

Now open a browser (chrome or safari, firefox uses it's own cert management independent of keychain)
and visit the URL: 

    https://cn-dev.test.dataone.org/cn/v2/diag/subject

You should see your credentials in the xml response.

## Installation

Put the d1_certificate folder on your PYTHONPATH.

