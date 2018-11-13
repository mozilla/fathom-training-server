import freezeDry from 'freeze-dry';

const marionetteScriptFinished = marionetteArguments[0];
setTimeout(async () => {
  const html = await freezeDry(window.document, document.URL);
  marionetteScriptFinished({html});
}, 5000);
