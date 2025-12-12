"""update attachments add fields and update enum

Revision ID: update_attachments_add_fields
Revises: add_created_at_to_guns
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'update_attachments_add_fields'
down_revision: Union[str, None] = 'add_created_at_to_guns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Sprawdza czy kolumna istnieje w tabeli"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'
    
    # Dla PostgreSQL - zaktualizuj enum AttachmentType
    if is_postgres:
        conn = bind.connect()
        
        # Sprawdź czy enum istnieje
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'attachment_type_enum'
            );
        """))
        enum_exists = result.scalar()
        
        if enum_exists:
            # Zaktualizuj istniejące wartości w bazie danych
            # Mapowanie starych wartości na nowe (każda instrukcja osobno)
            op.execute(sa.text("UPDATE attachments SET type = 'red_dot' WHERE type = 'optic'"))
            op.execute(sa.text("UPDATE attachments SET type = 'tactical_light' WHERE type = 'light'"))
            op.execute(sa.text("UPDATE attachments SET type = 'tactical_light' WHERE type = 'laser'"))
            op.execute(sa.text("UPDATE attachments SET type = 'foregrip' WHERE type = 'grip'"))
            op.execute(sa.text("UPDATE attachments SET type = 'red_dot' WHERE type = 'trigger'"))
            op.execute(sa.text("UPDATE attachments SET type = 'red_dot' WHERE type = 'other'"))
            
            # Usuń stary enum i utwórz nowy
            op.execute(sa.text("ALTER TABLE attachments ALTER COLUMN type TYPE VARCHAR(50)"))
            op.execute(sa.text("DROP TYPE IF EXISTS attachment_type_enum"))
        
        # Utwórz nowy enum
        new_enum = postgresql.ENUM(
            'red_dot', 'reflex', 'lpvo', 'magnifier', 'suppressor',
            'compensator', 'foregrip', 'angled_grip', 'bipod', 'tactical_light',
            name='attachment_type_enum',
            create_type=True
        )
        new_enum.create(bind, checkfirst=True)
        
        # Zmień typ kolumny na nowy enum
        op.execute(sa.text("ALTER TABLE attachments ALTER COLUMN type TYPE attachment_type_enum USING type::attachment_type_enum"))
        
        conn.close()
    else:
        # SQLite - zaktualizuj wartości bezpośrednio (każda instrukcja osobno)
        op.execute(sa.text("UPDATE attachments SET type = 'red_dot' WHERE type = 'optic'"))
        op.execute(sa.text("UPDATE attachments SET type = 'tactical_light' WHERE type = 'light'"))
        op.execute(sa.text("UPDATE attachments SET type = 'tactical_light' WHERE type = 'laser'"))
        op.execute(sa.text("UPDATE attachments SET type = 'foregrip' WHERE type = 'grip'"))
        op.execute(sa.text("UPDATE attachments SET type = 'red_dot' WHERE type = 'trigger'"))
        op.execute(sa.text("UPDATE attachments SET type = 'red_dot' WHERE type = 'other'"))
    
    # Dodaj nowe kolumny
    if not _column_exists('attachments', 'precision_help'):
        op.add_column('attachments', sa.Column('precision_help', sa.String(length=20), nullable=True, server_default='none'))
    
    if not _column_exists('attachments', 'recoil_reduction'):
        op.add_column('attachments', sa.Column('recoil_reduction', sa.String(length=20), nullable=True, server_default='none'))
    
    if not _column_exists('attachments', 'ergonomics'):
        op.add_column('attachments', sa.Column('ergonomics', sa.String(length=20), nullable=True, server_default='none'))
    
    # Ustaw wartości domyślne dla istniejących rekordów (każda instrukcja osobno dla SQLite)
    op.execute(sa.text("UPDATE attachments SET precision_help = 'none' WHERE precision_help IS NULL"))
    op.execute(sa.text("UPDATE attachments SET recoil_reduction = 'none' WHERE recoil_reduction IS NULL"))
    op.execute(sa.text("UPDATE attachments SET ergonomics = 'none' WHERE ergonomics IS NULL"))
    
    # Dla PostgreSQL - zmień na NOT NULL
    if is_postgres:
        op.alter_column('attachments', 'precision_help', nullable=False, server_default='none')
        op.alter_column('attachments', 'recoil_reduction', nullable=False, server_default='none')
        op.alter_column('attachments', 'ergonomics', nullable=False, server_default='none')


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'
    
    # Usuń kolumny jeśli istnieją
    if _column_exists('attachments', 'precision_help'):
        op.drop_column('attachments', 'precision_help')
    
    if _column_exists('attachments', 'recoil_reduction'):
        op.drop_column('attachments', 'recoil_reduction')
    
    if _column_exists('attachments', 'ergonomics'):
        op.drop_column('attachments', 'ergonomics')
    
    # Dla PostgreSQL - przywróć stary enum
    if is_postgres:
        conn = bind.connect()
        
        # Sprawdź czy nowy enum istnieje
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'attachment_type_enum'
            );
        """))
        enum_exists = result.scalar()
        
        if enum_exists:
            # Zmień typ kolumny na VARCHAR
            op.execute(sa.text("ALTER TABLE attachments ALTER COLUMN type TYPE VARCHAR(50)"))
            op.execute(sa.text("DROP TYPE IF EXISTS attachment_type_enum"))
            
            # Utwórz stary enum
            old_enum = postgresql.ENUM(
                'optic', 'light', 'laser', 'suppressor', 'bipod',
                'compensator', 'grip', 'trigger', 'other',
                name='attachment_type_enum',
                create_type=True
            )
            old_enum.create(bind, checkfirst=True)
            
            # Zmień typ kolumny na stary enum
            op.execute(sa.text("ALTER TABLE attachments ALTER COLUMN type TYPE attachment_type_enum USING type::attachment_type_enum"))
        
        conn.close()

