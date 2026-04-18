/**
 * Export an array of objects to a CSV file and trigger a browser download.
 *
 * @param {object[]}  data     - Array of row objects.
 * @param {string}    filename - Download filename (without extension).
 * @param {string[]}  columns  - Ordered list of object keys to include as columns.
 */
export function exportToCSV(data, filename, columns) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    console.warn('exportToCSV: no data to export')
    return
  }

  const header = columns.join(',')
  const rows = data.map((row) =>
    columns
      .map((col) => {
        let value = row[col]
        if (value === null || value === undefined) value = ''
        // Escape quotes and wrap in double-quotes if the value contains commas/newlines/quotes
        const str = String(value)
        if (str.includes(',') || str.includes('\n') || str.includes('"')) {
          return `"${str.replace(/"/g, '""')}"`
        }
        return str
      })
      .join(',')
  )

  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  downloadBlob(blob, `${filename}.csv`)
}

/**
 * Trigger a browser download for a Blob.
 *
 * @param {Blob}   blob     - The file Blob to download.
 * @param {string} filename - Desired download filename.
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  // Revoke after a short delay so the browser can initiate the download
  setTimeout(() => URL.revokeObjectURL(url), 250)
}
