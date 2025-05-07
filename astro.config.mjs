// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node'; // Agregar el adaptador

// https://astro.build/config
export default defineConfig({
  integrations: [tailwind()],
  adapter: node({
    mode: 'standalone' // or 'middleware'
  }), // Configuración del adaptador
});
