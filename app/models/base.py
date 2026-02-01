"""Base models and mixins for all database models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
import sqlalchemy.types as types


# Custom UUID type that works with SQLite and PostgreSQL
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


# Declarative base
Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True
    )


class TenantMixin:
    """Mixin for tenant isolation.
    
    All models that need tenant isolation should inherit from this.
    Automatically adds tenant_id foreign key and index.
    """
    
    @declared_attr
    def tenant_id(cls):
        return Column(
            GUID,
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    def soft_delete(self):
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()
    
    @property
    def is_deleted(self):
        """Check if record is soft deleted."""
        return self.deleted_at is not None


class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""
    
    __abstract__ = True
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TenantModel(BaseModel, TenantMixin, SoftDeleteMixin):
    """Base model for tenant-isolated resources with soft delete."""
    
    __abstract__ = True
    
    @classmethod
    def query_by_tenant(cls, query, tenant_id: uuid.UUID):
        """Filter query by tenant and exclude soft-deleted records."""
        return query.filter(
            cls.tenant_id == tenant_id,
            cls.deleted_at.is_(None)
        )
