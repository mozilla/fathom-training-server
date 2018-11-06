import freezeDry from 'freeze-dry';

setTimeout(async () => {
  const html = await freezeDry(window.document, document.URL);
  marionetteScriptFinished({html});
}, 5000);
