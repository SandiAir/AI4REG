"""Datenbank-Engine Setup - SQLAlchemy + AGE."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ngdai.core.config import get_settings

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.get_database_url(),
            echo=settings.database.echo,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return _session_factory


def get_session() -> Session:
    factory = get_session_factory()
    return factory()


def init_age(session: Session) -> None:
    """Initialisiert Apache AGE in der Session."""
    session.execute(text("LOAD 'age'"))
    session.execute(text("SET search_path = ag_catalog, \"$user\", public"))


def cypher_query(session: Session, query: str, graph_name: str = "ngdai_graph") -> list:
    """Fuehrt eine Cypher-Query via AGE aus."""
    init_age(session)
    sql = text(f"SELECT * FROM cypher('{graph_name}', $$ {query} $$) AS (result agtype)")
    result = session.execute(sql)
    return [row[0] for row in result.fetchall()]
