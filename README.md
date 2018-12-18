Runefoil
========

Run Runelite in a secure environment such that it's not possible for it to
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

Runefoil runs Runelite inside an unprivileged LXD container with nftables
firewall rules allowing only connections to official Jagex Servers. 

The API server of Runelite is also run inside this container to ensure no data
leaves tho container. All the setup of this is done via ansible.

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
- You need to [install LXD](https://linuxcontainers.org/lxd/getting-started-cli/).
- You need to [install ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html).

Instructions to run:

```
$ # Need my fork of lxdock as it has x11 support. PR for this to the upstream
$ # repository is pending: https://github.com/lxdock/lxdock/pull/143
$ git clone https://github.com/shuhaowu/lxdock.git
$ cd lxdock
$ python3 setup.py install --user
$ # You should add the line below to your .bashrc if not already
$ export PATH="`python3 -m site --user-base`/bin:$PATH"

$ cd ~/apps # whereever you want to put it
$ git clone https://github.com/shuhaowu/runefoil.git
$ cd runefoil

$ # you can change the below into any directory you want.
$ # this directory will contain your runelite settings. For example you can
$ # dropbox sync it.
$ echo "RUNELITE_SETTINGS_PATH=./dot-runelite" > .env
$ mkdir dot-runelite

$ # In the future, I'll replace these scripts with a small GUI program
$ ./scripts/setup-container.sh
$ ./scripts/start-runelite.sh

$ # In another terminal, as the first time setup can take quite a while to
$ # download all the maven stuff and compile runelite. This allows you
$ # to see that there are some progress.
$ ./scripts/tail-runelite-logs.sh
```

### Issues with rendering ###

If you experience issues with rendering ()b)bbintel GPU beaware), disable opengl via
`scripts/disable-opengl.sh`. To re-enable opengl, use
`scripts/enable-opengl.sh`.

Upgrading Runefoil
------------------

If runefoil changed and needs an upgrade, you might be best served to run:

```
$ lxdock provision
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
  - In the future, lxdock will be modified to include support to launch
    multiple containers from a single base.
  - As a work around right now, you can clone the runefoil repo multiple times
    and launch multiple containers.
- API server does not necessarily have all the features.
  - Feed updates do not fetch twitter/runelite updates for obvious reasons.
  - Pricing information may be inaccurate. It is only updated on every boot.
