/**
 * Format an ISO date string into a human-readable form.
 *
 * @param {string|Date} dateString - ISO date string or Date object.
 * @param {'long'|'short'|'datetime'} [format='long'] - Desired output format.
 * @returns {string} Formatted date string, or '—' when the input is invalid.
 */
export function formatDate(dateString, format = 'long') {
  if (!dateString) return '—'

  const date = typeof dateString === 'string' ? new Date(dateString) : dateString

  if (isNaN(date.getTime())) return '—'

  switch (format) {
    case 'short': {
      return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    }
    case 'datetime': {
      return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    }
    case 'long':
    default: {
      return date.toLocaleDateString('en-GB', {
        weekday: 'short',
        day: '2-digit',
        month: 'long',
        year: 'numeric',
      })
    }
  }
}

/**
 * Return a human-friendly relative time string (e.g. "2 hours ago").
 *
 * @param {string|Date} dateString - ISO date string or Date object.
 * @returns {string} Relative time description or '—' for invalid input.
 */
export function formatRelative(dateString) {
  if (!dateString) return '—'

  const date = typeof dateString === 'string' ? new Date(dateString) : dateString
  if (isNaN(date.getTime())) return '—'

  const now = new Date()
  const diffMs = now - date
  const diffSec = Math.floor(diffMs / 1000)
  const absSec = Math.abs(diffSec)

  // Less than a minute
  if (absSec < 60) {
    return 'just now'
  }

  const diffMin = Math.floor(absSec / 60)
  if (diffMin < 60) {
    return diffMin === 1 ? '1 minute ago' : `${diffMin} minutes ago`
  }

  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) {
    return diffHr === 1 ? '1 hour ago' : `${diffHr} hours ago`
  }

  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 7) {
    return diffDay === 1 ? 'yesterday' : `${diffDay} days ago`
  }

  const diffWeek = Math.floor(diffDay / 7)
  if (diffWeek < 4) {
    return diffWeek === 1 ? '1 week ago' : `${diffWeek} weeks ago`
  }

  const diffMonth = Math.floor(diffDay / 30)
  if (diffMonth < 12) {
    return diffMonth === 1 ? '1 month ago' : `${diffMonth} months ago`
  }

  const diffYear = Math.floor(diffDay / 365)
  return diffYear === 1 ? '1 year ago' : `${diffYear} years ago`
}
