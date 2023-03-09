# Adapted from https://github.com/algorand-devrel/docker-algorand-gitpod

###############
# Build indexer 
###############
FROM golang:1.17.8-bullseye as indexer-builder

RUN apt-get update 
RUN apt-get install -y libboost-dev libtool

ARG repo=algorand/indexer
ARG ref=master

ADD https://github.com/${repo}/archive/${ref}.tar.gz /tmp/tarball.tar.gz
RUN tar -xzvf /tmp/tarball.tar.gz -C /usr/local/src/
RUN mv /usr/local/src/indexer* /usr/local/src/indexer

WORKDIR /usr/local/src/indexer

# Build process relies on submodules, so we need to setup git
RUN git init
RUN git checkout -b ${ref}
RUN git remote add origin https://github.com/${repo}
RUN git fetch origin ${ref}
RUN git reset --hard origin/${ref}
RUN make

FROM node:16.19.0-bullseye as dappflow-builder

WORKDIR /workdir

################
# Build dappflow
################
ADD https://github.com/joe-p/dappflow/archive/gitpod.tar.gz /tmp/tarball.tar.gz
RUN tar -xzvf /tmp/tarball.tar.gz -C ./
RUN mv ./dappflow* ./dappflow

WORKDIR /workdir/dappflow

RUN yarn install && yarn build

########################
# Build gitpod workspace
########################
FROM gitpod/workspace-postgres:2022-12-15-12-38-23 as gitpod-workspace
COPY --from=indexer-builder /usr/local/src/indexer/cmd/algorand-indexer/algorand-indexer /usr/local/bin/algorand-indexer

# Install python 3.10.7
RUN pyenv install -v 3.10.7
RUN pyenv global 3.10.7

# Install beaker/SDK
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

# Install algodeploy
ADD https://github.com/joe-p/algodeploy/archive/master.tar.gz ./tarball.tar.gz
RUN sudo chown gitpod:gitpod ./tarball.tar.gz
RUN tar -xzvf ./tarball.tar.gz -C ./
RUN rm ./tarball.tar.gz 
RUN mv ./algodeploy* ./algodeploy
RUN pip install -r ./algodeploy/requirements.txt

# Create network with algodeploy
ARG TAG=stable
RUN ./algodeploy/algodeploy.py create $TAG
RUN echo "export PATH=$PATH:/home/gitpod/.algodeploy/localnet/bin" >> ~/.bashrc

RUN yarn global add serve
COPY --from=dappflow-builder /workdir/dappflow/build /home/gitpod/dappflow