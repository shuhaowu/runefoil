import logging
import os
import requests
import shutil
import socket
import subprocess
import time

from . import constants

WORLD_URL = "http://www.runescape.com/g=oldscape/slr.ws?order=LPWM"

UNRESTRICTED_HOSTS = """
127.0.0.1   localhost
127.0.1.1   {hostname}
""".lstrip()

RESTRICTED_HOSTS = """
127.0.0.1   localhost
127.0.1.1   {hostname}

{allowed_hosts}
""".lstrip()

RESTRICTED_NFTABLES = """
#!/usr/sbin/nft -f

flush ruleset

table inet filter {{
  chain input {{
    type filter hook input priority 0; policy drop;

    # accept any localhost traffic
    iif lo accept

    # accept traffic originated from us
    ct state established,related accept

    counter drop
  }}

  chain output {{
    type filter hook output priority 0; policy drop;

    oif lo accept

    # TODO: this is probably not needed/not safe, as existing connections will thus be allowed.
    # ct state established,related accept
    ip daddr 10.222.182.3 accept
    ip daddr 10.222.182.4 accept
{ipdaddr_rules}

    log prefix "rf-drop: " group 0 drop
  }}
}}
""".lstrip()

UNRESTRICTED_NFTABLES = """
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
  chain input {
    type filter hook input priority 0; policy accept;

    # accept any localhost traffic
    iif lo accept

    # accept traffic originated from us
    ct state established,related accept

    counter drop
  }

  chain output {
    type filter hook output priority 0; policy accept;
  }
}
""".lstrip()

RESTRICTED_NSSWITCH_PATH = os.path.join(constants.FILES_PATH, "nsswitch.conf.restricted")
UNRESTRICTED_NSSWITCH_PATH = os.path.join(constants.FILES_PATH, "nsswitch.conf.unrestricted")


def enable_internet():
  logging.info("writing unrestricted hosts into /etc/hosts")
  with open("/etc/hosts", "w") as f:
    f.write(UNRESTRICTED_HOSTS.format(hostname=socket.gethostname()))

  # logging.info("enabling dns access via nsswitch")
  # shutil.copyfile(UNRESTRICTED_NSSWITCH_PATH, "/etc/nsswitch.conf")

  logging.info("writing new nftable rules")
  with open("/etc/nftables.conf", "w") as f:
    f.write(UNRESTRICTED_NFTABLES)

  logging.info("disabling nft firewall")
  subprocess.check_call(["nft", "-f", "/etc/nftables.conf"])


def disable_internet():
  for i in range(3):
    try:
      allowed_rs_host_to_ips = _allowed_hostnames_to_ips()
    except UnicodeError as e:
      logging.warning("[RETRYING] {}".format(e))
      # Sometimes, we get a UnicodeError: encoding with 'idna' codec failed (UnicodeError: Invalid character '\x8a')
      # Retry seems to work
      time.sleep(0.5)
      continue
    else:
      break

  allowed_hosts = list(allowed_rs_host_to_ips.items())
  allowed_hosts.append(["api.runelite.net", "127.0.0.1"])  # Definitely prevents contact to real runelite
  allowed_hosts = map(lambda item: " ".join((item[1], item[0])), allowed_hosts)
  allowed_hosts = "\n".join(allowed_hosts)

  hosts = RESTRICTED_HOSTS.format(hostname=socket.gethostname(), allowed_hosts=allowed_hosts)

  logging.info("writing restricted hosts into /etc/hosts")
  with open("/etc/hosts", "w") as f:
    f.write(hosts)

  # logging.info("disabling dns access via nsswitch")
  # shutil.copyfile(RESTRICTED_NSSWITCH_PATH, "/etc/nsswitch.conf")

  logging.info("writing new nftable rules")
  ipdaddr_rules = []
  for ip in allowed_rs_host_to_ips.values():
    ipdaddr_rules.append("    ip daddr {} accept".format(ip))

  # TODO: this rule is not strictly necessary, I think there are some DHCP
  # packets that we should probably allow.
  # Also need to allow pulseaudio
  ipdaddr_rules.append("    ip daddr {} accept".format(_get_default_gateway_linux()))
  ipdaddr_rules = "\n".join(ipdaddr_rules)

  with open("/etc/nftables.conf", "w") as f:
    f.write(RESTRICTED_NFTABLES.format(ipdaddr_rules=ipdaddr_rules))

  logging.info("enabling nft firewall")
  subprocess.check_call(["nft", "-f", "/etc/nftables.conf"])


def _get_default_gateway_linux():
  output = subprocess.check_output("ip route | grep default | grep eth0", shell=True)
  return output.decode("utf-8").strip().split(" ")[2]


def _get_rs_hostnames():
  response = requests.get(WORLD_URL)
  response.raise_for_status()
  hosts = []
  i = 6
  while i < len(response.content):
    i += 2 + 4
    s = ""
    while True:
      if response.content[i] == 0:
        break

      s += chr(response.content[i])
      i += 1

    if not s.strip():
      break

    hosts.append(s)

    i += 1
    while True:
      if response.content[i] == 0:
        break
      i += 1

    i += 1 + 1 + 2

  return hosts


def _get_ips(hosts):
  ips = {}
  for host in hosts:
    ips[host] = socket.gethostbyname(host)

  return ips


def _allowed_hostnames_to_ips():
  hostnames = _get_rs_hostnames()
  hostnames.append("oldschool.runescape.com")
  hostnames.append("runescape.com")
  hostnames.append("www.runescape.com")
  hostnames.append("services.runescape.com")
  hostnames.append("secure.runescape.com")
  # The other two containers...
  hostnames.append("10.222.182.3")
  hostnames.append("10.222.182.4")
  return _get_ips(hostnames)
