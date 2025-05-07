function createUrlProxy({
  base,
  contentResolver,
  hasher,
  dataCollector,
  fontTypeExtractor
}) {
  return {
    proxy({ url: originalUrl, data, collectPreload, init }) {
      const type = fontTypeExtractor.extract(originalUrl);
      const hash = `${hasher.hashString(contentResolver.resolve(originalUrl))}.${type}`;
      const url = base + hash;
      dataCollector.collect({
        url: originalUrl,
        hash,
        preload: collectPreload ? { url, type } : null,
        data,
        init
      });
      return url;
    }
  };
}
export {
  createUrlProxy
};
