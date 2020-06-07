const AWS = require('aws-sdk')
exports.handler = async function(event, context) {
    const sns = new AWS.SNS()
    for (let i = 0; i < event.Records.length; i++) 
    {
        const record = event.Records[i]
        const keys = record.dynamodb.OldImage
        if (record.eventName == "REMOVE") 
        { // entry TTL'd
            const updateRequestedMessage = {
                AccountId: keys.AccountId.S,
                Region: keys.Region.S
            }

            const message = {
                Message: JSON.stringify(updateRequestedMessage),
                TopicArn: process.env.USER_GAMELIST_UPDATE_REQUESTED_TOPIC
            }

            console.log(`Requesting gamelist update for account ${keys.AccountId.S} in ${keys.Region.S}`)
            await sns.publish(message).promise()
        } 
        else 
        {
            console.log(`Skipping event of type ${record.eventName}`)
        }
    }
    context.done()
  }