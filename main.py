"""
Entry point for Fast API Server.

This server will serve the front end (and other clients) with
API to process resume, process JD and other admin API's.
"""

import json
from intai.schemas.chatbot_model import JobPostingChat
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
import os
from dotenv import load_dotenv
from intai.schemas.job_application import Candidate, JobApplication, JobApplicationInput
from intai.schemas.job_posting import JobPosting
from intai.schemas.company import Company
from intai.schemas.jobs_chatbot_model import JobsChat
from intai.schemas.screening_model import ScreeningRequest, ScreeningScoreRequest
from intai.workers.candidate_worker import CandidateWorker
from intai.workers.job_posting_worker import JobPostingWorker
from intai.workers.job_application_worker import JobApplicationWorker
from intai.ml.bot import Chatbot, ChatbotType
from intai.utils.fe_utils import update_screening_result_frontend_service
from intai.workers.screening_questions_worker import format_transcript, find_screening_score, generate_screening_questions
#from intai.workers.job_application_actor import JobApplicationActor
from intai.models.models import (
    SessionLocal,
    BackgroundTaskDb,
    BackgroundTaskTypeEnum,
    JobPostingDb,
    CompanyDb,
)
from loguru import logger
import traceback
import timeit


app = FastAPI()

load_dotenv()
logger.add(os.getenv("LOG_FILE_NAME"), level=os.getenv("LOG_LEVEL"))


@app.get("/")
async def main_route():
    """Define the main routing function for API server."""
    return "Welcome to Intalent API!"


def _process_job_posting_task(job_posting: JobPosting, task_id: int):
    """Background task for processing job posting"""
    try:
        with SessionLocal() as session:
            worker = JobPostingWorker(job_posting, session, task_id)
            logger.trace("****in Job posting background task.")
            task_id = worker.run(task_id, is_update=job_posting.is_update)
        return {"task_id": task_id}
    except Exception as err:
        # Log the error and continue
        logger.error(f"JA:run failed {err} \n {job_posting}")
        logger.error(traceback.format_exc())


def _process_job_application_task(job_application: JobApplication, task_id: int):
    """
    Store and process the JobApplication.

    This method will store the incoming JobApplication in the table as its
    then queue up a background job to process that JobApplication.
    NOTE: Currently every candidate is part of a job in front end and we
    will model the same in backend.
    """
    # import cProfile
    # pr = cProfile.Profile()

    try:
        logger.info("Process JobApplication: ", job_application)
        #pr.enable()
         
        # actor_system = ActorSystem()
        # job_application_actor = actor_system.createActor(JobApplicationActor)
        # job_application = ...  # Load or create a JobApplication object
        # actor_system.tell(job_application_actor, {"action": "process", "job_application": job_application, "task_id": task_id})
        
        worker = JobApplicationWorker(jobApplication=job_application, task_id=task_id)
        #worker.run(is_update=job_application.is_update)
        timer = timeit.Timer(lambda: worker.run(is_update=job_application.is_update))
        execution_time = timer.timeit(1)
        logger.warning(f"----- [[ ******* Execution time for task:{task_id} is: {execution_time} seconds ****** ]] -----")
        #pr.disable()
        #logger.warning(pr.getstats())
        #pr.print_stats(sort='cumtime')
        return {"task_id": task_id}

    except Exception as err:
        # Log the error and continue
        logger.error(f"JA:run failed err: {err} \nJA: {job_application}")
        logger.error(traceback.format_exc())

def _process_candidate_task(candidate: Candidate, task_id: int):
    """
    Store and process the Candidate.

    This method will store the incoming Candidate in the table as its
    then queue up a background job to process that Candidate.
    """
    try:
        logger.info("Process Candidate: ", candidate)
        with SessionLocal() as session:
            worker = CandidateWorker(candidate=candidate, session=session, task_id=task_id)
            worker.run(task_id, is_update=candidate.is_update)
        return {"task_id": task_id}

    except Exception as err:
        # Log the error and continue
        logger.error(f"CD:run failed err: {err} \nJA: {candidate}")
        logger.error(traceback.format_exc())

