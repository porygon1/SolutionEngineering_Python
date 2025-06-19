/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_URL: string
  readonly VITE_API_VERSION: string
  readonly VITE_SPOTIFY_CLIENT_ID?: string
  readonly VITE_SPOTIFY_CLIENT_SECRET?: string
  readonly VITE_NODE_ENV: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
} 