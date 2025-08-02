# from thespian.actors import Actor, ActorSystem
# from loguru import logger

# class JobApplicationActor(Actor):
#     """
#     JobApplicationActor Class.

#     This class orchestrates the job application processing pipeline using Thespian actors.
#     """

#     def __init__(self):
#         super().__init__()
#         self.job_application = None
#         self.db_session = None
#         self.company_id = None
#         self.task_id = None
#         self.is_update = False

#     def receiveMessage(self, message, sender):
#         if isinstance(message, dict) and message.get('type') == 'start_processing':
#             self.job_application = message['job_application']
#             self.db_session = message['db_session']
#             self.company_id = message['company_id']
#             self.task_id = message.get('task_id', 0)
#             self.is_update = message.get('is_update', False)
#             self.run()
#         elif isinstance(message, dict) and message.get('type') == 'actor_complete':
#             self.handle_actor_complete(message)

#     def run(self):
#         try:
#             self.send(self.createActor(LoadJobActor), {
#                 'type': 'load_job',
#                 'job_application': self.job_application,
#                 'db_session': self.db_session,
#                 'company_id': self.company_id,
#                 'task_id': self.task_id
#             })
#         except Exception as err:
#             logger.error(f"JA:run failed {err}")
#             self.handle_error(err)

#     def handle_actor_complete(self, message):
#         actor_type = message.get('actor_type')
#         if actor_type == 'LoadJobActor':
#             self.send(self.createActor(SaveDBExtractActor), {
#                 'type': 'save_and_extract',
#                 'job_application': self.job_application,
#                 'db_session': self.db_session,
#                 'company_id': self.company_id,
#                 'is_update': self.is_update,
#                 'job_posting_db': message.get('job_posting_db'),
#                 'client_job_id': message.get('client_job_id'),
#                 'job_posting_id': message.get('job_posting_id')
#             })
#         elif actor_type == 'SaveDBExtractActor':
#             self.send(self.createActor(GetScoreParseActor), {
#                 'type': 'get_score_and_parse',
#                 'job_application': self.job_application,
#                 'db_session': self.db_session,
#                 'company_id': self.company_id,
#                 'job_application_db': message.get('job_application_db'),
#                 'ja_extracted_text': message.get('ja_extracted_text')
#             })
#         elif actor_type == 'GetScoreParseActor':
#             self.send(self.createActor(FinishProcessingActor), {
#                 'type': 'finish_processing',
#                 'job_application': self.job_application,
#                 'db_session': self.db_session,
#                 'company_id': self.company_id,
#                 'task_id': self.task_id,
#                 'score': message.get('score'),
#                 'score_summary': message.get('score_summary')
#             })
#         elif actor_type == 'FinishProcessingActor':
#             logger.info(f"Job application processing completed for {self.job_application.client_job_application_id}")

#     def handle_error(self, err):
#         status = "ERROR"
#         job_application_fe = JobApplicationFrontEnd(companyId=self.company_id, processingStatus=status, processingStatusProgress=100)
#         update_ja_frontend_service(self.job_application.client_job_application_id, job_application_fe)
#         BackgroundTaskDb.update_background_task(self.db_session, self.task_id, status)
#         if hasattr(self, 'job_application_db'):
#             self.job_application_db.update_job_application(self.db_session, status=status)

# class LoadJobActor(Actor):
#     def receiveMessage(self, message, sender):
#         if isinstance(message, dict) and message.get('type') == 'load_job':
#             try:
#                 job_application = message['job_application']
#                 db_session = message['db_session']
#                 company_id = message['company_id']
#                 task_id = message['task_id']

#                 logger.trace("Loading JobPosting from application")
#                 status = "STARTED"
#                 BackgroundTaskDb.update_background_task(db_session, task_id, status)

#                 job_posting_db = JobPostingDb.get_job_posting(
#                     db_session, company_id, job_application.client_job_id
#                 )
#                 logger.debug(f"job_posting_db: {job_posting_db}")
#                 if job_posting_db is None:
#                     raise Exception("job_posting not found")

#                 client_job_id = job_posting_db.client_job_id
#                 job_posting_id = job_posting_db.id

