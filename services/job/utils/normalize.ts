export const clampString = (value: unknown, maxLen: number): string | null => {
	if (typeof value !== 'string') return null
	const s = value.trim()
	if (!s) return null
	if (s.length <= maxLen) return s
	return s.slice(0, maxLen)
}

/**
 * Normalize currency into something that fits `jobs.currency` (varchar(5)).
 * Prefer ISO 4217 codes (e.g. "USD"). Drops units like "/hour".
 */
export const normalizeCurrency = (value: unknown): string | null => {
	if (typeof value !== 'string') return null
	const raw = value.trim()
	if (!raw) return null

	/*
	 * Examples we want to handle:
	 * - "USD/hour" -> "USD"
	 * - "usd per hour" -> "USD"
	 * - "$" -> null (unknown)
	 */
	const isoMatch = raw.match(/[A-Za-z]{3}/)
	if (!isoMatch) return null

	const code = isoMatch[0]!.toUpperCase()
	return code.length <= 5 ? code : code.slice(0, 5)
}

/**
 * Normalize a salary to fit `bigint` columns stored as JS numbers.
 * - Accepts numbers or numeric strings
 * - Rounds to the nearest integer (since bigint can't store decimals)
 */
export const normalizeBigintNumber = (value: unknown): number | null => {
	if (value === null || value === undefined) return null

	const num =
		typeof value === 'number'
			? value
			: typeof value === 'string'
				? Number.parseFloat(value)
				: Number.NaN

	if (!Number.isFinite(num)) return null
	if (num < 0) return null

	const rounded = Math.round(num)
	if (!Number.isSafeInteger(rounded)) return null
	return rounded
}

export const normalizeStringArray = (value: unknown): string[] | null => {
	if (!Array.isArray(value)) return null
	const out: string[] = []
	for (const item of value) {
		if (typeof item !== 'string') continue
		const s = item.trim()
		if (!s) continue
		out.push(s)
	}
	return out.length ? out : []
}

