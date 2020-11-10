import os.path

RL_BASEDIR = "/opt/runelite"
RL_JAR_PATH = os.path.join(RL_BASEDIR, "client.shaded.jar")
RL_VERSION_PATH = os.path.join(RL_BASEDIR, "current-version")
RL_SOURCE_PATH = "/opt/runelite/src"
RL_STATIC_PATH = "/opt/static.runelite.net"

RUNEFOIL_BASEDIR = "/opt/runefoil"
RUNEFOIL_RL_SOURCE_PATH = os.path.join(RUNEFOIL_BASEDIR, "shared", "runelite")
OPENGL_DISABLED_PATH = os.path.join(RUNEFOIL_BASEDIR, "shared", "opengl-disabled")
GDK_SCALE_PATH = os.path.join(RUNEFOIL_BASEDIR, "shared", "gdk-scale")

TOMCAT_WEBAPP_DIR = "/opt/tomcat8/webapps"
FILES_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "files")
PATCHES_PATH = os.path.join(FILES_PATH, "patches")