#                 self.send(sender, {
#                     'type': 'actor_complete',
#                     'actor_type': 'LoadJobActor',
#                     'job_posting_db': job_posting_db,
#                     'client_job_id': client_job_id,
#                     'job_posting_id': job_posting_id
#                 })
#             except Exception as err:
#                 logger.error(f"Error in LoadJobActor: {err}")
#                 self.send(sender, {'type': 'actor_error', 'error': str(err)})

# class SaveDBExtractActor(Actor):
#     def receiveMessage(self, message, sender):
#         if isinstance(message, dict) and message.get('type') == 'save_and_extract':
#             try:
#                 job_application = message['job_application']
#                 db_session = message['db_session']
#                 company_id = message['company_id']
#                 is_update = message['is_update']
#                 job_posting_db = message['job_posting_db']
#                 job_posting_id = message['job_posting_id']

#                 logger.info(f"{'Update' if is_update else 'Insert'} JobApplication Entity")
                
#                 job_application_db = JobApplicationDb(job_application, job_posting_id)
#                 job_application_db.status = "Started"
#                 job_application_fe = JobApplicationFrontEnd(
#                     companyId=company_id, processingStatus="WORKING", processingStatusProgress=20)

#                 # Insert job application
#                 if is_update:
#                     job_application_db.update_job_application(db_session)
#                 else:
#                     job_application_db.insert_job_application(db_session)

#                 # Update frontend
#                 update_ja_frontend_service(job_application.client_job_application_id, job_application_fe)

#                 # Extract text
#                 ja_extracted_text = self.extract_text(job_application)

#                 self.send(sender, {
#                     'type': 'actor_complete',
#                     'actor_type': 'SaveDBExtractActor',
#                     'job_application_db': job_application_db,
#                     'ja_extracted_text': ja_extracted_text
#                 })
#             except Exception as err:
#                 logger.error(f"Error in SaveDBExtractActor: {err}")
#                 self.send(sender, {'type': 'actor_error', 'error': str(err)})

#     def extract_text(self, job_application):
#         # Implement text extraction logic here
#         return "Extracted text"

# class GetScoreParseActor(Actor):
#     def receiveMessage(self, message, sender):
#         if isinstance(message, dict) and message.get('type') == 'get_score_and_parse':
#             try:
#                 job_application = message['job_application']
#                 db_session = message['db_session']
#                 company_id = message['company_id']
#                 job_application_db = message['job_application_db']
#                 ja_extracted_text = message['ja_extracted_text']

#                 parsed_data = self.parse_and_match_application(ja_extracted_text)
#                 factor_score = self.get_factor_score(parsed_data)
#                 score_summary = self.get_score_summary(factor_score)

#                 # Save score to database
#                 self.save_job_application_score(db_session, job_application_db, parsed_data, factor_score, score_summary)

#                 self.send(sender, {
#                     'type': 'actor_complete',
#                     'actor_type': 'GetScoreParseActor',
#                     'score': str(factor_score.factor_score),
#                     'score_summary': str(score_summary)
#                 })
#             except Exception as err:
#                 logger.error(f"Error in GetScoreParseActor: {err}")
#                 self.send(sender, {'type': 'actor_error', 'error': str(err)})

#     def parse_and_match_application(self, ja_extracted_text):
#         # Implement parsing and matching logic here
#         return {}

#     def get_factor_score(self, parsed_data):
#         # Implement factor score calculation here
#         return None

#     def get_score_summary(self, factor_score):
#         # Implement score summary generation here
#         return ""

#     def save_job_application_score(self, db_session, job_application_db, parsed_data, factor_score, score_summary):
#         # Implement score saving logic here
#         pass

# # Usage
# if __name__ == "__main__":
#     actor_system = ActorSystem()
#     job_application_actor = actor_system.createActor(JobApplicationActor)
#     actor_system.ask(job_application_actor, {
#         'type': 'start_processing',
#         'job_application': job_application,
#         'db_session': db_session,
#         'company_id': company_id,
#         'task_id': task_id,
#         'is_update': is_update
#     })
