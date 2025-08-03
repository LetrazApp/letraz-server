from django.core.management.base import BaseCommand
from django.conf import settings
from RESUME.models import Resume

# Only import algoliasearch if it's available
if getattr(settings, 'ALGOLIA_STATUS', 'DISABLED') == 'OPERATIONAL':
    try:
        import algoliasearch_django as algoliasearch
        from algoliasearch_django import raw_search
        ALGOLIA_AVAILABLE = True
    except ImportError:
        ALGOLIA_AVAILABLE = False
else:
    ALGOLIA_AVAILABLE = False


class Command(BaseCommand):
    help = 'Reindex all Resume objects in Algolia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-index',
            action='store_true',
            help='Clear the Algolia index before reindexing'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually updating Algolia'
        )

    def handle(self, *args, **options):
        if not ALGOLIA_AVAILABLE:
            self.stdout.write(
                self.style.ERROR('Algolia is not available. Check your ALGOLIA_APPLICATION_ID and ALGOLIA_API_KEY environment variables.')
            )
            return
            
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        clear_index = options['clear_index']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting Algolia reindex for Resume model...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made to Algolia')
            )
        
        # Get total count
        total_resumes = Resume.objects.count()
        self.stdout.write(f'Found {total_resumes} Resume objects to index')
        
        if total_resumes == 0:
            self.stdout.write(
                self.style.WARNING('No Resume objects found to index')
            )
            return
        
        try:
            if clear_index and not dry_run:
                self.stdout.write('Clearing existing Algolia index...')
                algoliasearch.clear_index(Resume)
                self.stdout.write(
                    self.style.SUCCESS('Index cleared successfully')
                )
            
            if not dry_run:
                # Reindex all objects
                algoliasearch.reindex_all(Resume)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully reindexed {total_resumes} Resume objects'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'DRY RUN: Would reindex {total_resumes} Resume objects'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during reindexing: {str(e)}')
            )
            raise e