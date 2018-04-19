import requests

from . import constants as c


REPO_URL = "https://repo.runelite.net"
BOOTSTRAP_URL = "https://raw.githubusercontent.com/runelite/static.runelite.net/gh-pages/bootstrap.json"


def http_service_url(version):
  return "{}/net/runelite/http-service/{}/http-service-{}.war".format(REPO_URL, version, version)


def client_url(version):
  return "{}/net/runelite/client/{}/client-{}-shaded.jar".format(REPO_URL, version, version)


def check_current_version():
  data = requests.get(BOOTSTRAP_URL).json()
  return data["client"]["version"]


def download_runelite_client(version):
  pass


def download_runelite_http_service(version):
  pass


def verify_downloaded_jar(path):
  pass
