import pytest
from sqlmodel import Session
from models import Gun
from services.gun_service import GunService
from services.user_context import UserContext, UserRole
from schemas.gun import GunCreate


@pytest.mark.asyncio
async def test_create_and_list_guns_user(session: Session):
    user = UserContext(user_id="user-1", role=UserRole.user)
    gun_data = GunCreate(name="Test Gun", caliber="9mm", type="Pistol", notes=None)

    created = await GunService.create_gun(session, gun_data, user)
    assert created.id is not None
    assert created.user_id == "user-1"

    result = await GunService.get_all_guns(session, user, limit=10, offset=0, search=None)
    assert result["total"] == 1
    assert result["items"][0].name == "Test Gun"


@pytest.mark.asyncio
async def test_guest_gun_expires(session: Session):
    guest = UserContext(user_id="guest-1", role=UserRole.guest, is_guest=True)
    gun_data = GunCreate(name="Guest Gun", caliber="5.56", type="Rifle")

    created = await GunService.create_gun(session, gun_data, guest)
    assert created.expires_at is not None

    result = await GunService.get_all_guns(session, guest, limit=10, offset=0, search="guest")
    assert result["total"] == 1



