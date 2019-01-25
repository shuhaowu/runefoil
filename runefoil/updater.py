import contextlib
import grp
import logging
import os
import pwd
import requests
import shutil
import subprocess

from . import constants as c

RL_GIT_URL = "https://github.com/runelite/runelite"
RL_STATIC_GIT_URL = "https://github.com/runelite/static.runelite.net.git"
LOCAL_API_PATCH_FILE = os.path.join(c.FILES_PATH, "0001-Runefoil-base-patch-set.patch")

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


def get_local_version():
  if os.path.exists(c.RL_VERSION_PATH):
    with open(c.RL_VERSION_PATH) as f:
      local_version = f.read().strip()
  else:
    local_version = "none"

  return local_version


def get_remote_version():
  data = requests.get(BOOTSTRAP_URL).json()
  return data["client"]["version"]


def check_for_update():
  local_version = get_local_version()
  remote_version = get_remote_version()
  logging.info("Local version: {} | Remote version: {}".format(local_version, remote_version))
  return local_version, remote_version


def download_runelite_source_if_necessary(version):
  if os.path.exists(c.RL_SOURCE_PATH):
    with chdir(c.RL_SOURCE_PATH):
      system("git fetch origin")
  else:
    system("git clone {} {}".format(RL_GIT_URL, c.RL_SOURCE_PATH))

  with chdir(c.RL_SOURCE_PATH):
    system("git reset --hard HEAD")
    system("git checkout runelite-parent-{}".format(version))
    system("git apply {}".format(LOCAL_API_PATCH_FILE))


def compile_runelite():
  with chdir(c.RL_SOURCE_PATH):
    system("mvn clean install -DskipTests")


def update_static_runelite_net_source():
  if os.path.exists(c.RL_STATIC_PATH):
    with chdir(c.RL_STATIC_PATH):
      system("git fetch origin")
  else:
    system("git clone {} {}".format(RL_STATIC_GIT_URL, c.RL_STATIC_PATH))

  with chdir(c.RL_STATIC_PATH):
    system("git reset --hard HEAD")
    system("git checkout origin/gh-pages")


def main():
  logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
  update()


def update():
  logging.info("Checking runelite for updates")

  if not os.path.exists(c.RL_BASEDIR):
    os.makedirs(c.RL_BASEDIR)

  local_version, remote_version = check_for_update()
  if remote_version == local_version:
    logging.info("RL already up to date!")
    return

  update_static_runelite_net_source()

  download_runelite_source_if_necessary(remote_version)
  compile_runelite()
  jar_path = os.path.join(c.RL_SOURCE_PATH, "runelite-client", "target", "client-{}-shaded.jar".format(remote_version))
  war_path = os.path.join(c.RL_SOURCE_PATH, "http-service", "target", "runelite-{}.war".format(remote_version))

  logging.info("moving jar to {}".format(c.RL_JAR_PATH))
  shutil.copyfile(jar_path, c.RL_JAR_PATH)

  final_war_path = os.path.join(c.RL_WAR_BASEPATH, "runelite-{}.war".format(remote_version))
  logging.info("redeploying war to {}".format(final_war_path))
  shutil.rmtree(c.RL_WAR_BASEPATH)

  os.mkdir(c.RL_WAR_BASEPATH, 0o755)
  os.chown(c.RL_WAR_BASEPATH, pwd.getpwnam("tomcat8").pw_uid, grp.getgrnam("tomcat8").gr_gid)

  shutil.copyfile(war_path, final_war_path)

  with open(c.RL_VERSION_PATH, "w") as f:
    f.write(remote_version)
