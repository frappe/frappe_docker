FROM ubuntu:16.04
MAINTAINER Giovanni Bassi <giggio@giggio.net>

RUN mkdir /app
WORKDIR /app
RUN apt-get update && \
    apt-get install -y git curl build-essential vim libfontconfig1 libgconf-2-4 libnss3
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.31.4/install.sh | bash
RUN [ "/bin/bash", "-c", "source $HOME/.nvm/nvm.sh && nvm i 0.12 && nvm i 4 && nvm i 6 && nvm i 7 && nvm alias default 7" ]
RUN git clone https://github.com/giggio/node-chromedriver.git . && git remote add ssh git@github.com:giggio/node-chromedriver.git