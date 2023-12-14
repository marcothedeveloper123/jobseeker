from typing import Optional

from sqlmodel import Field, SQLModel, Session, create_engine
from dotenv import load_dotenv
import os
import pandas as pd
load_dotenv()

dbstring = os.getenv("dbstring")


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str
    job_title: Optional[str]
    company_name: Optional[str] = None
    location: Optional[str] = None
    job_link: Optional[str] = None
    job_description: Optional[str] = None


engine = create_engine(dbstring, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_jobs(csv_file="./data/bronze/marco_script/linkedin/head_of_product/jobs_Head_of_Product_-_European_Union_-_Remote_-_LinkedIn.csv"):
    session = Session(engine)
    df = pd.read_csv(csv_file)
    job_json = df.to_dict(orient="records")
    for job in job_json:
        job_ingest = Job(**job)
        session.add(job_ingest)
    session.commit()
        
if __name__ == "__main__":
    create_db_and_tables()
    create_jobs()