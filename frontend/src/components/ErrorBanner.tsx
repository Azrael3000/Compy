/*
 * Shared failure banner.
 *
 * The jquery app swallowed most request errors; on the admin screen that is
 * merely confusing, on the judge phone it means a tapped "Save" can do
 * nothing at all without saying so. Every user-initiated request now reports
 * its failure here. Styling lives with the palette in index.css so all four
 * screens look the same; the judge page scales the font in judge.css.
 */
export function ErrorBanner({
  message,
  onDismiss,
}: {
  message: string | null
  onDismiss: () => void
}) {
  if (message === null) {
    return null
  }
  return (
    <div className="error_banner" role="alert" id="error_banner">
      <span className="error_banner_msg">{message}</span>
      <button type="button" className="error_banner_close" aria-label="Dismiss" onClick={onDismiss}>
        ×
      </button>
    </div>
  )
}
