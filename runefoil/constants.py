import os.path

RL_BASEDIR = "/opt/runelite"
RL_JAR_PATH = os.path.join(RL_BASEDIR, "client.shaded.jar")
RL_VERSION_PATH = os.path.join(RL_BASEDIR, "current-version")
RL_SOURCE_PATH = "/opt/runelite-src"

RL_WAR_BASEPATH = "/var/lib/tomcat7/webapps"
FILES_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "files")
