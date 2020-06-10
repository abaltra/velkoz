exports.handler = async function(event, context) {
    if (event.Records.length > 1) {
        console.error(`Received ${event.Records.length} events in the record. What do?`)
        return context.done(`Received ${event.Records.length} events in the record. What do?`)
    }
    const record = event.Records[0]
    const message = JSON.parse(record.Sns.Message)
    console.log(`Getting game data for account ${message.accountId} in ${message.region}`)
    context.done()
  }