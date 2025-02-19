#!/bin/sh

name=old-tom
version=1.3.3


USER=root
REMOTE_HOST=vps.jeremymeadows.dev
IDENTITY_KEY=~/.ssh/vps
APP_ROOT=/bots/old_tom

set -e

docker build --network host -t $name:$version .
docker image tag $name:$version $name:latest

if [ "$1" = "--run" ]; then
    docker compose down
    docker compose up -d
fi

if [ "$1" = "--deploy" ]; then
    scp -i $IDENTITY_KEY docker-compose.yaml $USER@$REMOTE_HOST:$APP_ROOT
    docker image save $name:$version | ssh -i $IDENTITY_KEY $USER@$REMOTE_HOST "docker image load"
    ssh -i $IDENTITY_KEY $USER@$REMOTE_HOST << END
        cd $APP_ROOT
        mkdir -p data

        docker image tag $name:$version $name:latest
        docker compose down
        docker compose up -d
END

    echo "Deployed $name:$version to $REMOTE_HOST"
fi
