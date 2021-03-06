# Cousin-IDDD

A simple little bridge repo:

1.  Monitors the directory to which your [Podgrab](https://github.com/akhilrex/podgrab) install fetches your podcasts,
2.  Adds ID3 (title, album, artist, track number) tags to any new .mp3 files based on Podgrab's metadata, and
3.  Builds one playlist per podcast in your [Navidrome*](https://github.com/navidrome/navidrome) install, which features the last X episodes in reverse-chronological order.

* NOTE: Since Navidrome implements the Subsonic API, it's possible this library could work with other Subsonic-inspired projects. This is not tested, so proceed at your own risk.

**Actually, a broader note:** This _entire_ repo is in alpha stages. It shouldn't be relied upon in production — indeed, it's just a personal, duct-tape-and-bailing-wire project that I'm uploading in part so I can install it more easily.

## How to use

### First, create a Dockerfile. Mine looks like this:

```Dockerfile
FROM python:3.9 as build

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN pip install pipenv

WORKDIR /build
RUN git clone https://github.com/allanjamesvestal/Cousin-IDDD.git .

RUN bash -c 'PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy'

# Run the application
ENTRYPOINT ["pipenv", "run", "python", "monitor_folder.py"]
CMD []
```

### Next, build the image.

```sh
docker build test-release .
```

### Then, give it a go with `docker run`.

```sh
docker run \
  --volume /path/to/cousin-iddd/config:/config \
  --volume /path/to/cousin-iddd/logs:/logs \
  --volume /path/to/podgrab-assets:/watched_media \
  --env NAVIDROME_HOST=<192.168.0.1:4533> \
  --env NAVIDROME_USERNAME=<my_user> \
  --env NAVIDROME_PASSWORD=<my_pass> \
  --env PODGRAB_HOST=<192.168.0.1:8080> \
  --env PODGRAB_USERNAME=<podgrab> \
  --env PODGRAB_PASSWORD=<my_pass> \
  test-release .
```

### If you want to use `docker-compose`, my working implementation is like so:

```yaml
version: "3.9"
services:
  cousin-iddd:
    build: ./cousin-iddd
    environment:
      - NAVIDROME_HOST=<192.168.0.1:4533>
      - NAVIDROME_USERNAME=<my_user>
      - NAVIDROME_PASSWORD=<my_pass>
      - PODGRAB_HOST=<192.168.0.1:8080>
      - PODGRAB_USERNAME=<podgrab>
      - PODGRAB_PASSWORD=<my_pass>
    restart: always
    volumes:
      - /path/to/cousin-iddd/config:/config
      - /path/to/cousin-iddd/logs:/logs
      - /path/to/podgrab-assets:/watched_media
```
