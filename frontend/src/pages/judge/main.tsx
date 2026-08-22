import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@/index.css'
import './judge.css'
import { JudgeApp } from './JudgeApp'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <JudgeApp />
  </StrictMode>,
)
