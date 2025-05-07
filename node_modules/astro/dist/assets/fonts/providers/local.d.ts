import type * as unifont from 'unifont';
import type { FontTypeExtractor, UrlProxy } from '../definitions.js';
import type { ResolvedLocalFontFamily } from '../types.js';
interface Options {
    family: ResolvedLocalFontFamily;
    urlProxy: UrlProxy;
    fontTypeExtractor: FontTypeExtractor;
}
export declare function resolveLocalFont({ family, urlProxy, fontTypeExtractor }: Options): {
    fonts: Array<unifont.FontFaceData>;
};
export {};
