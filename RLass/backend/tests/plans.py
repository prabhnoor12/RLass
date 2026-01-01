import pytest
from backend.services import plan_service
from backend.crud import plan as crud_plan
from backend.schemas.plan import PlanCreate
from backend.models.plan import Plan


def test_create_plan_with_check(db_session):
    plan_in = PlanCreate(name="Basic", description="Basic plan", rate_limit=100)
    plan = plan_service.create_plan_with_check(db_session, plan_in)
    assert plan.name == "Basic"
    assert plan.rate_limit == 100
    assert plan.is_active
    # Duplicate should raise ValueError
    with pytest.raises(ValueError):
        plan_service.create_plan_with_check(db_session, plan_in)


def test_get_plan(db_session):
    plan_in = PlanCreate(name="Pro", description="Pro plan", rate_limit=1000)
    plan_service.create_plan_with_check(db_session, plan_in)
    plan = plan_service.get_plan(db_session, "Pro")
    assert plan is not None
    assert plan.name == "Pro"


def test_list_all_plans(db_session):
    plan_service.create_plan_with_check(db_session, PlanCreate(name="A", description="A", rate_limit=10))
    plan_service.create_plan_with_check(db_session, PlanCreate(name="B", description="B", rate_limit=20))
    plans = plan_service.list_all_plans(db_session)
    names = [p.name for p in plans]
    assert "A" in names and "B" in names


def test_update_plan_active_status(db_session):
    plan_in = PlanCreate(name="ActiveTest", description="Test", rate_limit=50)
    plan = plan_service.create_plan_with_check(db_session, plan_in)
    updated = plan_service.update_plan_active_status(db_session, plan.id, False)
    assert updated is not None
    assert not updated.is_active
    updated = plan_service.update_plan_active_status(db_session, plan.id, True)
    assert updated.is_active


def test_deactivate_plan(db_session):
    plan_in = PlanCreate(name="DeactTest", description="Test", rate_limit=30)
    plan = plan_service.create_plan_with_check(db_session, plan_in)
    deactivated = plan_service.deactivate_plan(db_session, plan.id)
    assert deactivated is not None
    assert not deactivated.is_active


def test_activate_plan(db_session):
    plan_in = PlanCreate(name="ActTest", description="Test", rate_limit=40, is_active=False)
    plan = plan_service.create_plan_with_check(db_session, plan_in)
    activated = plan_service.activate_plan(db_session, plan.id)
    assert activated is not None
    assert activated.is_active

# CRUD direct tests

def test_create_plan(db_session):
    plan_in = PlanCreate(name="CrudPlan", description="Crud", rate_limit=5)
    plan = crud_plan.create_plan(db_session, plan_in)
    assert plan.name == "CrudPlan"


def test_get_plan_by_name(db_session):
    plan_in = PlanCreate(name="CrudGet", description="Get", rate_limit=15)
    crud_plan.create_plan(db_session, plan_in)
    plan = crud_plan.get_plan_by_name(db_session, "CrudGet")
    assert plan is not None
    assert plan.name == "CrudGet"


def test_list_plans(db_session):
    crud_plan.create_plan(db_session, PlanCreate(name="List1", description="L1", rate_limit=1))
    crud_plan.create_plan(db_session, PlanCreate(name="List2", description="L2", rate_limit=2))
    plans = crud_plan.list_plans(db_session)
    names = [p.name for p in plans]
    assert "List1" in names and "List2" in names


def test_update_plan_status(db_session):
    plan_in = PlanCreate(name="StatusTest", description="Status", rate_limit=99)
    plan = crud_plan.create_plan(db_session, plan_in)
    updated = crud_plan.update_plan_status(db_session, plan.id, False)
    assert updated is not None
    assert not updated.is_active
    updated = crud_plan.update_plan_status(db_session, plan.id, True)
    assert updated.is_active
