from flask import Flask
from flask import request
from pymongo import MongoClient
from bson import json_util
from flask import jsonify

app = Flask(__name__)
db = MongoClient('mongodb://localhost:27017')['loldata']

@app.route('/')
def index():
    qstring = request.args
    q = {}
    aggsteps = []
    matchstep = { '$match': {} }
    stats_to_aggregate = ['kills', 'deaths', 'assists', 'totalDamageDealt', 'magicDamageDealt', 'physicalDamageDealt', 'trueDamageDealt', 'totalDamageDealtToChampions', 'magicDamageDealtToChampions', 'physicalDamageDealtToChampions', 'trueDamageDealtToChampions', 'timeCCingOthers', 'totalDamageTaken', 'magicalDamageTaken', 'physicalDamageTaken', 'trueDamageTaken', 'totalHeal', 'totalUnitsHealed', 'damageSelfMitigated', 'damageDealtToObjectives', 'damageDealtToTurrets', 'goldEarned', 'goldSpent', 'turretKills', 'inhibitorKills', 'totalMinionsKilled', 'neutralMinionsKilled', 'neutralMinionsKilledTeamJungle', 'neutralMinionsKilledEnemyJungle', 'totalTimeCrowdControlDealt', 'visionWardsBoughtInGame', 'sightWardsBoughtInGame', 'wardsPlaced', 'wardsKilled']

    if qstring.get('champion', None) is not None:
        matchstep['$match']['championId'] = int(qstring.get('champion'))
    if qstring.get('role', None) is not None:
        matchstep['$match']['role'] = qstring.get('role')
    if qstring.get('lane', None) is not None:
        matchstep['$match']['lane'] = qstring.get('lane')

    groupstep = { '$group': { '_id': { 'championId': '$championId' } } }

    for stat in stats_to_aggregate:
        groupstep['$group'][stat] = { '$sum': '$%s' % stat }
        groupstep['$group']['%sByTeam' % stat] = { '$sum': '$%sByTeam' % stat }
        groupstep['$group']['%sInMatch' % stat] = { '$sum': '$%sInMatch' % stat }

    aggsteps.append(matchstep)
    aggsteps.append(groupstep)
    ret = []
    for dpoint in db['match_aggregates'].aggregate(aggsteps):
        #dpoint.pop('_id', None)
        ret.append(dpoint)

    return jsonify(ret)

if __name__ == '__main__':
    app.run(debug=True, port=3000)
