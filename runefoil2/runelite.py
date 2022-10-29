import logging
import os.path
import requests
import subprocess
import supervisor.xmlrpc
import shutil
import xmlrpc.client
import pwd
import grp

from . import constants
from .utils import system, chdir

RL_GIT_URL = "https://github.com/runelite/runelite.git"
RL_STATIC_GIT_URL = "https://github.com/runelite/static.runelite.net.git"
RL_API_GIT_URL = "https://github.com/runelite/api.runelite.net.git"
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
    patchdir = os.path.join(constants.PATCHES_PATH, "runelite")
    patches = os.listdir(patchdir)
    patches.sort()
    for patch in patches:
      patch = os.path.join(patchdir, patch)
      system("git apply {}".format(patch))

  # api.runelite.net source code
  # ====================
  if os.path.exists(constants.RL_API_PATH):
    with chdir(constants.RL_API_PATH):
      system("git fetch origin")
  else:
    system("git clone {} {}".format(RL_API_GIT_URL, constants.RL_API_PATH))

  with chdir(constants.RL_API_PATH):
    system("git reset --hard HEAD")
    system("git checkout origin/master".format(version))
    patchdir = os.path.join(constants.PATCHES_PATH, "api.runelite.net")
    patches = os.listdir(patchdir)
    patches.sort()
    for patch in patches:
      patch = os.path.join(patchdir, patch)
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
    system("mvn clean package -DskipTests -Dcheckstyle.skip")
  with chdir(constants.RL_API_PATH):
    system("mvn clean package -DskipTests -Dcheckstyle.skip")

def move_compiled_artifact_to_final_positions(version):
  jar_path = os.path.join(constants.RL_SOURCE_PATH, "runelite-client", "target", "client-{}-shaded.jar".format(version))
  war_path = os.path.join(constants.RL_API_PATH, "http-service", "target", "runelite-1.1.7.war")

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
  dirname = os.path.dirname(constants.RL_JAR_PATH)
  os.chdir(dirname)

  custom_env = {}
  custom_env["PULSE_SERVER"] = "unix:/tmp/pulse/native"
  custom_env["PULSE_COOKIE"] = "/tmp/pulse.cookie"

  if os.path.exists(constants.GDK_SCALE_PATH):
    with open(constants.GDK_SCALE_PATH) as f:
      custom_env["GDK_SCALE"] = f.read().strip()
      logging.info("setting GDK_SCALE = {}".format(custom_env["GDK_SCALE"]))

  logging.info("Runefoil Custom ENV: {}".format(custom_env))
  os.environ.update(custom_env)

  # https://github.com/runelite/static.runelite.net/blob/1.6.30/bootstrap.json#L252-L258
  args = [
    "sudo",
    "-Eu",
    "btw",
    "java",
    "-Xmx512m",
    "-Xss2m",
    "-XX:CompileThreshold=1500",
    "-XX:+DisableAttachMechanism",
    "-Djna.nosys=true",
    "-Duser.home=/data/jagexcache",  # This will put jagexcache somewhere else, allowing it to be saved between container recreations
    # Linux? https://github.com/runelite/launcher/blob/27c82f85743b759c8fc46cd752a7c11d2f24a28e/src/main/java/net/runelite/launcher/Launcher.java#L125-L128
    # https://github.com/runelite/launcher/blob/9e2064aad88c16dae5370cbf36dd752e8e45d3df/src/main/java/net/runelite/launcher/HardwareAccelerationMode.java#L57-L60
    "-Dsun.java2d.noddraw=true",
    "-Drunelite.session.url=http://localhost:8080/session",
    "-Drunelite.http-service.url=http://localhost:8080/runelite-{}".format(_get_local_version()),
    "-Drunelite.static.url=http://localhost:8081",
    "-Drunelite.ws.url=http://localhost:8080/ws",
  ]

  # Maybe required in intel GPUs
  # See https://github.com/runelite/runelite/issues/2889
  if not os.path.exists(constants.OPENGL_DISABLED_PATH):
    args.append("-Dsun.java2d.opengl=true")

  args.append("-jar")
  args.append(constants.RL_JAR_PATH)

  logging.info("Runelite args: {}".format(args))
  subprocess.run(args)
  logging.info("Runelite stopped")


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
