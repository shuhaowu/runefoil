Runefoil
========

Run Runelite in a secure environment such that it is unlikely for it to
exfiltrate data(-). The name Runefoil is inspired by the tinfoil hat, as we are
paranoid enough to run it in such a convoluted environment.

**Runelite is currently partially closed source due to the injector. This means
the security assumption that the runelite source repository is safe is
partially broken.**

(-) Not 100% secure, see security considerations below.

Runefoil is designed to be relatively small. I'm hoping to keep the number of
lines of code low, such that anyone can easily audit it.

This project is super experimental right now, expect issues.

How does it work?
-----------------

Runefoil used to run Runelite in an unprivileged LXD container with nftable
rules allowing only connections to official Jagex servers. It is now running
inside a docker-based setup (via docker-compose) as maintaining the LXD setup
became increasingly difficult due to the lack of maintenance on lxdock.

The API server of Runelite is also run inside the container to ensure no data
leaves tho container. All the setup of this is done via the Dockerifle.

Runefoil also compiles Runelite locally inside the container instead of
downloading the binary. It checks for updates to Runelite everytime you launch
it and compiles the new code to the corresponding `runelite-parent-<version>`
tag from the https://github.com/runelite/runelite repository.

How do I run it?
----------------

Prerequisites: 

- This project only supports Linux hosts. It will not work on other platforms
  and they will not be supported in the future either.
- You run X11.
- You need to install docker and docker-compose.

Instructions to run:

```
$ cd ~/apps # whereever you want to put it
$ git clone https://github.com/shuhaowu/runefoil.git
$ cd runefoil

$ ./docker/start.sh
$ ./docker/runelite.sh
```

### Advanced usage ###

- If you experience issues with rendering, try either disabling or enabling
  OpenGL viathe script `docker/toggle-opengl.sh`. More information:
  https://github.com/runelite/runelite/wiki/Disable-Hardware-Acceleration
- If you're having trouble with scaling for HiDPI displays, use the script
  `docker/set-gdk-scale.sh` with the argument `1` or `2`. Example:
  `docker/set-gdk-scale.sh 2`. This sets `GDK_SCALE`. See:
  https://github.com/runelite/runelite/issues/2719.
- Runelite settings can be exported away from the container and put into
  a host-visible directory that can be synchronized somewhere. To do this:
  `echo "export DOT_RUNELITE_DIR=/path/to/runelite/settings/dir" > .env` here
  before recreating the docker containers via `docker/start.sh`

### Troubleshooting ###

- If Runelite doesn't start and the error says there are multiple instances
  running and you're sure there's no instances running:
  - `docker-compose stop` to stop all containers
  - `docker/start.sh` to restart all containers.
  - `docker-compose exec main rm -f /opt/runelite/lock` to remove the lock file
  - `docker/runelite.sh` to restart runelite.

Upgrading Runefoil
------------------

If runefoil changed and needs an upgrade, you might be best served to run:

```
$ docker/start.sh
```

**WARNING: THIS WILL TERMINATE YOUR RUNESCAPE SESSION.**

Security Considerations
-----------------------

Even though Runelite is open source software, there are no guarantees that the
downloaded binary is not hostile, even if we trust the developers and the
community. An extreme example would be a compromise on a developer's machine
due to a targeted attack. Such an attack is unlikely, perhaps even infeasible.
However, in one's most paranoid state, you cannot neglect such a possibility.

This situation could lead to a compromised binary download, or
even source tree. By the time someone notices and post it to reddit, it may be
too late already and your RS account and other digital assets (incl. but not
limited to your email, facebook, etc) may be stolen already.

Runefoil treats all Runelite code as hostile. It mitigates the security
issues by running the hostile code in a restricted environment such that it
can only make network connections to runescape's servers. This is enforced in a
container via nftables. To avoid information disclosure via DNS, DNS requests
are forbidden as well. It is replaced with a hosts file with the correct IP
address for all OSRS server hostnames and other required RS hostnames.
Operations requiring network access such as update checking is done only be
trusted code present in this repository.

Update checking is done when the application is in start up mode. When the
application starts, it first kills all the custom processes that can possibly
be started by Runelite. It then relaxes the network restrictions and proceeds
with updating the runelite client. After this update but before any binaries
can start, it restricts the network.

However, this is not 100% fool proof. Some possible information disclosure
route:

- Runelite binary posts your credential via the runescape website, via forums
  or via messages.
  - This mode of information disclosure CAN be fixed, although it requires more
    in depth analysis of the HTTP connections Runescape itself makes before
    setting the rules.
- Runelite binary posts your credential via a direct message in game.
  - This can be fixed if you get yourself permamuted in game.
- Runelite compilation process has malicious code.

Due to the partially closed source nature of Runelite, some of these operations
could be hidden in the closed source parts.

That said, even in the most paranoid scenario, Runefoil should be secure for
the following reasons:

- **A breach of Runelite is very very very very VERY very unlikely to occur**.
  - This is why people use it directly without using Runefoil.
- If a breach of Runelite occurs, it is much more likely that it happens to the
  download server as opposed to the source repo directly.
  - Since runefoil compiles the code from source, this breach will not affect
    runefoil.
- ~~A breach will likely be the result of a significant effort, with only a short
  amount of time before it is noticed by someone. This means that:~~
  - *This is not likely to be noticed if it is in the closed source Runelite*.
  - Any malicious code will likely not target Runefoil, given that it will have
    essentially 0 users.
  - Any malicious code will be noticed before an update even occurs locally.
    - TODO: in the future, there'll be a GUI program linking you to the updates
      and a diff of the code base on github.

However, if you're truly paranoid, just stick with the official client.

Known Issues
------------

In addition to the security issues above, some usability issues remains:

- You can only run 1 RL instance at a time. 
  - This is a security measure to ensure no race conditions can occur as we
    lower the network restrictions during the launch process.
  - As a work around right now, you can clone the runefoil repo multiple times
    and launch multiple containers.
- API server does not necessarily have all the features.
  - Feed updates do not fetch twitter/runelite updates for obvious reasons.
  - Pricing information may be inaccurate. It is only updated on every boot.
