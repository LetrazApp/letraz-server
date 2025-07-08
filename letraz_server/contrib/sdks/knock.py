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
    
    def _transform_user_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform user properties to match Knock's expected format.
        
        Args:
            properties: Dictionary of user properties
            
        Returns:
            Dict[str, Any]: Transformed properties for Knock
        """
        transformed = {}
        
        # Handle email
        if 'email' in properties:
            transformed['email'] = properties['email']
            
        # Handle name - combine first_name and last_name into name
        first_name = properties.get('first_name', '').strip()
        last_name = properties.get('last_name', '').strip()
        if first_name or last_name:
            transformed['name'] = f"{first_name} {last_name}".strip()
            
        # Handle phone_number
        if 'phone_number' in properties:
            transformed['phone_number'] = properties['phone_number']
            
        # Handle avatar
        if 'avatar' in properties:
            transformed['avatar'] = properties['avatar']
            
        # Handle timezone
        if 'timezone' in properties:
            transformed['timezone'] = properties['timezone']
            
        # Handle locale
        if 'locale' in properties:
            transformed['locale'] = properties['locale']
            
        # Handle created_at
        if 'created_at' in properties:
            transformed['created_at'] = properties['created_at']
        elif 'last_login' in properties:
            # Use last_login as created_at if available
            transformed['created_at'] = properties['last_login']
            
        # Add any other custom properties that don't conflict with reserved names
        # Note: Only add properties that Knock accepts as custom properties
        reserved_names = {'email', 'name', 'first_name', 'last_name', 'phone_number', 
                         'avatar', 'timezone', 'locale', 'created_at', 'last_login', 'source'}
        for key, value in properties.items():
            if key not in reserved_names:
                # Store additional properties as custom properties
                transformed[key] = value
                
        return transformed
        
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
            if not self.is_available():
                logger.warning("Knock SDK is not available - skipping customer creation")
                return False
                
            # Prepare user properties for Knock
            user_properties = {
                'email': user.email,
                'name': user.get_full_name() if user.get_full_name() else user.email,
            }
            
            # Add individual name fields if available
            if user.first_name:
                user_properties['first_name'] = user.first_name
            if user.last_name:
                user_properties['last_name'] = user.last_name
                
            # Add additional properties that might be useful for notifications
            user_properties.update({
                'created_at': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'source': 'clerk_signup'
            })
            
            # Remove None values
            user_properties = {k: v for k, v in user_properties.items() if v is not None}
            
            # Identify user in Knock
            success = self.identify_user(
                user_id=str(user.id),
                properties=user_properties
            )
            
            if success:
                logger.info(f"Successfully created/updated Knock customer for user {user.id}")
                return True
            else:
                logger.error(f"Failed to create/update Knock customer for user {user.id}")
                return False
                
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
            
    def is_available(self) -> bool:
        """
        Check if the Knock SDK is properly configured and available.
        
        Returns:
            bool: True if available, False otherwise
        """
        return self.client is not None and bool(self.api_key) 