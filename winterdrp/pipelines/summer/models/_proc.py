"""
Models for the 'proc' table
"""
import os
from typing import ClassVar

from pydantic import Field, validator
from sqlalchemy import (  # event,
    REAL,
    VARCHAR,
    Column,
    Double,
    ForeignKey,
    Integer,
    Sequence,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from winterdrp.pipelines.summer.models._raw import Raw
from winterdrp.pipelines.summer.models.basemodel import SummerBase
from winterdrp.processors.sqldatabase.basemodel import BaseDB, dec_field, ra_field


class ProcTable(SummerBase):  # pylint: disable=too-few-public-methods
    """
    Proc table in database
    """

    __tablename__ = "proc"
    __table_args__ = {"extend_existing": True}

    uprocid = Column(
        Integer,
        Sequence(start=1, name="raw_urawid_seq"),
        autoincrement=True,
        unique=True,
    )
    procid = Column(Double, primary_key=True, autoincrement=False)

    urawid: Mapped[int] = mapped_column(ForeignKey("raw.urawid"))
    raw_ids: Mapped["RawTable"] = relationship(back_populates="proc")

    savepath = Column(VARCHAR(255), unique=True)
    wghtpath = Column(VARCHAR(255), unique=True)

    cd1_1 = Column(REAL)
    cd1_2 = Column(REAL)
    cd2_1 = Column(REAL)
    cd2_2 = Column(REAL)
    crval1 = Column(REAL)
    crval2 = Column(REAL)
    crpix1 = Column(REAL)
    crpix2 = Column(REAL)
    zp_auto = Column(REAL)
    fwhm_med = Column(REAL)
    fwhm_std = Column(REAL)
    astr_dpa = Column(REAL)
    astr_off = Column(REAL)
    zp_auto_nstars = Column(Integer)
    zp_auto_std = Column(REAL)
    maglim = Column(REAL)


class Proc(BaseDB):
    """
    A pydantic model for a proc database entry
    """

    sql_model: ClassVar = ProcTable

    urawid: int = Field(ge=0)
    procid: int = Field(ge=0)
    savepath: str = Field(min_length=1)
    wghtpath: str = Field(min_length=1)

    cd1_1: float = Field()
    cd1_2: float = Field()
    cd2_1: float = Field()
    cd2_2: float = Field()
    crval1: float = ra_field
    crval2: float = dec_field
    crpix1: float = Field()
    crpix2: float = Field()
    zp_auto: float = Field(ge=0)
    fwhm_med: float = Field(ge=0)
    fwhm_std: float = Field(ge=0)
    astr_dpa: float = Field()
    astr_off: float = Field()
    zp_auto_nstars: int = Field(ge=0)
    zp_auto_std: float = Field(ge=0)
    maglim: float = Field()

    @validator("savepath")
    @classmethod
    def validate_savepath(cls, field_value: str):
        """
        Ensure that path exists

        :param field_value: field value
        :return: field value
        """
        assert os.path.exists(field_value)
        return field_value

    @validator("urawid")
    @classmethod
    def validate_expid(cls, field_value: int):
        """
        Ensure that expid exists in exposures table
        Args:
            field_value: expid

        Returns:

        """
        assert Raw.sql_model().exists(keys="urawid", values=field_value)
        return field_value