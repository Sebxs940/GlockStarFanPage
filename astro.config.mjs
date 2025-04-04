// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import staticAdapter from '@astrojs/static';

// https://astro.build/config
export default defineConfig({
  integrations: [tailwind()],
  output: 'static',
  adapter: staticAdapter()
});