@app.post("/jobposting")
async def process_job_posting(
    job_posting: JobPosting, background_tasks: BackgroundTasks
):
    """
    Store and process the JobPosting.

    This method will store the incoming JobPosting in the table as its
    then queue up a background job to process that JobPosting.
    """
    logger.info(f"Process_job_posting: {job_posting}")

    jp_str = str(job_posting)
    bg_task = BackgroundTaskDb(
        job_posting.company_id,
        message=jp_str,
        message_type=BackgroundTaskTypeEnum.JobPosting,
    )
    task_id = 0
    with SessionLocal() as session:
        bg_task.insert_background_task(session)
        logger.debug(bg_task)
        task_id = bg_task.id
    assert task_id > 0
    task = background_tasks.add_task(_process_job_posting_task, job_posting, task_id)
    logger.debug(task)

    return {"messsage": "submitted request for processing", "task_id": task_id}


@app.post("/jobapplication")
async def process_job_application(
    job_application_input: JobApplicationInput, background_tasks: BackgroundTasks
):
    """
    Store and process the JobApplication.

    This method will store the incoming JobApplication in the table as its
    then queue up a background job to process that JobApplication.
    NOTE: Currently every candidate is part of a job in front end and we
    will model the same in backend.
    """
    logger.info("API Call: Process JobApplication: ", job_application_input)
    job_application = JobApplication(**job_application_input.model_dump())
    ja_str = str(job_application)
    task_id = 0
    with SessionLocal() as session:
        bg_task = BackgroundTaskDb(
            job_application_input.company_id,
            message=ja_str,
            message_type=BackgroundTaskTypeEnum.JobApplication,
        )
        logger.info(bg_task)
        bg_task.insert_background_task(session)
        task_id = bg_task.id

    logger.debug(background_tasks)
    logger.debug(task_id)
    assert task_id > 0

    background_tasks.add_task(_process_job_application_task, job_application, task_id)

    logger.debug(f"messsage: submitted request for processing, task_id: {task_id}")
    return {
        "messsage": "submitted request for processing",
        "task_id": 1,
    }  #: bg_task.id}


@app.post("/candidate")
async def process_candidate(
    candidate: Candidate, background_tasks: BackgroundTasks
):
    """
    Store and process the Candidate

    This method will store the incoming Candidate in the table as its
    then queue up a background job to process that Candidate.
    NOTE: The difference between JobApplication and Candidate is that Candidate
    exists without a jobposting.
    """
    logger.info("API Call: Process Candidate: ", candidate)
    candidate_str = str(candidate)
    task_id = 0
    with SessionLocal() as session:
        bg_task = BackgroundTaskDb(
            candidate.company_id,
            message=candidate_str,
            message_type=BackgroundTaskTypeEnum.Candidate,
        )
        logger.info(bg_task)
        bg_task.insert_background_task(session)
        task_id = bg_task.id

    logger.debug(background_tasks)
    logger.debug(task_id)
    assert task_id > 0

    background_tasks.add_task(_process_candidate_task, candidate, task_id)

    logger.debug(f"messsage: submitted request for processing, task_id: {task_id}")
    return {
        "messsage": "submitted request for processing",
        "task_id": 1,
    }  #: bg_task.id}


# def stream_chat_response():
#     for i in range(10):
#         yield json.dumps(
#             {"event_id": i, "data": "randome data", "is_last_event": i == 9}
#         ) + "\n"
#         import time

#         time.sleep(0.5)


@app.post("/jobchatbot")
async def job_chat_request(chat_req: JobPostingChat, background_tasks: BackgroundTasks):
    """
    Store and process the Chatbot Request

    """
    logger.info(f"API Call: Process Chat Request: {chat_req}")
    with SessionLocal() as session:
        bot = Chatbot(session, chat_req.company_id, chat_req.conversation_id)
        job_posting = JobPostingDb.get_job_posting(
            session, chat_req.company_id, chat_req.client_job_id
        )
        logger.debug(f"job posting: {job_posting}")
        context = {}
        resp = ""
        if job_posting:
            context["JobDescription"] = job_posting.extracted_text
            resp = bot.start(context, chat_req.user_query)
            logger.debug(f"Response from bot: {resp}")

    # return StreamingResponse(stream_chat_response(), media_type="application/x-ndjson")
    return resp


