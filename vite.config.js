import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import edgeTtsPlugin from './vite-plugin-edge-tts';

export default defineConfig({
    plugins: [react(), edgeTtsPlugin()],
});
