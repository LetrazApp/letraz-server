import {api} from 'encore.dev/api'
import {
	ClearAllDatabasesResponse,
	ExportAllDatabasesResponse,
	ImportAllDatabasesRequest,
	ImportAllDatabasesResponse
} from '@/services/admin/interface'
import {AdminService} from '@/services/admin/service'

/**
 * Clear all databases across all services
 *
 * This endpoint clears all database tables except:
 * - waitlist table (core service)
 * - countries table (core service)
 *
 * Admin endpoint - requires x-admin-api-key header for authentication.
 * Accessible at DELETE /admin/databases/clear
 *
 * WARNING: This is a destructive operation and cannot be undone
 */
export const clearAllDatabases = api({
	method: 'DELETE',
	path: '/admin/databases/clear',
	auth: true,
	expose: true
}, async (): Promise<ClearAllDatabasesResponse> => {
	return AdminService.clearAllDatabases()
})

/**
 * Export all databases across all services
 *
 * This endpoint exports data from all services:
 * - core (countries, waitlist, feedback)
 * - identity (users)
 * - job (processes, jobs)
 * - resume (all resume-related tables)
 *
 * Admin endpoint - requires x-admin-api-key header for authentication.
 * Accessible at GET /admin/databases/export
 *
 * Returns JSON file that can be downloaded and used for backup or migration
 */
export const exportAllDatabases = api({
	method: 'GET',
	path: '/admin/databases/export',
	auth: true,
	expose: true
}, async (): Promise<ExportAllDatabasesResponse> => {
	return AdminService.exportAllDatabases()
})

/**
 * Import all databases across all services
 *
 * This endpoint imports data to all services in dependency order:
 * core → identity → job → resume
 *
 * Uses UPSERT for idempotent imports (can be run multiple times safely)
 *
 * Admin endpoint - requires x-admin-api-key header for authentication.
 * Accessible at POST /admin/databases/import
 */
export const importAllDatabases = api({
	method: 'POST',
	path: '/admin/databases/import',
	auth: true,
	expose: true
}, async (params: ImportAllDatabasesRequest): Promise<ImportAllDatabasesResponse> => {
	return AdminService.importAllDatabases(params)
})
