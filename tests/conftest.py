"""Gemeinsame Test-Fixtures fuer ngdai."""

import pytest


@pytest.fixture
def sample_entity():
    """Beispiel-Netzbetreiber fuer Tests."""
    from ngdai.core.models import LegalEntity
    return LegalEntity(
        name="Stadtwerke Elmshorn",
        mastr_nr="SNB123456789",
        sectors=["strom"],
        state="Schleswig-Holstein",
        city="Elmshorn",
    )


@pytest.fixture
def sample_fact_definition():
    """Beispiel-Fakt-Definition."""
    from ngdai.core.models import FactDefinition
    from ngdai.core.enums import TemporalBehavior, ValueType
    return FactDefinition(
        id="effizienzwert",
        name="Effizienzwert",
        temporal_behavior=TemporalBehavior.PERIOD_FIXED,
        value_type=ValueType.NUMERIC,
        unit="%",
    )
