import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/* Save a fetched blob under a file name. There is no navigation API for
 * "download this response", so the usual hidden-anchor click it is. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  /* revoked on the next tick, not inline: the download has to be started
   * before the url is released or the click is a no-op in some browsers */
  window.setTimeout(() => window.URL.revokeObjectURL(url), 0)
}

/* The message of a rejected api call, for the error banners. */
export function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message !== '') {
    return error.message
  }
  return String(error)
}
