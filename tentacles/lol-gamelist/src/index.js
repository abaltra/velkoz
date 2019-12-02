const axios = require('axios').default;
const RIOT_API_KEY = process.env.RIOT_API_KEY;

const PLATFORMS = {
    'br': 'BR1',
    'eune': 'EUN1',
    'euw': 'EUW1',
    'kr': 'KR',
    'lan': 'LA1',
    'las': 'LA2',
    'na': 'NA1',
    'oce': 'OC1',
    'tr': 'TR1',
    'ru': 'RU',
    'jp': 'JP1',
    'pbe': 'PBE'
}

exports.handler = async (event, context) => {
    //console.log('Received event:', JSON.stringify(event, null, 2));
    const message = event.Records[0].Sns.Message;
    console.log(message);
    // console.log(Object.keys(message));
    const parsedMessage = JSON.parse(message);
    const documentId = parsedMessage.documentKey._id;

    if (!documentId) {
        throw "documentId not found for message";
    }

    const [ gameId, userId, accountId, gameRegion ] = documentId.split('|');
    
    const platform = PLATFORMS[gameRegion];

    if (!platform) {
        throw `Failed getting platform for region ${gameRegion}`;
    }

    const url = `https://${platform}.api.riotgames.com/lol/match/v4/matchlists/by-account/${accountId}`;

    const headers = {};
    headers['X-Riot-Token'] = RIOT_API_KEY;

    const gameList = await axios.get(url, { headers: headers });
    
    console.log(gameList.data);

    return message;
};
