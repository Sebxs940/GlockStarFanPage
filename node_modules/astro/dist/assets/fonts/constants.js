const LOCAL_PROVIDER_NAME = "local";
const DEFAULTS = {
  weights: ["400"],
  styles: ["normal", "italic"],
  subsets: ["cyrillic-ext", "cyrillic", "greek-ext", "greek", "vietnamese", "latin-ext", "latin"],
  // Technically serif is the browser default but most websites these days use sans-serif
  fallbacks: ["sans-serif"],
  optimizedFallbacks: true
};
const VIRTUAL_MODULE_ID = "virtual:astro:assets/fonts/internal";
const RESOLVED_VIRTUAL_MODULE_ID = "\0" + VIRTUAL_MODULE_ID;
const URL_PREFIX = "/_astro/fonts/";
const CACHE_DIR = "./fonts/";
const FONT_TYPES = ["woff2", "woff", "otf", "ttf", "eot"];
const FONT_FORMAT_MAP = {
  woff2: "woff2",
  woff: "woff",
  otf: "opentype",
  ttf: "truetype",
  eot: "embedded-opentype"
};
const GENERIC_FALLBACK_NAMES = [
  "serif",
  "sans-serif",
  "monospace",
  "cursive",
  "fantasy",
  "system-ui",
  "ui-serif",
  "ui-sans-serif",
  "ui-monospace",
  "ui-rounded",
  "emoji",
  "math",
  "fangsong"
];
const FONTS_TYPES_FILE = "fonts.d.ts";
export {
  CACHE_DIR,
  DEFAULTS,
  FONTS_TYPES_FILE,
  FONT_FORMAT_MAP,
  FONT_TYPES,
  GENERIC_FALLBACK_NAMES,
  LOCAL_PROVIDER_NAME,
  RESOLVED_VIRTUAL_MODULE_ID,
  URL_PREFIX,
  VIRTUAL_MODULE_ID
};
