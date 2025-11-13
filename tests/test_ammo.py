import pytest
from sqlmodel import Session
from models import Ammo
from services.ammo_service import AmmoService
from services.user_context import UserContext, UserRole
from schemas.ammo import AmmoCreate


@pytest.mark.asyncio
async def test_create_and_list_ammo_user(session: Session):
    user = UserContext(user_id="user-1", role=UserRole.user)
    ammo_data = AmmoCreate(name="FMJ 9mm", caliber="9mm", price_per_unit=0.5, units_in_package=100)

    created = await AmmoService.create_ammo(session, ammo_data, user)
    assert created.id is not None
    assert created.units_in_package == 100

    result = await AmmoService.get_all_ammo(session, user, limit=5, offset=0, search="fmj")
    assert result["total"] == 1
    assert result["items"][0].name == "FMJ 9mm"


@pytest.mark.asyncio
async def test_add_ammo_quantity_guest(session: Session):
    guest = UserContext(user_id="guest-1", role=UserRole.guest, is_guest=True)
    ammo_data = AmmoCreate(name="Guest Ammo", caliber="5.56", price_per_unit=1.2, units_in_package=50)

    created = await AmmoService.create_ammo(session, ammo_data, guest)
    updated = await AmmoService.add_ammo_quantity(session, created.id, 25, guest)

    assert updated.units_in_package == 75
    assert updated.expires_at is not None



