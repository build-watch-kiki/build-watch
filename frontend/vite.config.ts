import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'
import type { PreviewServer, ProxyOptions, ViteDevServer } from 'vite'

import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget =
    process.env.BACKEND_URL || env.BACKEND_URL || 'http://localhost:8000'
  const s3Target =
    process.env.S3_PROXY_TARGET ||
    env.S3_PROXY_TARGET ||
    'http://localhost:9000'
  const s3SignedOrigin =
    process.env.S3_SIGNED_ORIGIN || env.S3_SIGNED_ORIGIN || s3Target
  const apiBaseUrl = process.env.API_BASE_URL || env.API_BASE_URL || '/api/'
  const allowedHosts = (
    process.env.FRONTEND_ALLOWED_HOSTS ||
    env.FRONTEND_ALLOWED_HOSTS ||
    ''
  )
    .split(',')
    .map((host) => host.trim())
    .filter(Boolean)
  const runtimeConfig = {
    apiBaseUrl,
    s3Origin: new URL(s3SignedOrigin).origin
  }
  const serveRuntimeConfig = (server: ViteDevServer | PreviewServer) => {
    server.middlewares.use('/runtime-config.js', (request, response, next) => {
      if (request.method !== 'GET') return next()
      response.setHeader(
        'Content-Type',
        'application/javascript; charset=utf-8'
      )
      response.setHeader('Cache-Control', 'no-store')
      response.end(
        `window.__BUILDWATCH_CONFIG__ = ${JSON.stringify(runtimeConfig)};`
      )
    })
  }
  const proxy: Record<string, ProxyOptions> = {
    '/api': {
      target: backendTarget,
      changeOrigin: true,
      rewrite: (path: string) => path.replace(/^\/api(?=\/|$)/, '') || '/'
    },
    '/s3': {
      target: s3Target,
      changeOrigin: true,
      rewrite: (path: string) => path.replace(/^\/s3(?=\/|$)/, '') || '/',
      configure: (server) => {
        server.on('proxyReq', (request) => {
          request.setHeader('Host', new URL(s3SignedOrigin).host)
        })
      }
    }
  }

  return {
    plugins: [
      vue(),
      vuetify(),
      {
        name: 'buildwatch-runtime-config',
        configureServer: serveRuntimeConfig,
        configurePreviewServer: serveRuntimeConfig
      }
    ],
    server: {
      host: '127.0.0.1',
      port: 5173,
      proxy
    },
    preview: {
      allowedHosts: ['yandex-vps.tail3763dd.ts.net', ...allowedHosts],
      proxy
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    }
  }
})
