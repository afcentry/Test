from sqlalchemy import Column,ForeignKey,Integer,String,BLOB,Binary,BigInteger,LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
TableBase=declarative_base()