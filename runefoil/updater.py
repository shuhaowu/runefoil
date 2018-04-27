import contextlib
import logging
import requests
import hashlib
import subprocess
import shutil
import sys
import tempfile
import os

from . import constants as c

GIT_URL = "https://github.com/runelite/runelite"
LOCAL_API_PATCH_FILE = os.path.join(c.FILES_PATH, "0001-Allow-RuneliteAPI-url-be-configurable.patch")

REPO_URL = "https://repo.runelite.net"
BOOTSTRAP_URL = "https://raw.githubusercontent.com/runelite/static.runelite.net/gh-pages/bootstrap.json"


@contextlib.contextmanager
def chdir(p):
  cwd = os.getcwd()
  try:
    os.chdir(p)
    yield
  finally:
    os.chdir(cwd)


def system(cmd):
  logging.info(cmd)
  subprocess.check_call(cmd, shell=True)


def http_service_url(version):
  return "{}/net/runelite/http-service/{}/http-service-{}.war".format(REPO_URL, version, version)


def client_url(version):
  return "{}/net/runelite/client/{}/client-{}-shaded.jar".format(REPO_URL, version, version)


def check_current_version():
  data = requests.get(BOOTSTRAP_URL).json()
  return data["client"]["version"]


def check_for_update():
  if os.path.exists(c.RL_VERSION_PATH):
    with open(c.RL_VERSION_PATH) as f:
      local_version = f.read().strip()
  else:
    local_version = "none"

  remote_version = check_current_version()
  logging.info("Local version: {} | Remote version: {}".format(local_version, remote_version))
  return local_version, remote_version


def download_runelite_source_if_necessary(version):
  if os.path.exists(c.RL_SOURCE_PATH):
    with chdir(c.RL_SOURCE_PATH):
      system("git fetch origin")
  else:
    system("git clone {} {}".format(GIT_URL, c.RL_SOURCE_PATH))

  with chdir(c.RL_SOURCE_PATH):
    system("git reset --hard HEAD")
    system("git checkout runelite-parent-{}".format(version))
    system("git apply {}".format(LOCAL_API_PATCH_FILE))


def compile_runelite():
  with chdir(c.RL_SOURCE_PATH):
    system("mvn clean install -DskipTests")


def download_runelite_client(version, path):
  url = client_url(version)
  download_and_checksum(url, path)


def download_runelite_http_service(version, path):
  url = http_service_url(version)
  download_and_checksum(url, path)


def download_and_checksum(url, path):
  response = requests.get(url, stream=True)
  response.raise_for_status()

  h = hashlib.sha1()
  with open(path, "wb") as f:
    for block in response.iter_content(1024):
      h.update(block)
      f.write(block)

  response = requests.get(url + ".sha1")
  if not response.ok:
    os.unlink(path)
    response.raise_for_status()

  if h.hexdigest() != response.text:
    raise ValueError("Downloaded hash does not match expected hash: {} {}".format(h.hexdigest(), response.text))


def verify_jar(path):
  jar_verifier_class = os.path.join(os.path.realpath(os.path.dirname(__file__)), "files", "JarVerifier.class")
  if not os.path.exists(jar_verifier_class):
    print("error: JarVerifier.class is not found, did you install it correctly?", file=sys.stderr)
    sys.exit(1)

  with chdir(os.path.dirname(jar_verifier_class)):
    p = subprocess.run(["java", "JarVerifier", path])
    if p.returncode != 0:
      raise RuntimeError("Cannot verify jar")


def main():
  logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
  if len(sys.argv) < 2:
    print("error: must specify action of either source or binary", file=sys.stderr)
    sys.exit(1)

  action = sys.argv[1].lower()
  if action not in {"source", "binary"}:
    print("error: action must be either source or binary", file=sys.stderr)
    sys.exit(1)

  if action == "binary":
    raise NotImplementedError("Cannot use binary until https://github.com/runelite/runelite/pull/2129 is merged")

  update(action)


def update(action):
  logging.info("Checking runelite for updates")

  if not os.path.exists(c.RL_BASEDIR):
    os.makedirs(c.RL_BASEDIR)

  local_version, remote_version = check_for_update()
  if remote_version == local_version:
    logging.info("RL already up to date!")
    return

  if action == "source":
    download_runelite_source_if_necessary(remote_version)
    compile_runelite()
    jar_path = os.path.join(c.RL_SOURCE_PATH, "runelite-client", "target", "client-{}-shaded.jar".format(remote_version))
    war_path = os.path.join(c.RL_SOURCE_PATH, "http-service", "target", "runelite-{}.war".format(remote_version))
    tempdir = None
  else:
    tempdir = tempfile.TemporaryDirectory()
    jar_path = os.path.join(tempdir.name, "client.shaded.jar")
    download_runelite_client(remote_version, jar_path)
    verify_jar(jar_path)

    war_path = os.path.join(tempdir.name, "runelite.war")
    download_runelite_http_service(remote_version, war_path)

  logging.info("moving jar to {}".format(c.RL_JAR_PATH))
  shutil.copyfile(jar_path, c.RL_JAR_PATH)

  final_war_path = os.path.join(c.RL_WAR_BASEPATH, "runelite-{}.war".format(remote_version))
  logging.info("redeploying war to {}".format(final_war_path))
  shutil.rmtree(c.RL_WAR_BASEPATH)
  os.mkdir(c.RL_WAR_BASEPATH, 0o755)
  shutil.copyfile(war_path, final_war_path)

  if tempdir is not None:
    tempdir.cleanup()

  with open(c.RL_VERSION_PATH, "w") as f:
    f.write(remote_version)
