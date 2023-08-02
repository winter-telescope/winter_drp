"""
Util functions for database interactions
"""
from sqlalchemy import Engine, NullPool, create_engine

from mirar.processors.database.postgres import DB_PASSWORD, DB_USER


def get_engine(
    db_user: str = DB_USER,
    db_password: str = DB_PASSWORD,
    db_name: str = "summer",
) -> Engine:
    """
    Function to create a postgres engine

    :param db_user: User for db
    :param db_password: password for db
    :param db_name: name of db
    :return: sqlalchemy engine
    """

    return create_engine(
        f"postgresql+psycopg://{db_user}:{db_password}" f"@/{db_name}",
        future=True,
        poolclass=NullPool,
    )
