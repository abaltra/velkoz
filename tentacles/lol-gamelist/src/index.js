const axios = require('axios').default;
const AWS = require('aws-sdk');
const RIOT_API_KEY = process.env.RIOT_API_KEY;
const NEW_GAME_FOUND_TOPIC_ARN = process.env.NEW_GAME_FOUND_TOPIC_ARN

AWS.config.update({ region: "us-east-1" });
const sns = new AWS.SNS()

const PLATFORMS = {
    'br': 'br1',
    'eune': 'eun1',
    'euw': 'euw1',
    'kr': 'kr',
    'lan': 'la1',
    'las': 'la2',
    'na': 'na1',
    'oce': 'oc1',
    'tr': 'tr1',
    'ru': 'ru',
    'jp': 'jp1',
    'pbe': 'pbe'
}

exports.handler = async (event, context) => {
    //console.log('Received event:', JSON.stringify(event, null, 2));
    const message = event.Records[0].Sns.Message;

    // console.log(Object.keys(message));
    const parsedMessage = JSON.parse(message);
    
    const platform = PLATFORMS[parsedMessage.gameRegion];

    if (!platform) {
        throw `Failed getting platform for region ${parsedMessage.gameRegion}`;
    }

    let url = `https://${platform}.api.riotgames.com/lol/match/v4/matchlists/by-account/${parsedMessage.accountId}`;

    if (parsedMessage.lastUpdate) {
        var date = new Date(parsedMessage.lastUpdate);
        url = `${url}?beginTime=${date.getTime()}`;
    }

    const headers = {};
    headers['X-Riot-Token'] = RIOT_API_KEY;

    console.log(`Getting match list from ${url} with headers ${JSON.stringify(headers)}`);

    let gameList;
    try {
        gameList = await axios.get(url, { headers: headers });    
    } catch (error) {
        console.warn(`Failed retrieving match list with code ${gameList.status}`);
        return;
    }
    
    const gameListData = gameList.data.matches;

    const promises = [];
    for (let i = 0; i < gameListData.length; i++) {
        let game = gameListData[i];
        promises.push(sns.publish({
            Message: JSON.stringify({
                gameId: game.gameId,
                playerAccountId: parsedMessage.accountId
            }),
            TopicArn: NEW_GAME_FOUND_TOPIC_ARN
        }).promise());
    }

    console.log(`Triggering ${gameListData.length} new game events`)
    await Promise.all(promises);

    return message;
};
