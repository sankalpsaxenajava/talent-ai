from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from sqlalchemy.engine import create_engine
from intai.models.models import JobPosting, JobApplication


def start():
    Base = declarative_base()

    # Step 2: Establish a database connection

    engine = create_engine(
        "mysql://root:Madarchod01%40@127.0.0.1:3306/intalent?charset=utf8", echo=True
    )
    Base.metadata.create_all(engine)

    # Step 5: Insert data into the database
    Session = sessionmaker(bind=engine)
    session = Session()

    # new_job_posting = JobPosting(
    #     id=1,
    #     company_id=1,
    #     client_job_id=1,
    #     job_posting_doc_url="http://www.jd.com",
    #     status="Init",
    # )

    # new_job_application = JobApplication(
    #     id=2,
    #     company_id=1,
    #     client_job_application_id=1,
    #     job_posting_id=1,
    #     candidate_email="nest@west.com",
    #     resume_doc_url="http://www.g.com",
    #     status="Init",
    # )
    # # session.add(new_job_posting)
    # session.add(new_job_application)
    # session.commit()

    # Step 6: Query data from the database
    # Example: Querying all users from the database
    all_job_applications = session.query(JobApplication).all()

    print(all_job_applications)
    # Example: Querying a specific user by their username
    ja = session.query(JobApplication).filter_by(company_id=1).first()

    print(ja)
    jp = session.query(JobPosting).filter_by(id=1).first()
    print(jp)
    # Step 7: Close the session
    session.close()
