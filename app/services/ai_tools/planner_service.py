"""
Scenario Planner Service

Wrapper around existing planner functionality with enhanced service interface.
"""

from app.services.scenario_planner import ScenarioPlanner as ExistingPlanner
from app.models import Scenario
from app import db


class PlannerService:
    """Service for financial scenario planning."""

    @staticmethod
    def create_scenario(user_id, name, description):
        """Create a new financial scenario."""
        scenario = Scenario(user_id=user_id, name=name, description=description)
        db.session.add(scenario)
        db.session.commit()
        return scenario

    @staticmethod
    def get_scenario(scenario_id):
        """Get a scenario by ID."""
        return Scenario.query.get(scenario_id)

    @staticmethod
    def get_user_scenarios(user_id):
        """Get all scenarios for a user."""
        return Scenario.query.filter_by(user_id=user_id).all()

    @staticmethod
    def delete_scenario(scenario_id):
        """Delete a scenario."""
        scenario = PlannerService.get_scenario(scenario_id)
        if scenario:
            db.session.delete(scenario)
            db.session.commit()

    @staticmethod
    def project_scenario(scenario_id, months=12):
        """Project financial outcomes for a scenario."""
        return ExistingPlanner.project_scenario(scenario_id, months)

    @staticmethod
    def compare_scenarios(scenario_ids):
        """Compare multiple scenarios."""
        return ExistingPlanner.compare_scenarios(scenario_ids)
