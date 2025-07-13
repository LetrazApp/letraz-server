import logging
from rest_framework import serializers
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from CORE.models import Waitlist
from CORE.serializers import WaitlistSerializer, WaitlistUpdateSerializer, WaitlistBulkUpdateSerializer, ErrorSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.contrib.admin_auth import admin_api_key_required
from letraz_server.contrib.sdks.knock import KnockSDK
from letraz_server import settings
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


# Admin Waitlist Management
@extend_schema(
    methods=['GET'],
    tags=['Admin - Waitlist'],
    auth=[],
    responses={200: WaitlistSerializer(many=True), 401: ErrorSerializer, 500: ErrorSerializer},
    summary="[ADMIN] Get all waitlists",
    description="Returns all waitlist entries ordered by waiting number. Requires admin API key authentication.",
    parameters=[
        {
            'name': 'x-admin-api-key',
            'in': 'header',
            'required': True,
            'schema': {'type': 'string'},
            'description': 'Admin API key for authentication'
        }
    ]
)
@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_waitlist_list(request):
    """
    Admin endpoint to get all waitlist entries
    """
    try:
        waitlist_qs: QuerySet[Waitlist] = Waitlist.objects.all().order_by('waiting_number')
        return Response(WaitlistSerializer(waitlist_qs, many=True).data)
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INTERNAL_SERVER_ERROR, message=e.__str__())
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response


