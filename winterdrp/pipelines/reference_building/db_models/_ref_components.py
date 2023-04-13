"""
Module to make reference components table
"""
from typing import ClassVar

from pydantic import Field
from sqlalchemy import VARCHAR, Column, Float, Integer

from winterdrp.pipelines.reference_building.db_models.basemodel import (
    RefBase,
    dec_field,
    ra_field,
)
from winterdrp.processors.sqldatabase.basemodel import BaseDB


class RefComponentsTable(RefBase):
    """
    Table for individual reference images
    """

    __tablename__ = "refcomponents"

    compid = Column(Integer, primary_key=True)
    query_ra = Column(Float)
    query_dec = Column(Float)

    savepath = Column(VARCHAR(255))
    query_url = Column(VARCHAR(255))


class RefComponents(BaseDB):
    """
    Pydantic model for Reference components
    """

    sql_model: ClassVar = RefComponentsTable

    query_ra: float = ra_field
    query_dec: float = dec_field
    savepath: str = Field(min_length=1)
    query_url: str = Field(min_length=1)

    def exists(self) -> bool:
        """
        Checks if the pydantic-ified data exists the corresponding sql database

        :return: bool
        """
        return self.sql_model().exists(
            values=[self.query_ra, self.query_dec], keys=["query_ra", "query_dec"]
        )