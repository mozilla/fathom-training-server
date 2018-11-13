/* global addMessageListener sendAsyncMessage content global */
addMessageListener('checkRuleset', {
  receiveMessage(message) {
    sendAsyncMessage(
      'matchResult',
      global.ruleset.extractFacts(content.document, message.facts, message.coefficients),
    );
  },
});
