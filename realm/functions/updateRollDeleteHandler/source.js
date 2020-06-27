exports = async function(changeEvent) {
  /*
    A Database Trigger will always call a function with a changeEvent.
    Documentation on ChangeEvents: https://docs.mongodb.com/manual/reference/change-events/

    Access the _id of the changed document:
    const docId = changeEvent.documentKey._id;

    Access the latest version of the changed document
    (with Full Document enabled for Insert, Update, and Replace operations):
    const fullDocument = changeEvent.fullDocument;

    const updateDescription = changeEvent.updateDescription;

    See which fields were changed (if any):
    if (updateDescription) {
      const updatedFields = updateDescription.updatedFields; // A document containing updated fields
    }

    See which fields were removed (if any):
    if (updateDescription) {
      const removedFields = updateDescription.removedFields; // An array of removed fields
    }

    Functions run by Triggers are run as System users and have full access to Services, Functions, and MongoDB Data.

    Access a mongodb service:
    const collection = context.services.get(<SERVICE_NAME>).db("db_name").collection("coll_name");
    const doc = collection.findOne({ name: "mongodb" });

    Note: In Atlas Triggers, the service name is defaulted to the cluster name.

    Call other named functions if they are defined in your application:
    const result = context.functions.execute("function_name", arg1, arg2);

    Access the default http client and execute a GET request:
    const response = context.http.get({ url: <URL> })

    Learn more about http client here: https://docs.mongodb.com/stitch/functions/context/#context-http
  */
  
  const docId = changeEvent.documentKey._id;
  const [ accountId, region ] = docId.split(":")
  console.log(`Got doc ${docId} updated. Gonna use api key: ${context.values.get('riot_key')}`)

  const games_collection = context.services.get("velkoz").db("velkoz").collection("game");
  const game_download_requests_collection = context.services.get("velkoz").db("velkoz").collection("game_update_requests");

  let last_game = (await games_collection.find({ "teams.players.accountId": accountId }, { gameId: 1, gameCreation: 1, gameDuration: 1 }).sort({ gameCreation: -1 }).limit(1).toArray())[0];

  let last_game_id = 0;

  if (last_game)
  {
    const last_game_ended = last_game.gameCreation + last_game.gameDuration * 1000;
    const now = Date.now();
    if (now - last_game_ended < 600000) {
      // 10 minutes since game ended
      console.log(`Last game ended 10 minutes ago. Not checking yet`);
      return;
    }
    last_game_id = last_game.gameId;
  }

  const url = `https://${region}.api.riotgames.com/lol/match/v4/matchlists/by-account/${accountId}?api_key=${context.values.get("riot_key")}`
  console.log(`Gonna call ${url}`)

  let matches = await context.http.get({
    url: url
  })

  matches = EJSON.parse(matches.body.text())
  
  let new_match_ids = matches.matches.slice(0, 2).filter(m => +m.gameId > last_game_id ).map(m => m.gameId);
  if (new_match_ids.length === 0) {
    console.log(`No new matches found for account ${accountId}`);
    return;
  }

  console.log(`Need to get data for following match ids: ${JSON.stringify(new_match_ids)}`)
  let new_game_requests = new_match_ids.map(m => { return { gameId: m, region: region, ttl: Date.now()}})
  console.log(`Inserting ${JSON.stringify(new_game_requests)}`)
  await game_download_requests_collection.insertMany(new_game_requests)
};
