import type * as unifont from 'unifont';
import type { UrlProxy } from '../definitions.js';
export declare function normalizeRemoteFontFaces({ fonts, urlProxy, }: {
    fonts: Array<unifont.FontFaceData>;
    urlProxy: UrlProxy;
}): Array<unifont.FontFaceData>;
