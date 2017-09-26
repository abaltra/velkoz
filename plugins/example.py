import datetime

#Riot has BOT, DUO_BOT and some other flavors. These champs are flagged as "marksmen" in their ID, so in case of finding a bot lane champion, check against this list to know if support or ADC
MARKSMEN_IDS = {
	22: 'ASHE', 268: 'AZIR', 42: 'CORKI', 119: 'DRAVEN', 81: 'EZREAL', 104: 'GRAVES', 126: 'JAYCE', 202: 'JHIN', 222: 'JINX', 429: 'KALISTA', 85: 'KENNEN', 203: 'KINDRED', 96: 'KOGMAW', 236: 'LUCIAN', 21: 'MISSFORTUNE', 133: 'QUINN', 15: 'SIVIR', 17: 'TEEMO', 18: 'TRISTANA', 29: 'TWITCH', 6: 'URGOT', 110: 'VARUS', 67: 'VAYNE', 51: 'CAITLYN'
}

ENDPOINTS_TO_REGIONS_MAP = {
    'na1': 'na',
    'ru1': 'ru',
    'kr': 'kr',
    'br1': 'br',
    'oc1': 'oce',
    'jp1': 'jp',
    'eun1': 'eun',
    'euw1': 'euw',
    'tr1': 'tr1',
    'la1': 'lan',
    'la2': 'las'
}

def process(m, summonerId=None, mongoHelper=None):
    stats_to_aggregate = ['kills', 'deaths', 'assists', 'totalDamageDealt', 'magicDamageDealt', 'physicalDamageDealt', 'trueDamageDealt', 'totalDamageDealtToChampions', 'magicDamageDealtToChampions', 'physicalDamageDealtToChampions', 'trueDamageDealtToChampions', 'timeCCingOthers', 'totalDamageTaken', 'magicalDamageTaken', 'physicalDamageTaken', 'trueDamageTaken', 'totalHeal', 'totalUnitsHealed', 'damageSelfMitigated', 'damageDealtToObjectives', 'damageDealtToTurrets', 'goldEarned', 'goldSpent', 'turretKills', 'inhibitorKills', 'totalMinionsKilled', 'neutralMinionsKilled', 'neutralMinionsKilledTeamJungle', 'neutralMinionsKilledEnemyJungle', 'totalTimeCrowdControlDealt', 'visionWardsBoughtInGame', 'sightWardsBoughtInGame', 'wardsPlaced', 'wardsKilled']

    participant_identity = None
    participant = None
    match_doc = dict()
    totals_incs = dict()
    team_incs = dict()
    match_incs = dict()
    match_doc['day'] = datetime.datetime.fromtimestamp(m['gameCreation'] / 1000).strftime('%y:%m:%d')
    match_doc['region'] = ENDPOINTS_TO_REGIONS_MAP[m['platformId'].lower()]
    match_doc['queueId'] = m['queueId']
    match_doc['season'] = m['seasonId']

    for _participant_identity in m['participantIdentities']:
        if 'player' in _participant_identity and _participant_identity['player']['summonerId'] == summonerId:
            #Found the player we are gathering data for
            participant_identity = _participant_identity
            break #no need to keep looking
    if participant_identity is None:
        raise ValueError('Summoner %s not found in match %s from %s' % (summonerId, m['gameId'], ENDPOINTS_TO_REGIONS_MAP[m['platformId'].lower()]))

    for _participant in m['participants']:
        #We need to find the correct participant's team first
        if _participant['participantId'] == participant_identity['participantId']:
            participant = _participant
            break #no need to keep going

    if participant is None:
        raise ValueError('Participant %s not found in match %s from %s' % (participant_id, m['gameId'], ENDPOINTS_TO_REGIONS_MAP[m['platformId'].lower()]))

    for _participant in m['participants']:
        #now that we have the team, we loop through all of them again, aggregating
        if _participant['teamId'] == participant['teamId']:
            #teammate or same player, we aggregate to team stats
            pstats = _participant['stats']
            for stat in stats_to_aggregate:
                team_incs[stat + 'ByTeam'] = pstats.get(stat, 0) if team_incs.get(stat + 'ByTeam', None) is None else team_incs.get(stat + 'ByTeam') + pstats.get(stat, 0)

        if _participant['participantId'] == participant['participantId']:
            #lets add the aggregates specific to our guy
            pstats = _participant['stats']
            match_doc['championId'] = _participant['championId']
            for stat in stats_to_aggregate:
                match_incs[stat] = pstats.get(stat, 0) if match_incs.get(stat, None) is None else match_incs.get(stat) + pstats.get(stat, 0)
            match_incs['firstBloodKills'] = 1 if pstats.get('firstBloodKill', False) else 0
            match_incs['firstBloodAssists'] = 1 if pstats.get('firstBloodAssist', False) else 0
            match_incs['firstTowerKills'] = 1 if pstats.get('firstTowerKill', False) else 0
            match_incs['firstTowerAssists'] = 1 if pstats.get('firstTowerAssist', False) else 0
            match_incs['firstInhibitorKills'] = 1 if pstats.get('firstInhibitorKill', False) else 0

        #now add them to the match total, regardless of team
        for stat in stats_to_aggregate:
            pstats = _participant['stats']
            totals_incs[stat + 'InMatch'] = pstats.get(stat, 0) if totals_incs.get(stat + 'InMatch', None) is None else totals_incs.get(stat + 'InMatch') + pstats.get(stat, 0)

    match_doc['summonerId'] = participant_identity['player']['summonerId']
    match_doc['accountId'] = participant_identity['player']['currentAccountId']


    for team in m['teams']:
        if team['teamId'] == participant['teamId']:
            match_incs['count'] = 1 #track of how many matches for this combination we've seen so far
            match_incs['redSideMatches'] = 1 if team['teamId'] == 100 else 0
            match_incs['blueSideMatches'] = 1 if team['teamId'] == 200 else 0
            match_incs['wins'] = 1 if team['win'] == 'Win' else 0

    full_incs = dict(match_incs.items() | team_incs.items() | totals_incs.items())

    if mongoHelper is not None:
        mongoHelper.save_match_agg(match_doc, full_incs)