@extend_schema(
    methods=['POST'],
    tags=['Admin - Waitlist'],
    summary="[ADMIN] Update waitlist entry",
    description="Update a specific waitlist entry by ID. Currently supports updating the has_access field. Requires admin API key authentication.",
    request=WaitlistUpdateSerializer,
    responses={
        200: WaitlistSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        404: ErrorSerializer
    },
    parameters=[
        {
            'name': 'x-admin-api-key',
            'in': 'header',
            'required': True,
            'schema': {'type': 'string'},
            'description': 'Admin API key for authentication'
        }
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_waitlist_update(request, waitlist_id):
    """
    Admin endpoint to update a specific waitlist entry by ID
    """
    try:
        waitlist_entry = Waitlist.objects.get(id=waitlist_id)
    except Waitlist.DoesNotExist:
        return ErrorResponse(
            code=ErrorCode.NOT_FOUND, 
            message='Waitlist entry not found!',
            details={'waitlist_id': waitlist_id}
        ).response
    
    try:
        # Check if has_access is being updated from False to True
        old_has_access = waitlist_entry.has_access
        new_has_access = request.data.get('has_access')
        
        update_serializer = WaitlistUpdateSerializer(waitlist_entry, data=request.data, partial=True)
        if update_serializer.is_valid():
            updated_waitlist = update_serializer.save()
            
            # Trigger welcome-flow workflow if has_access changed from False to True
            if not old_has_access and new_has_access is True:
                try:
                    knock_sdk = KnockSDK(api_key=settings.KNOCK_API_KEY)
                    if knock_sdk.is_available():
                        # Use waitlist entry ID as the Knock user ID
                        workflow_data = {
                            'email': updated_waitlist.email,
                            'waiting_number': updated_waitlist.waiting_number,
                            'referrer': updated_waitlist.referrer
                        }
                        
                        success = knock_sdk.trigger_workflow(
                            workflow_key="welcome-flow",
                            user_id=str(updated_waitlist.id),
                            data=workflow_data
                        )
                        
                        if success:
                            logger.info(f"Successfully triggered welcome-flow workflow for waitlist entry {updated_waitlist.id}")
                        else:
                            logger.warning(f"Failed to trigger welcome-flow workflow for waitlist entry {updated_waitlist.id}")
                    else:
                        logger.warning("Knock SDK not available - skipping workflow trigger")
                        
                except Exception as knock_error:
                    # Log the error but don't fail the update
                    logger.error(f"Error triggering welcome-flow workflow for waitlist entry {updated_waitlist.id}: {str(knock_error)}")
            
            return Response(WaitlistSerializer(updated_waitlist).data)
        else:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST,
                message='Invalid data provided!',
                details=update_serializer.errors,
                extra={'data': request.data}
            ).response
    except Exception as e:
        error_response = ErrorResponse(
            code=ErrorCode.INVALID_REQUEST,
            message=e.__str__(),
            extra={'data': request.data}
        )
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response


@extend_schema(
    methods=['POST'],
    tags=['Admin - Waitlist'],
    summary="[ADMIN] Bulk update waitlist entries",
    description="Update multiple waitlist entries at once. Currently supports updating the has_access field for multiple users. Requires admin API key authentication.",
    request=WaitlistBulkUpdateSerializer,
    responses={
        200: WaitlistSerializer(many=True),
        400: ErrorSerializer,
        401: ErrorSerializer
    },
    parameters=[
        {
            'name': 'x-admin-api-key',
            'in': 'header',
            'required': True,
            'schema': {'type': 'string'},
            'description': 'Admin API key for authentication'
        }
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_waitlist_bulk_update(request):
    """
    Admin endpoint to bulk update waitlist entries
    """
    try:
        bulk_serializer = WaitlistBulkUpdateSerializer(data=request.data)
        if not bulk_serializer.is_valid():
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST,
                message='Invalid data provided!',
                details=bulk_serializer.errors,
                extra={'data': request.data}
            ).response
        
        validated_data = bulk_serializer.validated_data
        waitlist_ids = validated_data['waitlist_ids']
        has_access = validated_data['has_access']
        
        # Filter waitlist entries that exist
        waitlist_entries = Waitlist.objects.filter(id__in=waitlist_ids)
        found_ids = set(waitlist_entries.values_list('id', flat=True))
        missing_ids = set(waitlist_ids) - found_ids
        
        if missing_ids:
            return ErrorResponse(
                code=ErrorCode.NOT_FOUND,
                message='Some waitlist entries not found!',
                details={'missing_ids': list(missing_ids)}
            ).response
        
        # Get entries that will have has_access changed from False to True
        entries_to_trigger_workflow = []
        if has_access is True:
            entries_to_trigger_workflow = list(waitlist_entries.filter(has_access=False))
        
        # Update all entries
        updated_count = waitlist_entries.update(has_access=has_access)
        
        # Trigger welcome-flow workflow for entries that changed from False to True
        if entries_to_trigger_workflow:
            try:
                knock_sdk = KnockSDK(api_key=settings.KNOCK_API_KEY)
                if knock_sdk.is_available():
                    for entry in entries_to_trigger_workflow:
                        try:
                            workflow_data = {
                                'email': entry.email,
                                'waiting_number': entry.waiting_number,
                                'referrer': entry.referrer
                            }
                            
                            success = knock_sdk.trigger_workflow(
                                workflow_key="welcome-flow",
                                user_id=str(entry.id),
                                data=workflow_data
                            )
                            
                            if success:
                                logger.info(f"Successfully triggered welcome-flow workflow for waitlist entry {entry.id}")
                            else:
                                logger.warning(f"Failed to trigger welcome-flow workflow for waitlist entry {entry.id}")
                                
                        except Exception as knock_error:
                            # Log the error but don't fail the bulk update
                            logger.error(f"Error triggering welcome-flow workflow for waitlist entry {entry.id}: {str(knock_error)}")
                else:
                    logger.warning("Knock SDK not available - skipping workflow triggers")
                    
            except Exception as e:
                # Log the error but don't fail the bulk update
                logger.error(f"Error initializing Knock SDK for bulk workflow trigger: {str(e)}")
        
        # Return updated entries
        updated_entries = Waitlist.objects.filter(id__in=waitlist_ids)
        return Response({
            'updated_count': updated_count,
            'entries': WaitlistSerializer(updated_entries, many=True).data
        })
        
    except Exception as e:
        error_response = ErrorResponse(
            code=ErrorCode.INVALID_REQUEST,
            message=e.__str__(),
            extra={'data': request.data}
        )
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response 