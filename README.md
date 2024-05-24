Bluetooth low energy stack for software defined radio


# Build docker image
```sh
docker build -t ghcr.io/zaporozhets/openble:latest .
```

# Run image localy
```sh
docker run -it --net=host -v "$(pwd)":"$(pwd)":rw --workdir "$(pwd)" ghcr.io/zaporozhets/openble:latest bash
```

# Run tests for baseband
```sh
pytest -s ./baseband/test/
```
