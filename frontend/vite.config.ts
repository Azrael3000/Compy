import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'node:path'

// Every Flask path the frontend talks to. They share no common prefix,
// so each one is proxied to the backend in dev to stay same-origin.
const API_PREFIXES = [
  '/admin_data',
  '/results_data',
  '/clock_data',
  '/judge',
  '/judge_json',
  '/judges',
  '/athlete',
  '/athletes',
  '/competition',
  '/load_comp',
  '/start_list',
  '/start_list_pdf',
  '/breaks',
  '/lane_list',
  '/lane_list_pdf',
  '/result',
  '/result_pdf',
  '/results_list',
  '/block',
  '/publish_results',
  '/upload_file',
  '/upload_sponsor_img',
  '/store_results',
  '/change_special_ranking_name',
  '/change_registration',
  '/change_lane_style',
  '/change_comp_type',
  '/change_selected_country',
  '/national_records',
  '/aida',
  '/disciplines',
  '/static',
  '/admin/login',
  '/admin/logout',
]

// compy.py --port moves the backend; point the dev proxy at the same port so
// "a test instance next to the dev server" composes with `npm run dev`:
//   COMPY_BACKEND_PORT=5001 npm run dev:vite
const BACKEND_PORT = process.env.COMPY_BACKEND_PORT ?? '5000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/app/',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    rollupOptions: {
      input: {
        admin: resolve(__dirname, 'admin.html'),
        judge: resolve(__dirname, 'judge.html'),
        results: resolve(__dirname, 'results.html'),
        clock: resolve(__dirname, 'clock.html'),
      },
    },
  },
  server: {
    proxy: Object.fromEntries(
      API_PREFIXES.map((p) => [
        p,
        { target: `http://localhost:${BACKEND_PORT}`, changeOrigin: false },
      ]),
    ),
  },
})
