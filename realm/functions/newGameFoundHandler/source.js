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
    const { fullDocument } = changeEvent
    const { gameId, region } = fullDocument

    console.log(`Getting raw game data for game ${gameId} in ${region}`)
    const collection = context.services.get("velkoz").db("velkoz").collection("game");
    const players_collection = context.services.get("velkoz").db("velkoz").collection("player");
    const game_update_requests_collection = context.services.get("velkoz").db("velkoz").collection("game_update_requests");
    const game = await collection.findOne({ gameId: gameId, region: region })

    console.log(Object.keys(collection))

    if (!game)
    {
      const url = `https://${region}.api.riotgames.com/lol/match/v4/matches/${gameId}?api_key=${context.values.get("riot_key")}`
      console.log(`Getting raw game from ${url}`)
      let raw_game = await context.http.get({ url: url })
      raw_game = EJSON.parse(raw_game.body.text())
      await collection.updateOne({ gameId: gameId }, { $set: parseGame(raw_game, region) }, { upsert: true });
      const players_to_update_promises = raw_game.participantIdentities.map(p => { players_collection.updateOne({ accountId: p.player.accountId }, { $set: { accountId: p.player.accountId, region: region, summonerName: p.player.summonerName, lastGame: gameId } }, { upsert: true }) })
      await Promise.all(players_to_update_promises)
    } else {
      console.log(`Game ${gameId} already inserted`);
    }

    await game_update_requests_collection.deleteOne({ _id: changeEvent.documentKey._id });
  
};

function parseGame(raw_game, region) {
  const { gameId, gameCreation, gameDuration, queueId, seasonId, teams, participants, participantIdentities } = raw_game

  const parsedTeams = teams.map(t => {
    return {
      win: t.win === "Win",
      id: t.teamId,
      players: participants.filter(p => p.teamId === t.teamId).map(p => { return {
        participantId: p.participantId,
        championId: p.championId,
        spell1Id: p.spell1Id,
        spell2Id: p.spell2Id,
        item0: p.stats.item0,
        item1: p.stats.item1,
        item2: p.stats.item2,
        item3: p.stats.item3,
        item4: p.stats.item4,
        item5: p.stats.item5,
        item6: p.stats.item6,
        kills: p.stats.kills,
        deaths: p.stats.deaths,
        assists: p.stats.assists,
        goldEarned: p.stats.goldEarned,
        accountId: participantIdentities.filter(pi => pi.participantId === p.participantId).map(pi => pi.player.accountId)[0]
      } })
    }    
  });

  return {
    gameId,
    region,
    gameCreation,
    gameDuration,
    queueId,
    seasonId,
    teams: parsedTeams
  }
}
