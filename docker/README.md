# Run TPA from a docker container

This Dockerfile should be used to run tpa from a container.

 Build this container image like this from TPA source folder

``` bash
  docker build -f docker/Dockerfile -t tpaexec:$(git describe --tags) -t tpaexec:latest .
```

 To use the container image, create a shell alias like this

``` bash
   alias tpaexec="docker run --rm -v $PWD:/work -v $HOME/.git:/root/.git -v $HOME/.gitconfig:/root/.gitconfig \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -e USER_ID=$(id -u) -e GROUP_ID=$(id -g) tpaexec"
```

 Then run commands like this

``` bash
   tpaexec configure cluster -a M1 --postgresql 15 --failover-manager patroni --platform docker
   tpaexec deploy cluster
```
