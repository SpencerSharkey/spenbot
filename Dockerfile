FROM spencersharkey/disco:latest
ENV DISCO_ARGS --run-bot --plugins discoexample
ADD * /opt/
