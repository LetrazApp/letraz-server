import {
	ClearAllDatabasesResponse,
	ExportAllDatabasesResponse,
	ImportAllDatabasesRequest,
	ImportAllDatabasesResponse
} from '@/services/admin/interface'
import log from 'encore.dev/log'
import {core, identity, job, resume} from '~encore/clients'

export const AdminService = {
	/**
	 * Clear all databases across all services
	 * Excludes waitlist and countries tables from core service
	 *
	 * This operation:
	 * 1. Calls clearDatabase on each service with a database
	 * 2. Aggregates results from all services
	 * 3. Returns summary of the operation
	 *
	 * WARNING: This is a destructive operation and cannot be undone
	 */
	clearAllDatabases: async (): Promise<ClearAllDatabasesResponse> => {
		log.info('Starting database clearing operation across all services')

		const clearedServices: string[] = []
		const timestamp = new Date().toISOString()

		try {
			// Clear core service database (except waitlist and countries)
			log.info('Clearing core service database...')
			await core.clearDatabase()
			clearedServices.push('core')

			// Clear identity service database
			log.info('Clearing identity service database...')
			await identity.clearDatabase()
			clearedServices.push('identity')

			// Clear job service database
			log.info('Clearing job service database...')
			await job.clearDatabase()
			clearedServices.push('job')

			// Clear resume service database
			log.info('Clearing resume service database...')
			await resume.clearDatabase()
			clearedServices.push('resume')

			log.info('Database clearing operation completed successfully', {
				cleared_services: clearedServices,
				timestamp
			})

			return {
				success: true,
				message: `Successfully cleared databases for ${clearedServices.length} services`,
				cleared_services: clearedServices,
				timestamp
			}
		} catch (error) {
			log.error(error as Error, 'Failed to clear databases', {
				cleared_services: clearedServices,
				timestamp
			})

			throw error
		}
	},

	/**
	 * Export all databases across all services
	 * Exports data from core, identity, job, and resume services
	 * Returns combined JSON with metadata
	 */
	exportAllDatabases: async (): Promise<ExportAllDatabasesResponse> => {
		log.info('Starting database export operation across all services')

		const timestamp = new Date().toISOString()

		try {
			// Export core service database
			log.info('Exporting core service database...')
			const coreExport = await core.exportDatabase()

			// Export identity service database
			log.info('Exporting identity service database...')
			const identityExport = await identity.exportDatabase()

			// Export job service database
			log.info('Exporting job service database...')
			const jobExport = await job.exportDatabase()

			// Export resume service database
			log.info('Exporting resume service database...')
			const resumeExport = await resume.exportDatabase()

			log.info('Database export operation completed successfully', {
				timestamp
			})

			return {
				success: true,
				message: 'Successfully exported all databases',
				metadata: {
					timestamp,
					version: '1.0'
				},
				databases: {
					core: coreExport.data,
					identity: identityExport.data,
					job: jobExport.data,
					resume: resumeExport.data
				}
			}
		} catch (error) {
			log.error(error as Error, 'Failed to export databases', {timestamp})
			throw error
		}
	},

	/**
	 * Import all databases across all services
	 * Imports data in dependency order: core → identity → job → resume
	 * Uses UPSERT for idempotent imports
	 */
	importAllDatabases: async (params: ImportAllDatabasesRequest): Promise<ImportAllDatabasesResponse> => {
		log.info('Starting database import operation across all services')

		const importedServices: string[] = []
		const timestamp = new Date().toISOString()
		let totalInserted = 0
		let totalUpdated = 0
		let totalSkipped = 0

		try {
			// Import core service database (no dependencies)
			log.info('Importing core service database...')
			const coreImport = await core.importDatabase({data: params.databases.core})
			importedServices.push('core')
			totalInserted += coreImport.inserted
			totalUpdated += coreImport.updated
			totalSkipped += coreImport.skipped

			// Import identity service database (depends on core for countries reference)
			log.info('Importing identity service database...')
			const identityImport = await identity.importDatabase({data: params.databases.identity})
			importedServices.push('identity')
			totalInserted += identityImport.inserted
			totalUpdated += identityImport.updated
			totalSkipped += identityImport.skipped

			// Import job service database (depends on core, can be parallel with identity)
			log.info('Importing job service database...')
			const jobImport = await job.importDatabase({data: params.databases.job})
			importedServices.push('job')
			totalInserted += jobImport.inserted
			totalUpdated += jobImport.updated
			totalSkipped += jobImport.skipped

			// Import resume service database (depends on identity for users, job for jobs)
			log.info('Importing resume service database...')
			const resumeImport = await resume.importDatabase({data: params.databases.resume})
			importedServices.push('resume')
			totalInserted += resumeImport.inserted
			totalUpdated += resumeImport.updated
			totalSkipped += resumeImport.skipped

			log.info('Database import operation completed successfully', {
				imported_services: importedServices,
				total_inserted: totalInserted,
				total_updated: totalUpdated,
				total_skipped: totalSkipped,
				timestamp
			})

			return {
				success: true,
				message: `Successfully imported databases for ${importedServices.length} services`,
				imported_services: importedServices,
				total_inserted: totalInserted,
				total_updated: totalUpdated,
				total_skipped: totalSkipped,
				timestamp
			}
		} catch (error) {
			log.error(error as Error, 'Failed to import databases', {
				imported_services: importedServices,
				timestamp
			})
			throw error
		}
	}
}

