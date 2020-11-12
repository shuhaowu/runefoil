## Bootstrap process

- MySQL is setup with seed data and right data.
- MongoDB is running and accepting requests.
- Tomcat configuration is built in the main container.
- NVIDIA GPU drivers are available.
  - If this is not available during runelite startup, it should be reinstalled.

## Runelite Startup Process

0. Verify container properly bootstrapped.
1. Stop all existing services: tomcat, static runelite server.
2. Be extra careful: kill all processes in the btw user.
3. Enable network connectivity.
4. Update runelite source code and compile.
5. Fetch price to seed MySQL database.
6. Disable network connectivity.
7. Start tomcat, static runelite server.
8. Finally: start runelite
9. When runelite quits, we need to stop tomcat8 and static runelite server to
   save resources.

As a note, systemd has ExecStartPre (0-7), ExecStart (8), and ExecStopPost (9).
This is not available in supervisord, so we need to reinvent a process manager
in code for docker. Also need to perform user switching.

## HTTP Service

The Runelite HTTP service is compiled during the built and deployed to a
tomcat8 process managed by supervisord. This is the only way I can reliably run
the HTTP service. I was unable to figure out how to get it to run standalone.

## Network restrictions

Performed by nftables within the container before and after runelite execution.
We get all the worlds via Jagex's proprietary API and then translates the
hostnames into IP addresses we are allowed to contact. We also allow
connectivity to the MySQL and MongoDB containers. Dropped packets are logged
via ulogd to /var/log/ulog/syslogemu.log.

The MySQL container has similar restrictions, as it also runs foreign code.
MongoDB is not subject to restrictions, tho.

## Other services

- MySQL runs locally with a custom built image on top of MariaDB, as we need to
  manually compile a runelite-specific mysql plugin.
  - The container is also built with some initial table creation code, which is
    cherry-picked from runelite and may become out of sync.
- MongoDB just runs normally as its own container.

## Devices

GPU is shared into the container. In order to not use nvidia's docker thing and
be generic, regular docker is used and we detect/install nvidia drivers every
time it is launched.

Sound is setup via pulseaduio by forwarding the pulse audio unix socket and cookie into the container via https://github.com/mviereck/x11docker/wiki/Container-sound:-ALSA-or-Pulseaudio#pulseaudio-as-system-wide-daemon
