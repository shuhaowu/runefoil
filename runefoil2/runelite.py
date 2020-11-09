import logging
import os.path
import requests
import subprocess
import supervisor.xmlrpc
import shutil
import xmlrpc.client
import time
import pwd
import grp

from . import constants
from .utils import system, chdir

RL_GIT_URL = "https://github.com/runelite/runelite.git"
RL_STATIC_GIT_URL = "https://github.com/runelite/static.runelite.net.git"
BOOTSTRAP_URL = "https://raw.githubusercontent.com/runelite/static.runelite.net/gh-pages/bootstrap.json"


def stop_all_services():
  p = _supervisorctl()
  if p.supervisor.getProcessInfo("static_runelite_net")["statename"] == "RUNNING":
    logging.info("stopping static_runelite_net")
    p.supervisor.stopProcess("static_runelite_net")

  if p.supervisor.getProcessInfo("tomcat")["statename"] == "RUNNING":
    logging.info("stopping tomcat8")
    p.supervisor.stopProcess("tomcat")


def start_all_services():
  logging.info("starting services")
  p = _supervisorctl()
  p.supervisor.startProcess("tomcat")
  p.supervisor.startProcess("static_runelite_net")


def terminate_stray_applications():
  output = subprocess.check_output("ps aux | awk '{ print $1 }' | sed '1 d' | sort | uniq", shell=True)
  output = output.decode("utf-8").strip().split("\n")
  if "btw" in output:
    logging.warn("btw process detected, killing...")
    system("killall -s 9 -u btw")  # make sure nothing lives to ensure they can't access the network


def check_for_update():
  local_version = _get_local_version()
  remote_version = _get_remote_version()
  logging.info("Local version: {} | Remote version: {}".format(local_version, remote_version))
  return local_version, remote_version


def update_and_patch_source_code(version):
  # Runelite source code
  # ====================
  if os.path.exists(constants.RL_SOURCE_PATH):
    with chdir(constants.RL_SOURCE_PATH):
      system("git fetch origin")
  else:
    system("git clone {} {}".format(RL_GIT_URL, constants.RL_SOURCE_PATH))

  with chdir(constants.RL_SOURCE_PATH):
    system("git reset --hard HEAD")
    system("git checkout runelite-parent-{}".format(version))
    patches = os.listdir(constants.PATCH_DIR)
    patches.sort()
    for patch in patches:
      patch = os.path.join(constants.PATCH_DIR, patch)
      system("git apply {}".format(patch))

  # static.runelite.net source code
  # ===============================
  if os.path.exists(constants.RL_STATIC_PATH):
    with chdir(constants.RL_STATIC_PATH):
      system("git fetch origin")
  else:
    system("git clone {} {}".format(RL_STATIC_GIT_URL, constants.RL_STATIC_PATH))

  with chdir(constants.RL_STATIC_PATH):
    system("git reset --hard HEAD")
    system("git checkout origin/gh-pages")


def compile():
  with chdir(constants.RL_SOURCE_PATH):
    system("mvn clean package -DskipTests")


def move_compiled_artifact_to_final_positions(version):
  jar_path = os.path.join(constants.RL_SOURCE_PATH, "runelite-client", "target", "client-{}-shaded.jar".format(version))
  war_path = os.path.join(constants.RL_SOURCE_PATH, "http-service", "target", "runelite-{}.war".format(version))

  logging.info("moving jar to {}".format(constants.RL_JAR_PATH))
  shutil.copyfile(jar_path, constants.RL_JAR_PATH)

  final_war_path = os.path.join(constants.TOMCAT_WEBAPP_DIR, "runelite-{}.war".format(version))
  logging.info("redeploying war to {}".format(final_war_path))
  shutil.rmtree(constants.TOMCAT_WEBAPP_DIR)

  os.mkdir(constants.TOMCAT_WEBAPP_DIR, 0o750)
  os.chown(constants.TOMCAT_WEBAPP_DIR, pwd.getpwnam("tomcat").pw_uid, grp.getgrnam("tomcat").gr_gid)

  shutil.copyfile(war_path, final_war_path)


def record_local_version(version):
  with open(constants.RL_VERSION_PATH, "w") as f:
    f.write(version)


def run_with_post_stop_hook():
  run()
  stop_all_services()


def run():
  logging.info("starting runelite")
  time.sleep(1000000)


def _supervisorctl():
  return xmlrpc.client.ServerProxy(
    "http://127.0.0.1",
    transport=supervisor.xmlrpc.SupervisorTransport(
      None,
      None,
      "unix:///tmp/supervisor.sock"
    )
  )


def _get_local_version():
  if os.path.exists(constants.RL_VERSION_PATH):
    with open(constants.RL_VERSION_PATH) as f:
      local_version = f.read().strip()
  else:
    local_version = "none"

  return local_version


def _get_remote_version():
  data = requests.get(BOOTSTRAP_URL).json()
  return data["client"]["version"]
