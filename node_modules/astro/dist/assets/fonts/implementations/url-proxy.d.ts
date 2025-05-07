import type { DataCollector, FontTypeExtractor, Hasher, UrlProxy, UrlProxyContentResolver } from '../definitions.js';
export declare function createUrlProxy({ base, contentResolver, hasher, dataCollector, fontTypeExtractor, }: {
    base: string;
    contentResolver: UrlProxyContentResolver;
    hasher: Hasher;
    dataCollector: DataCollector;
    fontTypeExtractor: FontTypeExtractor;
}): UrlProxy;
