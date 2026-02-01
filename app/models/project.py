"""Project model for task organization."""
from sqlalchemy import Column, String, Text, JSON, Index, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import TenantModel, GUID


class Project(TenantModel):
    """Project model for organizing tasks."""
    
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=True)  # Hex color for UI
    icon = Column(String(50), nullable=True)  # Icon name/emoji
    
    # Owner
    owner_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Statistics
    task_count = Column(Integer, default=0, nullable=False)
    completed_task_count = Column(Integer, default=0, nullable=False)
    
    # Additional info
    project_metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    # owner = relationship("User")
    # tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_projects_tenant_name", "tenant_id", "name"),
        Index("idx_projects_owner", "owner_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"
