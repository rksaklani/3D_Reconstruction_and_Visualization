import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'SplatRenderer',
      fileName: 'splat-renderer'
    },
    rollupOptions: {
      external: ['@babylonjs/core', '@babylonjs/loaders', '@babylonjs/materials', 'ammo.js'],
      output: {
        globals: {
          '@babylonjs/core': 'BABYLON',
          '@babylonjs/loaders': 'BABYLON',
          '@babylonjs/materials': 'BABYLON',
          'ammo.js': 'Ammo'
        }
      }
    }
  }
});
