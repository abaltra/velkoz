#!/bin/bash

TENTACLES="tentacles/*"
ROOT=$(pwd)
GAME_PREFIX=$1

for t in $TENTACLES
do
    printf "Processing tentacle $t\n"
    cd $t
    if [ ! -d "src" ]; then
        printf "src folder not found for tentacle $t. Skipping.\n\n"
        cd $ROOT
        continue
    fi

    if [ ! -d "terraform" ]; then
        printf "terraform folder not found for tentacle $t. Skipping\n\n"
        cd $ROOT
        continue
    fi

    cd src
    npm install --production

    IFS_BACK=$IFS
    IFS="/"
    read -ra PARTS <<< "$t"
    IFS=$IFS_BACK
    TENTACLE_NAME=${PARTS[1]}
    rm "../terraform/$GAME_PREFIX-$TENTACLE_NAME-lambda.zip"
    zip -r "$GAME_PREFIX=$TENTACLE_NAME-lambda.zip" *
    mv "$GAME_PREFIX-$TENTACLE_NAME-lambda.zip" ../terraform/

    printf "Created terraform/$GAME_PREFIX-$TENTACLE_NAME-lambda.zip\n" 
done