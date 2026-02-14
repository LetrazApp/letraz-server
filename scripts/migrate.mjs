import fs from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'

import dotenv from 'dotenv'
import pg from 'pg'
import {drizzle} from 'drizzle-orm/node-postgres'
import {migrate} from 'drizzle-orm/node-postgres/migrator'

const {Pool} = pg

// Load local env vars for CLI usage (does nothing if .env is missing).
// In production you typically provide env vars via the runtime, not a file.
dotenv.config({path: path.join(process.cwd(), '.env')})

const parseArgs = (argv) => {
	const out = {config: null}
	for (let i = 2; i < argv.length; i += 1) {
		const arg = argv[i]
		if (arg === '--config') {
			out.config = argv[i + 1] ?? null
			i += 1
		}
	}
	return out
}

const resolveEnvString = (value, label) => {
	if (typeof value === 'string') return value
	if (value && typeof value === 'object' && typeof value.$env === 'string') {
		const envName = value.$env
		const envVal = process.env[envName]
		if (!envVal) {
			throw new Error(`Missing required env var ${envName} for ${label}`)
		}
		return envVal
	}
	throw new Error(`Invalid value for ${label} (expected string or {$env})`)
}

const fileExists = async (p) => {
	try {
		await fs.access(p)
		return true
	} catch {
		return false
	}
}

const main = async () => {
	const args = parseArgs(process.argv)
	const configPath = args.config ?? process.env.INFRA_CONFIG_PATH ?? 'infra-config.json'

	const rootDir = process.cwd()
	const absConfigPath = path.isAbsolute(configPath) ? configPath : path.join(rootDir, configPath)
	const raw = await fs.readFile(absConfigPath, 'utf8')
	const infra = JSON.parse(raw)

	const sqlServers = infra?.sql_servers
	if (!Array.isArray(sqlServers) || sqlServers.length === 0) {
		throw new Error('infra-config.json missing sql_servers')
	}

	// For minimal footprint, we just run migrations for each configured database sequentially.
	for (const [serverIdx, server] of sqlServers.entries()) {
		const host = server?.host
		if (typeof host !== 'string' || !host) {
			throw new Error(`sql_servers[${serverIdx}].host must be a non-empty string`)
		}

		const tlsDisabled = server?.tls_config?.disabled === true
		const ssl = tlsDisabled ? undefined : {rejectUnauthorized: false}

		const dbs = server?.databases
		if (!dbs || typeof dbs !== 'object') {
			throw new Error(`sql_servers[${serverIdx}].databases must be an object`)
		}

		for (const [dbKey, dbCfg] of Object.entries(dbs)) {
			const dbNameOnServer = typeof dbCfg?.name === 'string' && dbCfg.name ? dbCfg.name : dbKey
			const username = resolveEnvString(dbCfg?.username, `sql_servers[${serverIdx}].databases.${dbKey}.username`)
			const password = resolveEnvString(dbCfg?.password, `sql_servers[${serverIdx}].databases.${dbKey}.password`)

			const migrationsFolder = path.join(rootDir, 'services', dbKey, 'migrations')
			const journalPath = path.join(migrationsFolder, 'meta', '_journal.json')
			if (!(await fileExists(journalPath))) {
				// Skip databases that don't have Drizzle migrations in services/<dbKey>/migrations
				// (useful if you later add more DBs that are managed differently).
				console.warn(`[migrate] skipping ${dbKey}: no migrations found at ${migrationsFolder}`)
				continue
			}

			// Neon typically requires TLS; we default to TLS unless explicitly disabled.
			const connectionString = `postgresql://${encodeURIComponent(username)}:${encodeURIComponent(password)}@${host}/${encodeURIComponent(dbNameOnServer)}`

			console.log(`[migrate] ${dbKey}: migrating ${host}/${dbNameOnServer} using ${migrationsFolder}`)

			const pool = new Pool({
				connectionString,
				ssl,
				max: 1,
				idleTimeoutMillis: 10_000,
			})

			try {
				const db = drizzle(pool)
				await migrate(db, {migrationsFolder})
				console.log(`[migrate] ${dbKey}: done`)
			} finally {
				await pool.end()
			}
		}
	}
}

main().catch((err) => {
	console.error('[migrate] failed:', err instanceof Error ? err.message : err)
	process.exitCode = 1
})

