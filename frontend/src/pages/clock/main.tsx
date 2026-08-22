import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@/index.css'
import './clock.css'
import { ClockApp } from './ClockApp'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ClockApp />
  </StrictMode>,
)
