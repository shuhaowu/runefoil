import sys
import subprocess
import os
import logging

from . import network_sentry
from . import constants as c
from .price_fetcher import PriceFetcher
# TODO: move some of these methods to utils
from .updater import update, system

GPU_DRIVER_PATHS = [
  "/usr/lib/nvidia-384"
]

OPENGL_DISABLED = os.path.exists(c.RL_GL_DISABLE_PATH)


def _start_services():
  system("systemctl start tomcat8")
  system("systemctl start static-runelite-net")


def _stop_services():
  system("systemctl stop tomcat8")
  system("systemctl stop static-runelite-net")


def _kill_btw_processes():
  output = subprocess.check_output("ps aux | awk '{ print $1 }' | sed '1 d' | sort | uniq", shell=True)
  output = output.decode("utf-8").strip().split("\n")
  if "btw" in output:
    logging.warn("btw process detected, killing...")
    system("killall -s 9 -u btw")  # make sure nothing lives to ensure they can't access the network


def setup_run():
  if is_running():
    print("error: runelite is already running in this container, cannot run another due to security restrictions", file=sys.stderr)
    sys.exit(1)

  _stop_services()
  _kill_btw_processes()

  # It's okay to leave this network restriction disabled if error occurs as
  # RL is already shutdown. The next time we successfully launch, we have to
  # enable network restrictions, so it is okay.
  network_sentry.disable_network_restrictions()
  update()
  fetcher = PriceFetcher()
  fetcher.fetch()
  network_sentry.enable_network_restrictions()

  _start_services()


def run():
  if os.geteuid() == 0:
    raise RuntimeError("do not run runelite as root")

  dirname = os.path.dirname(c.RL_JAR_PATH)
  os.chdir(dirname)

  custom_env = {}
  custom_env["RUNELITE_API_BASE"] = "http://localhost:8080/runelite-"
  custom_env["RUNELITE_WS_BASE"] = "wss://localhost:8080/runelite-"
  custom_env["RUNELITE_STATIC_BASE"] = "https://localhost:8081"
  custom_env["PULSE_SERVER"] = network_sentry._get_default_gateway_linux()

  gpu_driver_paths = []
  for path in GPU_DRIVER_PATHS:
    if os.path.exists(path):
      gpu_driver_paths.append(path)

  custom_env["LD_LIBRARY_PATH"] = ":".join(gpu_driver_paths)

  logging.info("Starting runelite via runefoil with environment: {}".format(custom_env))
  os.environ.update(custom_env)

  # https://github.com/runelite/static.runelite.net/blob/a8a19d47521a6e9d00c4eb449405697021d175b8/bootstrap.json#L17-L23
  args = [
    "java",
    "-Xmx512m",
    "-Xss2m",
    "-XX:CompileThreshold=1500",
    "-Xincgc",
    "-XX:+UseConcMarkSweepGC",
    "-XX:+UseParNewGC",
    "-Djna.nosys=true",
    "-Dsun.java2d.noddraw=true",
    "-jar",
    os.path.basename(c.RL_JAR_PATH),
  ]

  # Maybe required in intel GPUs
  # See https://github.com/runelite/runelite/issues/2889
  if not OPENGL_DISABLED:
    args.append("-Dsun.java2d.opengl=true")

  os.execlp("java", *args)


def cleanup_run():
  _stop_services()
  _kill_btw_processes()


def run_static_server():
  import http.server
  import socketserver

  os.chdir(c.RL_STATIC_PATH)
  httpd = socketserver.TCPServer(("", 8081), http.server.SimpleHTTPRequestHandler)
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    return
  finally:
    print("shutting down")
    httpd.server_close()


def is_running():
  return False


def main():
  logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
  if len(sys.argv) < 2:
    print("error: must specify action as either setup-run, run, clean-run, or static", file=sys.stderr)
    sys.exit(1)

  action = sys.argv[1].lower()
  if action == "setup-run":
    setup_run()
  elif action == "run":
    run()
  elif action == "cleanup-run":
    cleanup_run()
  elif action == "static":
    run_static_server()
  else:
    print("error: unknown action {}".format(action), file=sys.stderr)
    sys.exit(1)
