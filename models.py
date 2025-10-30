from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Position(Base):
    __tablename__ = 'positions'

    poscode = Column(Integer, primary_key=True)
    posname = Column(String(100), nullable=False)
    parentpos = Column(Integer, nullable=True)
    filial = Column(Integer, nullable=False)


class Employee(Base):
    __tablename__ = 'employee'

    emplcode = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    patronymic = Column(String(50), nullable=False)
    birthday = Column(Date, nullable=False)
    passport = Column(String(10), nullable=False)
    poscode = Column(Integer, ForeignKey('positions.poscode'), nullable=False)
    filial = Column(Integer, nullable=False)
    status = Column(String(20), default='Active')

    position = relationship("Position")
    history = relationship("EmplHistory", back_populates="employee")
    conflicts = relationship("Conflist", back_populates="employee")


class EmplHistory(Base):
    __tablename__ = 'emplhistory'

    historyid = Column(Integer, primary_key=True)
    emplcode = Column(Integer, ForeignKey('employee.emplcode'), nullable=False)
    changedate = Column(Date, nullable=False)
    surname = Column(String(50), nullable=False)
    passport = Column(String(10), nullable=False)
    poscode = Column(Integer, ForeignKey('positions.poscode'), nullable=False)
    action = Column(String(50), nullable=False)

    employee = relationship("Employee", back_populates="history")


class Conflist(Base):
    __tablename__ = 'conflist'

    conflictid = Column(Integer, primary_key=True)
    emplcode = Column(Integer, ForeignKey('employee.emplcode'), nullable=False)
    errlist = Column(String(1000), nullable=False)
    conflictdate = Column(TIMESTAMP, default=func.now())
    resolved = Column(Boolean, default=False)

    employee = relationship("Employee", back_populates="conflicts")