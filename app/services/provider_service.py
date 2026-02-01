"""Provider service for managing AI provider configurations.

Handles:
- CRUD operations for providers
- Credential encryption/decryption
- Provider validation
- Default provider management
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models.provider import Provider, Model, ProviderType
from app.models.tenant import Tenant
from app.core.encryption import encrypt_credentials, decrypt_credentials
from app.services.providers.factory import ProviderFactory, create_provider
from app.services.providers.adapter import ProviderConfig, ProviderError

logger = logging.getLogger(__name__)


class ProviderService:
    """Service for managing AI providers."""
    
    def __init__(self, db: AsyncSession):
        """Initialize provider service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_provider(
        self,
        tenant_id: UUID,
        name: str,
        provider_type: ProviderType,
        credentials: dict,
        base_url: Optional[str] = None,
        is_default: bool = False,
        is_active: bool = True,
    ) -> Provider:
        """Create a new provider configuration.
        
        Args:
            tenant_id: Tenant ID
            name: Provider name
            provider_type: Provider type
            credentials: Provider credentials (will be encrypted)
            base_url: Optional base URL
            is_default: Set as default provider
            is_active: Provider is active
            
        Returns:
            Created Provider
            
        Raises:
            ValueError: If provider type is not supported
            ProviderError: If credentials are invalid
        """
        # Validate provider type
        if not ProviderFactory.is_supported(provider_type.value):
            raise ValueError(f"Unsupported provider type: {provider_type.value}")
        
        # Validate credentials by testing connection
        try:
            config = ProviderConfig(
                provider_type=provider_type.value,
                api_key=credentials.get("api_key", ""),
                base_url=base_url,
                organization=credentials.get("organization"),
                api_version=credentials.get("api_version"),
            )
            
            adapter = create_provider(provider_type.value, config)
            is_valid = await adapter.validate_credentials()
            
            if not is_valid:
                raise ProviderError(
                    message="Invalid credentials",
                    provider=provider_type.value,
                    error_type="authentication"
                )
        except Exception as e:
            logger.error(f"Provider validation failed: {e}")
            raise
        
        # Encrypt credentials
        encrypted = encrypt_credentials(credentials)
        
        # If setting as default, unset other defaults
        if is_default:
            await self._unset_default_providers(tenant_id)
        
        # Create provider
        provider = Provider(
            tenant_id=tenant_id,
            name=name,
            type=provider_type,
            credentials_encrypted=encrypted,
            base_url=base_url,
            is_default=is_default,
            is_active=is_active,
        )
        
        self.db.add(provider)
        await self.db.commit()
        await self.db.refresh(provider)
        
        logger.info(f"Created provider {name} ({provider_type.value}) for tenant {tenant_id}")
        return provider
    
    async def get_provider(
        self,
        provider_id: UUID,
        tenant_id: UUID
    ) -> Optional[Provider]:
        """Get provider by ID.
        
        Args:
            provider_id: Provider ID
            tenant_id: Tenant ID
            
        Returns:
            Provider or None
        """
        result = await self.db.execute(
            select(Provider).where(
                and_(
                    Provider.id == provider_id,
                    Provider.tenant_id == tenant_id,
                    Provider.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_provider_with_credentials(
        self,
        provider_id: UUID,
        tenant_id: UUID
    ) -> Optional[tuple[Provider, dict]]:
        """Get provider with decrypted credentials.
        
        Args:
            provider_id: Provider ID
            tenant_id: Tenant ID
            
        Returns:
            Tuple of (Provider, credentials_dict) or None
        """
        provider = await self.get_provider(provider_id, tenant_id)
        if not provider:
            return None
        
        credentials = decrypt_credentials(provider.credentials_encrypted)
        return provider, credentials
    
    async def list_providers(
        self,
        tenant_id: UUID,
        provider_type: Optional[ProviderType] = None,
        is_active: Optional[bool] = None
    ) -> List[Provider]:
        """List providers for tenant.
        
        Args:
            tenant_id: Tenant ID
            provider_type: Filter by provider type
            is_active: Filter by active status
            
        Returns:
            List of providers
        """
        conditions = [
            Provider.tenant_id == tenant_id,
            Provider.deleted_at.is_(None)
        ]
        
        if provider_type:
            conditions.append(Provider.type == provider_type)
        if is_active is not None:
            conditions.append(Provider.is_active == is_active)
        
        result = await self.db.execute(
            select(Provider).where(and_(*conditions))
        )
        return list(result.scalars().all())
    
    async def get_default_provider(
        self,
        tenant_id: UUID,
        provider_type: Optional[ProviderType] = None
    ) -> Optional[Provider]:
        """Get default provider for tenant.
        
        Args:
            tenant_id: Tenant ID
            provider_type: Optional provider type filter
            
        Returns:
            Default provider or None
        """
        conditions = [
            Provider.tenant_id == tenant_id,
            Provider.is_default == True,
            Provider.is_active == True,
            Provider.deleted_at.is_(None)
        ]
        
        if provider_type:
            conditions.append(Provider.type == provider_type)
        
        result = await self.db.execute(
            select(Provider).where(and_(*conditions))
        )
        return result.scalar_one_or_none()
    
    async def update_provider(
        self,
        provider_id: UUID,
        tenant_id: UUID,
        name: Optional[str] = None,
        credentials: Optional[dict] = None,
        base_url: Optional[str] = None,
        is_default: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Provider]:
        """Update provider configuration.
        
        Args:
            provider_id: Provider ID
            tenant_id: Tenant ID
            name: New name
            credentials: New credentials (will be encrypted)
            base_url: New base URL
            is_default: Set as default
            is_active: Active status
            
        Returns:
            Updated Provider or None
        """
        provider = await self.get_provider(provider_id, tenant_id)
        if not provider:
            return None
        
        # Update fields
        if name is not None:
            provider.name = name
        if base_url is not None:
            provider.base_url = base_url
        if is_active is not None:
            provider.is_active = is_active
        
        # Update credentials if provided
        if credentials is not None:
            # Validate new credentials
            try:
                config = ProviderConfig(
                    provider_type=provider.type.value,
                    api_key=credentials.get("api_key", ""),
                    base_url=base_url or provider.base_url,
                    organization=credentials.get("organization"),
                    api_version=credentials.get("api_version"),
                )
                
                adapter = create_provider(provider.type.value, config)
                is_valid = await adapter.validate_credentials()
                
                if not is_valid:
                    raise ProviderError(
                        message="Invalid credentials",
                        provider=provider.type.value,
                        error_type="authentication"
                    )
                
                # Encrypt and store
                provider.credentials_encrypted = encrypt_credentials(credentials)
            except Exception as e:
                logger.error(f"Credential validation failed: {e}")
                raise
        
        # Handle default provider
        if is_default is not None and is_default:
            await self._unset_default_providers(tenant_id)
            provider.is_default = True
        
        await self.db.commit()
        await self.db.refresh(provider)
        
        logger.info(f"Updated provider {provider_id}")
        return provider
    
    async def delete_provider(
        self,
        provider_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """Soft delete provider.
        
        Args:
            provider_id: Provider ID
            tenant_id: Tenant ID
            
        Returns:
            True if deleted, False if not found
        """
        provider = await self.get_provider(provider_id, tenant_id)
        if not provider:
            return False
        
        provider.soft_delete()
        await self.db.commit()
        
        logger.info(f"Deleted provider {provider_id}")
        return True
    
    async def create_adapter(
        self,
        provider_id: UUID,
        tenant_id: UUID
    ) -> Optional[tuple[Provider, any]]:
        """Create provider adapter with decrypted credentials.
        
        Args:
            provider_id: Provider ID
            tenant_id: Tenant ID
            
        Returns:
            Tuple of (Provider, ProviderAdapter) or None
        """
        result = await self.get_provider_with_credentials(provider_id, tenant_id)
        if not result:
            return None
        
        provider, credentials = result
        
        # Create config
        config = ProviderConfig(
            provider_type=provider.type.value,
            api_key=credentials.get("api_key", ""),
            base_url=provider.base_url,
            organization=credentials.get("organization"),
            api_version=credentials.get("api_version"),
        )
        
        # Create adapter
        adapter = create_provider(provider.type.value, config)
        
        return provider, adapter
    
    async def _unset_default_providers(self, tenant_id: UUID):
        """Unset all default providers for tenant.
        
        Args:
            tenant_id: Tenant ID
        """
        result = await self.db.execute(
            select(Provider).where(
                and_(
                    Provider.tenant_id == tenant_id,
                    Provider.is_default == True,
                    Provider.deleted_at.is_(None)
                )
            )
        )
        providers = result.scalars().all()
        
        for provider in providers:
            provider.is_default = False
        
        if providers:
            await self.db.commit()
