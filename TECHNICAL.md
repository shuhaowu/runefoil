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

