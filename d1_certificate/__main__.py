import sys
import logging
import argparse
from pprint import pprint
from . import *


def dumpSubject(cert):
  info = getSubjectFromCertFile(cert)
  pprint(info, indent=2)


def main():
  services = ",".join(LOGIN_SERVICE.keys())
  parser = argparse.ArgumentParser(description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-l', '--log_level',
                      action='count',
                      default=0,
                      help='Set logging level, multiples for more detailed.')
  parser.add_argument('-C','--cert',
                      default=None,
                      help='Show information for existing certificate')
  parser.add_argument('-s', '--service',
                      default='production',
                      help='Service to login, one of ({})'.format(services))
  parser.add_argument('-j', '--jnlp',
                      default=None,
                      help='Process specified JNLP file')
  parser.add_argument('-t', '--ttl',
                      default=None,
                      help='Certificate lifetime in seconds, use JNLP default if not set')
  args = parser.parse_args()
  # Setup logging verbosity
  levels = [logging.WARNING, logging.INFO, logging.DEBUG]
  level = levels[min(len(levels) - 1, args.log_level)]
  logging.basicConfig(level=level,
                      format="%(asctime)s %(levelname)s %(message)s")

  if args.cert is not None:
    cert_file = args.cert
    if cert_file == "default":
      cert = getDefaultCertificatePath()
    dumpSubject(cert_file)
    sys.exit(0)

  if args.service not in LOGIN_SERVICE.keys():
    logging.error("Uknown service: %s", args.service)
    sys.exit(1)

  cert_file = None
  if args.jnlp is not None:
    cert_file = grid_shib.retrieveCertificate(args.jnlp,
                                              getDefaultCertificatePath(),
                                              lifetime_seconds=args.ttl)
  else:
    cert_file = login(overwrite=True,
                      service=LOGIN_SERVICE[args.service],
                      lifetime_seconds=args.ttl )
  print("Certificate downloaded to: {}\n".format(cert_file))
  print("Certificate info:")
  dumpSubject(cert_file)


if __name__ == "__main__":
  main()