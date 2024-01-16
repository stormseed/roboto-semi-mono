FROM alpine:latest

RUN apk add --no-cache \
  fontforge \
  python3 \
  py3-pip \
  py3-setuptools

# COPY . /tmp/fonts

ENTRYPOINT ["/usr/bin/fontforge", "-lang=py", "-script", "/tmp/fonts/create_font.py"]
CMD ["settings-roboto.yaml"]
