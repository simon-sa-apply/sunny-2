"""add_cache_unique_constraint

Revision ID: 4a5b6c7d8e9f
Revises: 3e3f1266ac84
Create Date: 2025-12-29 21:00:00.000000+00:00

Adds unique constraint on (latitude, longitude) for CacheRepository
ON CONFLICT upsert operations.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4a5b6c7d8e9f"
down_revision: Union[str, None] = "3e3f1266ac84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on latitude, longitude."""
    # Drop existing non-unique index
    op.drop_index("ix_cached_locations_lat_lon", table_name="cached_locations")
    
    # Create unique constraint
    op.create_unique_constraint(
        "uq_cached_locations_lat_lon",
        "cached_locations",
        ["latitude", "longitude"],
    )
    
    # Recreate index (now implicitly unique via constraint)
    op.create_index(
        "ix_cached_locations_lat_lon",
        "cached_locations",
        ["latitude", "longitude"],
        unique=True,
    )


def downgrade() -> None:
    """Remove unique constraint."""
    op.drop_constraint(
        "uq_cached_locations_lat_lon", 
        "cached_locations", 
        type_="unique"
    )
    
    # Recreate non-unique index
    op.drop_index("ix_cached_locations_lat_lon", table_name="cached_locations")
    op.create_index(
        "ix_cached_locations_lat_lon",
        "cached_locations",
        ["latitude", "longitude"],
        unique=False,
    )

