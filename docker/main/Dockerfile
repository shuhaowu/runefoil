FROM ubuntu:focal

ARG uid
ARG gid

ENV BTW_USER btw
ENV TOMCAT_USER tomcat

RUN set -xe; \
    addgroup --gid $gid $BTW_USER; \
    adduser --gecos "" --disabled-password --uid $uid --gid $gid $BTW_USER; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get install -y wget gnupg software-properties-common; \
    wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | apt-key add -; \
    add-apt-repository --yes https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/; \
    apt-get -y install \
      adoptopenjdk-11-hotspot \
      supervisor \
      pulseaudio \
      nftables \
      mesa-utils \
      python3-setuptools \
      python3-requests \
      python3-pymysql \
      x11-apps \
      iproute2 \
      ulogd2 \
      sudo \
      git \
      make \
      maven \
      curl \
      # NVIDIA driver requirements
      kmod \
    ; \
    # Begin installing tomcat8
    cd /tmp; \
    adduser --system --group $TOMCAT_USER; \
    mkdir -p /opt/tomcat8; \
    wget -O tomcat.tar.gz --progress=dot:mega https://archive.apache.org/dist/tomcat/tomcat-8/v8.5.60/bin/apache-tomcat-8.5.60.tar.gz; \
    echo "460b4d0f2d445670b69ff97d4295628b9ce444c294e301b4c0c5e4c48b42bb1a642769f075dfe105b7d7257d9aba62b75a6ea5b6fb65487891ab23d7bb3d6140 tomcat.tar.gz" | sha512sum --strict --check -; \
    tar xf tomcat.tar.gz -C /opt/tomcat8 --strip-components=1; \
    chown -R root:$TOMCAT_USER /opt/tomcat8; \
    chmod 0750 /opt/tomcat8/conf; \
    chmod 0640 /opt/tomcat8/conf/*; \
    rm -rf /opt/tomcat8/webapps/*; \
    chown -R $TOMCAT_USER:$TOMCAT_USER /opt/tomcat8/webapps /opt/tomcat8/work /opt/tomcat8/temp /opt/tomcat8/logs; \
    cd /opt/tomcat8/lib; \
    # Installing required tomcat plugins
    wget https://repo1.maven.org/maven2/org/mongodb/mongo-java-driver/3.10.2/mongo-java-driver-3.10.2.jar; \
    echo "bfeba21e18c3b63e62f3a99cf6787a5e3c0a7453a08e3dde5285e0daa2d6baca mongo-java-driver-3.10.2.jar" | sha256sum --strict --check -; \
    wget https://downloads.mariadb.com/Connectors/java/connector-java-2.2.3/mariadb-java-client-2.2.3.jar; \
    echo "f367db6535798fdc990a183197d6e8ec5b4a170877e9a9f9084376d66cf2acbb  mariadb-java-client-2.2.3.jar" | sha256sum --strict --check -; \
    chown root:tomcat *; \
    chmod 0640 *; \
    apt-get purge -y --autoremove gnupg software-properties-common; \
    apt-get clean; \
    rm /var/lib/apt/list/* -rf; \
    rm /opt/tomcat8/conf/context.xml; \
    rm /tmp/* -rf;

COPY supervisord.conf /etc/supervisord.conf
COPY custom.sh /etc/profile.d/custom.sh
COPY context.xml /opt/tomcat8/conf/context.xml
