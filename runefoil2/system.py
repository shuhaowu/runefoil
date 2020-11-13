import os.path
import re

from . import constants, utils


CURRENT_NVIDIA_VERSION_PATH = "/proc/driver/nvidia/version"
CURRENT_NVIDIA_VERSION_PATH = "/v"


def ensure_gpu_drivers_are_up_to_date():
  if not os.path.exists(CURRENT_NVIDIA_VERSION_PATH):
    return

  if os.path.exists(constants.NVIDIA_VERSION_PATH):
    with open(constants.NVIDIA_VERSION_PATH) as f:
      installed_nvidia_version = f.read().strip()
  else:
    installed_nvidia_version = "none"

  with open(CURRENT_NVIDIA_VERSION_PATH) as f:
    current_nvidia_version = f.read().strip()
    current_nvidia_version = current_nvidia_version.splitlines()[0]
    current_nvidia_version = re.split(r"\s+", current_nvidia_version)[7]

  if installed_nvidia_version != current_nvidia_version:
    utils.system('wget "https://http.download.nvidia.com/XFree86/Linux-x86_64/{}/NVIDIA-Linux-x86_64-{}.run" -O /tmp/NVIDIA-installer.run'.format(current_nvidia_version, current_nvidia_version))
    utils.system('sh /tmp/NVIDIA-installer.run --accept-license --no-questions --no-backup --ui=none --no-kernel-module --no-nouveau-check --no-kernel-module-source --no-nvidia-modprobe --install-libglvnd')
    utils.system('rm -f /tmp/NVIDIA-installer.run')
    with open(constants.NVIDIA_VERSION_PATH, "w") as f:
      f.write(current_nvidia_version)


def ensure_database_is_seeded():
  pass
