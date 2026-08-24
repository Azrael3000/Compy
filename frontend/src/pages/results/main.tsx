import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@/index.css'
import './results.css'
import { ResultsApp } from './ResultsApp'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ResultsApp />
  </StrictMode>,
)
