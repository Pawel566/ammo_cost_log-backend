import pytest
from sqlmodel import Session
from services.session_service import SessionService
from services.user_context import UserContext, UserRole
from models import Gun, Ammo


@pytest.mark.asyncio
async def test_create_cost_session(session: Session):
    user = UserContext(user_id="user-1", role=UserRole.user)
    gun = Gun(name="Cost Gun", user_id=user.user_id)
    ammo = Ammo(name="Cost Ammo", price_per_unit=2.0, units_in_package=200, user_id=user.user_id)
    session.add(gun)
    session.add(ammo)
    session.commit()
    session.refresh(gun)
    session.refresh(ammo)

    result = await SessionService.create_cost_session(session, user, gun.id, ammo.id, None, 20)

    assert result["session"].cost == 40.0
    assert result["remaining_ammo"] == 180


@pytest.mark.asyncio
async def test_get_all_sessions_with_search(session: Session):
    user = UserContext(user_id="user-2", role=UserRole.user)
    gun = Gun(name="Session Gun", user_id=user.user_id)
    ammo = Ammo(name="Session Ammo", price_per_unit=1.0, units_in_package=100, user_id=user.user_id)
    session.add(gun)
    session.add(ammo)
    session.commit()
    session.refresh(gun)
    session.refresh(ammo)

    await SessionService.create_cost_session(session, user, gun.id, ammo.id, "2025-01-10", 10)
    await SessionService.create_accuracy_session(session, user, gun.id, ammo.id, "2025-01-11", 50, 10, 7, None)

    sessions = await SessionService.get_all_sessions(session, user, limit=10, offset=0, search="session")
    assert sessions["cost_sessions"]["total"] == 1
    assert sessions["accuracy_sessions"]["total"] == 1





