import json
from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Read from json config, connect to the database and creates a session for reuse.
with open("configs/config.json") as config_file:
    config = json.load(config_file)["sql_config"]

SQLALCHEMY_DATABASE_URL = (f"""mysql+pymysql://{config["username"]}:%s@{config["server_addr"]}:{config["server_port"]}/{config["database"]}""" % quote(config["password"])).replace("\n", "")
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
