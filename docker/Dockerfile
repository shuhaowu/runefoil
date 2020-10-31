FROM ubuntu:focal

ARG uid
ARG gid

RUN set -xe; \
    addgroup --gid $gid btw; \
    adduser --gecos "" --disabled-password --uid $uid --gid $gid btw; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get install -y wget gnupg software-properties-common; \
    wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | apt-key add -; \
    add-apt-repository --yes https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/; \
    apt-get -y install \
      adoptopenjdk-8-hotspot \
      git \
      make \
      maven \
    ; \
    apt-get purge -y --autoremove wget gnupg software-properties-common; \
    apt-get clean; \
    rm /var/lib/apt/list/* -rf