@app.post("/jobschatbot")
async def jobs_chat_request(chat_req: JobsChat, background_tasks: BackgroundTasks):
    """
    Store and process the JobsChatbot Request

    """
    logger.info(f"API Call: Process JobsChat Request: {chat_req}")
    # get the context doc for the company

    with SessionLocal() as session:
        company_info = CompanyDb.get_company(session, chat_req.company_id)
        if not company_info:
            raise Exception(f"Company Id not found for id: {chat_req.company_id}")

        logger.info(f"company: {company_info}")

        bot = Chatbot(
            session, chat_req.company_id, chat_req.conversation_id, chatbot_type=ChatbotType.Jobs
        )
        context = {}
        """ extracted_text = company_info.context_doc
        context["JobsFAQ"] = extracted_text """
        json_resp = bot.start(context, chat_req.user_query)
        logger.debug(f"Response from bot: {json_resp}")

        # if the response.intent is general_question send the question to qa bot
        resp = json.loads(json_resp)
        if resp["intent"] == "general_question":
            logger.debug("Intent is General Questions Intent so calling OpenAI again for QA answer.")
            qa_conversation_id = "QA-" + chat_req.conversation_id
            qa_bot = Chatbot(session, chat_req.company_id, qa_conversation_id, chatbot_type=ChatbotType.QA)
            context = {}
            extracted_text = company_info.context_doc
            context["JobsFAQ"] = extracted_text
            json_resp = qa_bot.start(context, chat_req.user_query)
            logger.debug(f"Response from QA bot: {json_resp}")


    # return StreamingResponse(stream_chat_response(), media_type="application/x-ndjson")
    return json_resp

@app.post("/screeningquestions")
async def screening_questions(screening_req: ScreeningRequest, background_tasks: BackgroundTasks):
    """
    Store and process the Screening Questions Request
    """
    logger.info(f"API Call: Process Screening Questions Request: {screening_req.job_application_id}, {screening_req.job_posting_id}, {screening_req.company_id}")

    json_resp = generate_screening_questions(
        client_job_application_id=screening_req.job_application_id,
        client_job_id=screening_req.job_posting_id,
        company_id=screening_req.company_id,
        screening_focus_area=screening_req.screening_focus_area)
    logger.debug(f"Response from screening bot: {json_resp}")

    return json_resp

@app.post("/screeningscore")
async def screening_score(screening_req: ScreeningScoreRequest, background_tasks: BackgroundTasks):
    """
    Store and process the Screening Score Request
    """
    logger.info(f"API Call: Process Screening Score Request: {screening_req.job_application_id}, {screening_req.job_posting_id}, {screening_req.company_id}")

    formatted_transcript = format_transcript(screening_req.transcript, session_id=screening_req.job_application_id, client_id=screening_req.company_id)
    logger.debug(f"Formatted transcript: {formatted_transcript}")
    result_resp = find_screening_score(
        client_job_application_id=screening_req.job_application_id,
        client_job_id=screening_req.job_posting_id,
        company_id=screening_req.company_id,
        transcript=formatted_transcript,
        screening_focus_area=screening_req.screening_focus_area)
    logger.debug(f"Response from screening score bot: {result_resp}")
    # Generate a json response where result is set to result_resp and screening_id is set to screening_req.screening_id and log that.
    json_response = {
        "result": result_resp,
        "screening_id": screening_req.screening_id,
        "transcript": formatted_transcript
    }
    logger.info(f"Screening score response: {json_response}")
    update_screening_result_frontend_service(json_response)

    return json_response

@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    """Intercept and log all requests."""
    req_body = await request.body()
    response = await call_next(request)

    # TODO: Log in backgroundtask instead of foreground
    print(
        "LogMiddleware: request_body: {}, response status:{}".format(
            req_body, response.status_code
        )
    )
    return response


def start():
    """Launch with `poetry run start` at root level."""
    uvicorn.run("intai.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == '__main__':
    start()
