/**
 * Common currency symbols keyed by ISO 4217 code.
 */
export const CURRENCY_SYMBOLS = {
  NGN: '₦',
  USD: '$',
  EUR: '€',
  GBP: '£',
  JPY: '¥',
  CNY: '¥',
  KRW: '₩',
  INR: '₹',
  BRL: 'R$',
  CAD: 'C$',
  AUD: 'A$',
  CHF: 'CHF',
  ZAR: 'R',
  KES: 'KSh',
  GHS: 'GH₵',
  TZS: 'TSh',
  UGX: 'USh',
  XOF: 'CFA',
  XAF: 'FCFA',
  EGP: 'E£',
  MAD: 'MAD',
  AED: 'د.إ',
  SAR: '﷼',
  TRY: '₺',
  RUB: '₽',
  PLN: 'zł',
  SEK: 'kr',
  NOK: 'kr',
  DKK: 'kr',
  CZK: 'Kč',
  HUF: 'Ft',
  RON: 'lei',
  BGN: 'лв',
  THB: '฿',
  VND: '₫',
  PHP: '₱',
  MYR: 'RM',
  IDR: 'Rp',
  PKR: '₨',
  BDT: '৳',
  MXN: 'MX$',
  ARS: 'AR$',
  COP: 'COL$',
  CLP: 'CLP$',
  PEN: 'S/',
  NZD: 'NZ$',
  SGD: 'S$',
  HKD: 'HK$',
  TWD: 'NT$',
  ILS: '₪',
}

/**
 * Format a numeric amount as currency.
 *
 * @param {number} amount          - The number to format.
 * @param {string} [symbolOrCode] - A currency symbol string (e.g. '$') or
 *                                  an ISO code (e.g. 'NGN').  Falls back to
 *                                  looking up CURRENCY_SYMBOLS, then to '$'.
 * @param {string} [locale='en']  - BCP-47 locale for Intl.NumberFormat.
 * @returns {string} The formatted currency string.
 */
export function formatCurrency(amount, symbolOrCode, locale = 'en') {
  const num = Number(amount)
  if (isNaN(num)) return '—'

  let symbol = symbolOrCode

  // If the caller passed an ISO code without an explicit symbol, look it up
  if (symbol && CURRENCY_SYMBOLS[symbol]) {
    symbol = CURRENCY_SYMBOLS[symbol]
  }

  if (!symbol) {
    symbol = '₦'
  }

  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: 'NGN',       // dummy currency – we override with symbol
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
      .format(num)
      .replace(/\₦/g, symbol)
  } catch {
    // Graceful fallback
    return `${symbol}${num.toFixed(2)}`
  }
}
