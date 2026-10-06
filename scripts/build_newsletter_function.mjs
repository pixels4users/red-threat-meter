import './compile_hosted_validator.mjs';
import { build } from 'vite';
await build({ configFile:false, publicDir:false, ssr:{noExternal:true,target:'webworker'}, build:{
  ssr:'hosting/newsletter-edge.mjs',outDir:'supabase/functions/rta-newsletter',emptyOutDir:true,
  target:'es2022',sourcemap:false,minify:true,rollupOptions:{output:{entryFileNames:'index.js'}}
}});
