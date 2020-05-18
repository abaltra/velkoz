exports.handler = async (event, context) => {
    console.log(`Function ${context.functionName} called`);
    console.log(event);
};