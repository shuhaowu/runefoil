FROM ubuntu:focal

ARG uid
ARG gid

ENV BTW_USER btw
ENV TOMCAT_USER tomcat

RUN set -xe; \
    addgroup --gid $gid $BTW_USER; \
    adduser --gecos "" --disabled-password --uid $uid --gid $uid $BTW_USER; \
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
      x11-apps \
      git \
      make \
      maven \
      curl \
    ; \
    # Begin installing tomcat8
    cd /tmp; \
    adduser --system --group $TOMCAT_USER; \
    mkdir -p /opt/tomcat8; \
    wget -O tomcat.tar.gz --progress=dot:mega https://mirror.dsrg.utoronto.ca/apache/tomcat/tomcat-8/v8.5.59/bin/apache-tomcat-8.5.59.tar.gz; \
    echo "3106fa39f1859ba31c87d245eaf8efe9c1f2f4837dc4f259c245d2c9b55d3593e97a9925e7d012d397987279965b8e24d940cfdda062d8ac9b64e41396120bd9 tomcat.tar.gz" | sha512sum --strict --check -; \
    tar xf tomcat.tar.gz -C /opt/tomcat8 --strip-components=1; \
    chown -R root:$TOMCAT_USER /opt/tomcat8; \
    chmod 0750 /opt/tomcat8/conf; \
    chmod 0640 /opt/tomcat8/conf/*; \
    chown -R $TOMCAT_USER:$TOMCAT_USER /opt/tomcat8/webapps /opt/tomcat8/work /opt/tomcat8/temp /opt/tomcat8/logs; \
    apt-get purge -y --autoremove wget gnupg software-properties-common; \
    apt-get clean; \
    rm /var/lib/apt/list/* -rf; \
    rm /tmp/* -rf;

COPY supervisord.conf /etc/supervisord.conf
