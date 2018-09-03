# Face Engine

[![Face Engine Docker Image](https://dockerbuildbadges.quelltext.eu/status.svg?organization=holymatch&repository=faceengine)](https://hub.docker.com/r/holymatch/faceengine/)

The source code is for my dissertations A Deep Learning Based Face Recognition Application with Augmented Reality on Microsoft Hololens. This server is used to recognize person based on face database. 

## Run the server
It is highly recommand to use [face system docker compose](https://github.com/holymatch/facesystem) to run the Face Engine with the [Face Information Server](https://github.com/holymatch/faceweb).

```sh
docker-compose up -d
```

## Setup Face Information Server and Face Engine in different hosts
To start the Face Information Server and Face Engine in different hosts, we need to expose ports to OS. Use `-p 5002:5002` to map the faceengine port to OS port 5002.

To keep the data permanently we can create docker volume to store the data. To create and map the volume to Docker, run the following comamand:
```sh
$ docker volume create faceengine-data-volume
```

Start the Docker with volume and hosts mapping
```sh
$ docker run -d \
  --name faceengine \
  --mount source=faceengine-data-volume,target=/Data/KnowFace \
  -p 5002:5002 \
  holymatch/faceengine:latest
```

