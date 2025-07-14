# Run TPA from a docker container

This Dockerfile should be used to run TPA from a container.

 Build this container image like this from TPA source folder:

``` bash
  docker build -f docker/Dockerfile \
      --build-arg TPA_VER=$(git describe) -t tpaexec:latest .
```

 To use the container image, create a shell alias like this

``` bash
   alias tpaexec="docker run --rm -v $PWD:/work \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -e EDB_SUBSCRIPTION_TOKEN=$EDB_SUBSCRIPTION_TOKEN tpaexec"
```

 Then run commands like this

``` bash
   tpaexec configure cluster -a M1 --postgresql 15 --failover-manager patroni --platform docker
   tpaexec deploy cluster
```
