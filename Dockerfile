#e the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
COPY . ./usr/bin/bash/.env 
COPY . ./usr/bin/bash/.model
# Install production dependencies.
RUN make install

EXPOSE 8080

CMD [ "main.py" ]
ENTRYPOINT [ "python" ]