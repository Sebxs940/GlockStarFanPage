function normalizeRemoteFontFaces({
  fonts,
  urlProxy
}) {
  return fonts.filter((font) => typeof font.meta?.priority === "number" ? font.meta.priority === 0 : true).map((font) => {
    let index = 0;
    return {
      ...font,
      src: font.src.map((source) => {
        if ("name" in source) {
          return source;
        }
        const proxied = {
          ...source,
          originalURL: source.url,
          url: urlProxy.proxy({
            url: source.url,
            // We only collect the first URL to avoid preloading fallback sources (eg. we only
            // preload woff2 if woff is available)
            collectPreload: index === 0,
            data: {
              weight: font.weight,
              style: font.style
            },
            init: font.meta?.init ?? null
          })
        };
        index++;
        return proxied;
      })
    };
  });
}
export {
  normalizeRemoteFontFaces
};
