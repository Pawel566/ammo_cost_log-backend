import pytest
from sqlmodel import Session
from services.shooting_sessions_service import ShootingSessionsService
from services.user_context import UserContext, UserRole
from models import Gun, Ammo, ShootingSession
from schemas.shooting_sessions import ShootingSessionCreate, ShootingSessionUpdate


@pytest.mark.asyncio
async def test_create_shooting_session(session: Session):
    user = UserContext(user_id="user-1", role=UserRole.user)
    gun = Gun(name="Test Gun", caliber="9mm", user_id=user.user_id)
    ammo = Ammo(name="Test Ammo", price_per_unit=2.0, units_in_package=200, caliber="9mm", user_id=user.user_id)
    session.add(gun)
    session.add(ammo)
    session.commit()
    session.refresh(gun)
    session.refresh(ammo)

    session_data = ShootingSessionCreate(
        gun_id=gun.id,
        ammo_id=ammo.id,
        date="2025-01-15",
        shots=20,
        cost=None,
        notes="Test session"
    )

    result = await ShootingSessionsService.create_shooting_session(session, user, session_data)

    assert result["session"].cost == 40.0
    assert result["remaining_ammo"] == 180
    assert result["session"].shots == 20


@pytest.mark.asyncio
async def test_create_shooting_session_with_accuracy(session: Session):
    user = UserContext(user_id="user-2", role=UserRole.user)
    gun = Gun(name="Accuracy Gun", caliber="5.56", user_id=user.user_id)
    ammo = Ammo(name="Accuracy Ammo", price_per_unit=1.0, units_in_package=100, caliber="5.56", user_id=user.user_id)
    session.add(gun)
    session.add(ammo)
    session.commit()
    session.refresh(gun)
    session.refresh(ammo)

    session_data = ShootingSessionCreate(
        gun_id=gun.id,
        ammo_id=ammo.id,
        date="2025-01-16",
        shots=10,
        distance_m=25.0,
        hits=7
    )

    result = await ShootingSessionsService.create_shooting_session(session, user, session_data)

    assert result["session"].accuracy_percent == 70.0
    assert result["session"].hits == 7
    assert result["session"].distance_m == 25.0


@pytest.mark.asyncio
async def test_update_shooting_session(session: Session):
    user = UserContext(user_id="user-3", role=UserRole.user)
    gun = Gun(name="Update Gun", caliber="9mm", user_id=user.user_id)
    ammo = Ammo(name="Update Ammo", price_per_unit=2.0, units_in_package=200, caliber="9mm", user_id=user.user_id)
    session.add(gun)
    session.add(ammo)
    session.commit()
    session.refresh(gun)
    session.refresh(ammo)

    session_data = ShootingSessionCreate(
        gun_id=gun.id,
        ammo_id=ammo.id,
        shots=10
    )
    created = await ShootingSessionsService.create_shooting_session(session, user, session_data)
    session_id = created["session"].id

    update_data = ShootingSessionUpdate(shots=15, hits=12, distance_m=25.0)
    result = await ShootingSessionsService.update_shooting_session(session, session_id, user, update_data)

    assert result["session"].shots == 15
    assert result["session"].hits == 12
    assert result["session"].accuracy_percent == 80.0
    assert result["remaining_ammo"] == 185


@pytest.mark.asyncio
async def test_delete_shooting_session(session: Session):
    user = UserContext(user_id="user-4", role=UserRole.user)
    gun = Gun(name="Delete Gun", caliber="9mm", user_id=user.user_id)
    ammo = Ammo(name="Delete Ammo", price_per_unit=2.0, units_in_package=200, caliber="9mm", user_id=user.user_id)
    session.add(gun)
    session.add(ammo)
    session.commit()
    session.refresh(gun)
    session.refresh(ammo)

    initial_ammo = ammo.units_in_package

    session_data = ShootingSessionCreate(
        gun_id=gun.id,
        ammo_id=ammo.id,
        shots=30
    )
    created = await ShootingSessionsService.create_shooting_session(session, user, session_data)
    session_id = created["session"].id

    session.refresh(ammo)
    assert ammo.units_in_package == initial_ammo - 30

    result = await ShootingSessionsService.delete_shooting_session(session, session_id, user)
    assert result["message"] == "Session deleted"

    session.refresh(ammo)
    assert ammo.units_in_package == initial_ammo


@pytest.mark.asyncio
async def test_get_all_sessions(session: Session):
    user = UserContext(user_id="user-5", role=UserRole.user)
    gun = Gun(name="List Gun", caliber="9mm", user_id=user.user_id)
    ammo = Ammo(name="List Ammo", price_per_unit=1.0, units_in_package=100, caliber="9mm", user_id=user.user_id)
    session.add(gun)
    session.add(ammo)
    session.commit()
    session.refresh(gun)
    session.refresh(ammo)

    for i in range(3):
        session_data = ShootingSessionCreate(
            gun_id=gun.id,
            ammo_id=ammo.id,
            shots=10
        )
        await ShootingSessionsService.create_shooting_session(session, user, session_data)

    result = await ShootingSessionsService.get_all_sessions(session, user, limit=10, offset=0, search=None)
    assert result["total"] == 3
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_get_monthly_summary(session: Session):
    user = UserContext(user_id="user-6", role=UserRole.user)
    gun = Gun(name="Summary Gun", caliber="9mm", user_id=user.user_id)
    ammo = Ammo(name="Summary Ammo", price_per_unit=2.0, units_in_package=200, caliber="9mm", user_id=user.user_id)
    session.add(gun)
    session.add(ammo)
    session.commit()
    session.refresh(gun)
    session.refresh(ammo)

    session_data1 = ShootingSessionCreate(
        gun_id=gun.id,
        ammo_id=ammo.id,
        date="2025-01-15",
        shots=10
    )
    session_data2 = ShootingSessionCreate(
        gun_id=gun.id,
        ammo_id=ammo.id,
        date="2025-01-20",
        shots=15
    )
    await ShootingSessionsService.create_shooting_session(session, user, session_data1)
    await ShootingSessionsService.create_shooting_session(session, user, session_data2)

    result = await ShootingSessionsService.get_monthly_summary(session, user, limit=12, offset=0, search=None)
    assert result["total"] == 1
    assert result["items"][0]["month"] == "2025-01"
    assert result["items"][0]["total_shots"] == 25
    assert result["items"][0]["total_cost"] == 50.0









