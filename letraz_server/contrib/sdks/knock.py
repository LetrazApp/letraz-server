import logging
from typing import Optional, Dict, Any

from knockapi import Knock
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.{__name__}'
logger = logging.getLogger(__module_name)


class KnockSDK:
    def __init__(self, api_key: str):
        """
        Initialize the Knock SDK wrapper.
        
        Args:
            api_key: The Knock API key for authentication
        """
        self.api_key = api_key
        self.client = Knock(api_key=api_key) if api_key else None
        
    def identify_user(self, user_id: str, properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Identify a user in Knock with their properties.
        
        Args:
            user_id: The unique identifier for the user
            properties: Optional dictionary of user properties
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("Knock client not initialized - API key missing")
            return False
            
        if not user_id:
            logger.error("User ID is required for Knock identification")
            return False
            
        try:
            # Transform properties to match Knock's expected format
            knock_properties = self._transform_user_properties(properties or {})
            
            # Use the update method to create/update user in Knock (v1.0 SDK)
            self.client.users.update(
                user_id=user_id,
                **knock_properties
            )
            logger.info(f"Successfully identified user {user_id} in Knock")
            return True
            
        except Exception as e:
            logger.error(f"Failed to identify user {user_id} in Knock: {str(e)}")
            return False
    
    def _transform_user_properties(self, user_info: dict) -> dict:
        """
        Transform user properties from our format to Knock's expected format.
        
        Args:
            user_info: Dict containing user information
            
        Returns:
            Dict with properties formatted for Knock API
        """
        properties = {}
        
        # Combine first_name and last_name into 'name' for Knock
        first_name = user_info.get('first_name', '').strip()
        last_name = user_info.get('last_name', '').strip()
        
        if first_name or last_name:
            properties['name'] = f"{first_name} {last_name}".strip()
        
        # Add email if available
        if user_info.get('email_address'):
            properties['email'] = user_info['email_address']
        
        # Add avatar URL if available
        if user_info.get('avatar_url'):
            properties['avatar'] = user_info['avatar_url']
        
        # Add any other properties that Knock accepts
        # Note: We filter out properties that Knock doesn't accept
        
        return properties
        
    def create_customer_from_user_info(self, user_id: str, user_info: dict) -> bool:
        """
        Create a customer in Knock from user info dict.
        
        Args:
            user_id: User ID
            user_info: Dict containing user information including avatar_url
            
        Returns:
            bool: True if customer was created successfully, False otherwise
        """
        try:
            if not self.client:
                logger.debug("Knock client not initialized, skipping customer creation")
                return False
                
            properties = self._transform_user_properties(user_info)
            
            logger.debug(f"Creating Knock customer for user {user_id} with properties: {properties}")
            
            # Pass properties as individual keyword arguments
            response = self.client.users.update(
                user_id=user_id,
                **properties
            )
            
            logger.debug(f"Knock customer creation response: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Knock customer for user {user_id}: {e}")
            return False

    def ensure_customer_exists_with_info(self, user_id: str, user_info: dict) -> bool:
        """
        Ensure a customer exists in Knock with user info.
        
        Args:
            user_id: User ID
            user_info: Dict containing user information including avatar_url
            
        Returns:
            bool: True if customer exists or was created, False otherwise
        """
        try:
            if not self.client: # Changed from self.enabled to self.client
                logger.debug("Knock client not initialized, skipping customer check")
                return False
                
            # Check if user already exists in Knock
            try:
                response = self.client.users.get(user_id=user_id)
                logger.debug(f"User {user_id} already exists in Knock: {response}")
                return True
            except Exception as e:
                logger.debug(f"User {user_id} not found in Knock, creating: {e}")
                return self.create_customer_from_user_info(user_id, user_info)
                
        except Exception as e:
            logger.error(f"Failed to check/create Knock customer for user {user_id}: {e}")
            return False
        
    def create_customer_from_user(self, user) -> bool:
        """
        Create or update a customer in Knock from a Django User instance.
        
        Args:
            user: The Django User instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if Knock is available
            if not self.client: # Changed from self.is_available to self.client
                logger.warning("Knock SDK is not available - skipping customer creation")
                return False
                
            # Create properties dict for Knock
            properties = {
                'email': user.email,
            }
            
            # Add name if available
            if user.first_name or user.last_name:
                properties['name'] = f"{user.first_name or ''} {user.last_name or ''}".strip()
                
            logger.debug(f"Creating Knock customer for user {user.id} with properties: {properties}")
            
            # Pass properties as individual keyword arguments
            response = self.client.users.update(
                user_id=user.id,
                **properties
            )
            
            logger.debug(f"Knock customer creation response: {response}")
            return True
            
        except Exception as e:
            # Log the error but don't break the user creation flow
            logger.error(f"Unexpected error creating Knock customer for user {user.id}: {str(e)}")
            return False
    
    def re_identify_user(self, user, additional_properties=None) -> bool:
        """
        Re-identify an existing user in Knock with updated properties.
        This can be called when significant user events occur.
        
        Args:
            user: The Django User instance
            additional_properties: Optional dict of additional properties to include
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare base user properties
            user_properties = {
                'email': user.email,
                'name': user.get_full_name() if user.get_full_name() else user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'source': 'user_update'
            }
            
            # Add any additional properties
            if additional_properties:
                user_properties.update(additional_properties)
            
            # Remove None values
            user_properties = {k: v for k, v in user_properties.items() if v is not None}
            
            # Re-identify user in Knock
            success = self.identify_user(
                user_id=str(user.id),
                properties=user_properties
            )
            
            if success:
                logger.info(f"Successfully re-identified user {user.id} in Knock")
                return True
            else:
                logger.error(f"Failed to re-identify user {user.id} in Knock")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error re-identifying user {user.id} in Knock: {str(e)}")
            return False
    
    def ensure_customer_exists(self, user) -> bool:
        """
        Ensure a user exists as a customer in Knock.
        This method is idempotent and safe to call multiple times.
        
        Args:
            user: The Django User instance
            
        Returns:
            bool: True if user exists or was created successfully, False otherwise
        """
        try:
            if not self.client: # Changed from self.is_available to self.client
                logger.warning("Knock SDK is not available - skipping customer check")
                return False
            
            # Check if user exists in Knock first
            try:
                existing_user = self.client.users.get(user_id=str(user.id))
                if existing_user:
                    logger.debug(f"User {user.id} already exists in Knock")
                    return True
            except Exception as e:
                # User doesn't exist or other error, proceed to create
                logger.debug(f"User {user.id} not found in Knock, will create: {str(e)}")
            
            # Create the user in Knock
            return self.create_customer_from_user(user)
            
        except Exception as e:
            logger.error(f"Error ensuring Knock customer exists for user {user.id}: {str(e)}")
            return False
            
    def is_available(self) -> bool:
        """
        Check if the Knock SDK is properly configured and available.
        
        Returns:
            bool: True if available, False otherwise
        """
        return self.client is not None and bool(self.api_key) 