/**
 * Clear All Databases Response
 * Returns summary of database clearing operation
 */
export interface ClearAllDatabasesResponse {
	success: boolean
	message: string
	cleared_services: string[]
	timestamp: string
}

/**
 * Export All Databases Response
 * Returns combined export data from all services
 */
export interface ExportAllDatabasesResponse {
	success: boolean
	message: string
	metadata: {
		timestamp: string
		version: string
	}
	databases: {
		core: any
		identity: any
		job: any
		resume: any
	}
}

/**
 * Import All Databases Request
 * Data structure for importing all databases
 */
export interface ImportAllDatabasesRequest {
	metadata: {
		timestamp: string
		version: string
	}
	databases: {
		core: any
		identity: any
		job: any
		resume: any
	}
}

/**
 * Import All Databases Response
 * Returns summary of import operation across all services
 */
export interface ImportAllDatabasesResponse {
	success: boolean
	message: string
	imported_services: string[]
	total_inserted: number
	total_updated: number
	total_skipped: number
	timestamp: string
}
