# d1Login
Python helper for authenticating in a DataONE environment.

The d1_certificate library offers some routines to assist with authenticating for interactions with DataONE services. Authentication requires a web browser UI, and so is not suitable for use on headles systems. The basic process is:

1. A web browser is opened to select an identity provider
2. Credentials are entered into the selected IDP
3. A certificate signing request is created and token information is retieved from CILogon
4. The certificate is signed and moved to a consistent location.

Caveats:
1. A web browser is required
2. It is assumed that the file downloaded by the web browser is located in ${HOME}/Downloads
3. The generated certificate is placed into ${HOME}/.dataone/certificates

## Example


