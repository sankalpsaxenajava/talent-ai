# import json
# from thespian.actors import Actor, ActorExitRequest

# from intai.ml.ai_prompt import (
#     FactorAnalysisAIPrompt,
#     JobApplicationAIPrompt,
#     JobApplicationMatchSummaryAIPrompt,
# )
# from intai.ml.ai_client import OpenAIClient
# from intai.ml.scoring_utils import (
#     get_skill_score_job,
#     ja_calculate_matching_percentage,
#     ja_calculate_matching_skill_score,
#     ja_get_bucket,
#     ja_match_industry_with_jd,
#     ja_match_title_with_jd,
#     match_certificate_skills_with_jd_skills,
# )
# from intai.models.models import (
#     BackgroundTaskDb,
#     JobApplicationDb,
#     JobApplicationDetailDb,
#     JobApplicationCertificationDb,
#     JobApplicationCertificationSkillDb,
#     JobApplicationEducationDb,
#     JobApplicationExperienceDb,
#     JobApplicationInterestDb,
#     JobApplicationAwardDb,
#     JobApplicationLanguageDb,
#     JobApplicationProjectDb,
#     JobApplicationPublicationDb,
#     JobApplicationVolunteerDb,
#     JobApplicationAddressDb,
#     JobApplicationSkillDb,
#     JobApplicationScoreDb,
# )
# from intai.schemas.job_application import (
#     JobApplication,
#     JobApplicationScore,
#     JobApplicationAddress,
#     JobApplicationDetail,
#     JobApplicationCertification,
#     JobApplicationCertificationSkill,
#     JobApplicationEducation,
#     JobApplicationExperience,
#     JobApplicationInterest,
#     JobApplicationAward,
#     JobApplicationLanguage,
#     JobApplicationProject,
#     JobApplicationPublication,
#     JobApplicationVolunteer,
# )
# from intai.utils.fe_utils import update_ja_frontend_service
# from intai.utils.file_utils import extract_text, get_bytes_from_url
# from intai.utils.json_data_utils import (
#     ja_get_address_from_json,
#     ja_get_details_from_json,
#     ja_get_experience_from_json,
#     ja_get_education_from_json,
#     ja_get_languages_from_json,
#     ja_get_publications_from_json,
#     ja_get_awards_from_json,
#     ja_get_interests_from_json,
#     ja_get_volunteers_from_json,
#     ja_get_certifications_from_json,
#     ja_get_projects_from_json,
# )
# from intai.utils.model_utils import insert_applicant_entities
# from intai.utils.str_utils import check_str_not_null

# from loguru import logger
   
# class ParseApplicationActor(Actor):
#     def receiveMessage(self, message, sender):
#         if isinstance(message, dict) and message.get("action") == "parse":
#             logger.info(f"Parse Application Actor received message: {message} sender: {sender}")
#             job_application = message["job_application"]
#             ja_bytes_data, ja_docType = get_bytes_from_url(job_application.resume_doc_url)
#             ja_extracted_text = extract_text(ja_bytes_data, ja_docType)
#             prompt = JobApplicationAIPrompt(ja_text=ja_extracted_text)
#             ai_client = LLMClient()
#             extracted_entities = ai_client.get_model_response(prompt)
#             self.send(sender, {"extracted_entities": extracted_entities, "ja_extracted_text": ja_extracted_text})

# class ScoringApplicationActor(Actor):
#     def receiveMessage(self, message, sender):
#         if isinstance(message, dict) and message.get("action") == "score":
#             logger.info(f"Scoring Application Actor received message: {message} sender: {sender}")

#             self.sender = sender
#             job_application = message["job_application"]
#             ja_extracted_text = message["ja_extracted_text"]
#             jp_text = job_application.job_posting_db.extracted_text
            
#             factor_analysis_actor = self.createActor(FactorAnalysisActor)
#             summary_actor = self.createActor(SummaryActor)
            
#             self.send(factor_analysis_actor, {
#                 "jp_text": jp_text,
#                 "ja_text": ja_extracted_text
#             })
#             self.send(summary_actor, {
#                 "jp_text": jp_text,
#                 "ja_text": ja_extracted_text
#             })
            
#             self.factor_score = None
#             self.summary = None
#             self.become(self.wait_for_responses)
    
#     def wait_for_responses(self, message, sender):
#         if "factor_score" in message:
#             self.factor_score = message["factor_score"]
#         elif "summary" in message:
#             self.summary = message["summary"]
        
#         if self.factor_score is not None and self.summary is not None:
#             logger.info(f"Scoring Application Actor sending factor score: {self.factor_score} summary: {self.summary}")
#             self.send(self.sender, {
#                 "factor_score": self.factor_score,
#                 "summary": self.summary
#             })
#             self.send(self.myAddress, ActorExitRequest())

# class FactorAnalysisActor(Actor):
#     def receiveMessage(self, message, sender):
#         logger.info(f"Factor Analysis Actor received message: {message} sender: {sender}")
#         jp_text = message["jp_text"]
#         ja_text = message["ja_text"]
#         prompt = FactorAnalysisAIPrompt(jp_text=jp_text, ja_text=ja_text)
#         ai_client = LLMClient()
#         response = ai_client.get_model_response(prompt)
#         data = json.loads(response)
#         self.send(sender, {"factor_score": data["final_score"]})

# class SummaryActor(Actor):
#     def receiveMessage(self, message, sender):
#         logger.info(f"Summary Actor received message: {message} sender: {sender}")
#         jp_text = message["jp_text"]
#         ja_text = message["ja_text"]
#         summary_prompt = JobApplicationMatchSummaryAIPrompt(jp_text=jp_text, ja_text=ja_text)
#         ai_client = LLMClien()
#         summary_response = ai_client.get_model_response(summary_prompt)
#         summary_data = json.loads(summary_response)
#         self.send(sender, {"summary": summary_data["summary"]})

# class SaveJobApplicationActor(Actor):
#     def receiveMessage(self, message, sender):
#         if isinstance(message, dict) and message.get("action") == "save":
#             logger.info(f"Save Job Application Actor received message: {message} sender: {sender}")
#             job_application = message["job_application"]
#             try:
#                 # Assuming job_application has a method to save itself to the database
#                 job_application.save_to_db()
#                 self.send(sender, {"status": "saved", "job_application_id": job_application.id})
#             except Exception as err:
#                 logger.error(f"Error saving job application: {err}")
#                 self.send(sender, {"status": "error", "message": str(err)})

# class JobApplicationActor(Actor):
#     def receiveMessage(self, message, sender):
#         try:
#             if isinstance(message, dict) and message.get("action") == "process":
#                 logger.trace(f"JobApplicationActor: Received message: {message} sender: {sender}")

#                 status = "STARTED"
#                 task_id = message["task_id"]
#                 BackgroundTaskDb.update_background_task(self.db, task_id, status)
#                 job_application = message["job_application"]
#                 parse_actor = self.createActor(ParseApplicationActor)
#                 save_actor = self.createActor(SaveJobApplicationActor)
                
#                 self.send(parse_actor, {"action": "parse", "job_application": job_application})
#                 self.send(save_actor, {"action": "save", "job_application": job_application})
                
#                 self.become(self.wait_for_parsing_and_saving)
#                 self.parse_result = None
#                 self.save_result = None
#                 self.original_sender = sender
#         except Exception as e:
#             logger.error(f"Error in receiveMessage: {str(e)}")
#             self.update_job_application_status(job_application, "ERROR")
#             self.send(sender, {"status": "error", "message": str(e)})
#             self.send(self.myAddress, ActorExitRequest())

#     def wait_for_parsing_and_saving(self, message, sender):
#         try:
#             if isinstance(message, dict):
#                 if "extracted_entities" in message:
#                     self.parse_result = message
#                 elif "status" in message and message["status"] in ["saved", "error"]:
#                     self.save_result = message

#             if self.parse_result and self.save_result:
#                 if self.save_result["status"] == "error":
#                     self.send(self.original_sender, {"status": "error", "message": self.save_result["message"]})
#                     self.send(self.myAddress, ActorExitRequest())
#                 else:
#                     self.process_parsing_result(self.parse_result)
#         except Exception as e:
#             logger.error(f"Error in wait_for_parsing_and_saving: {str(e)}")
#             self.update_job_application_status(self.parse_result["job_application"], "ERROR")
#             self.send(self.original_sender, {"status": "error", "message": str(e)})
#             self.send(self.myAddress, ActorExitRequest())

#     def process_parsing_result(self, message):
#         try:
#             job_application = message["job_application"]
#             ja_extracted_text = message["ja_extracted_text"]
#             scoring_actor = self.createActor(ScoringApplicationActor)
#             self.send(scoring_actor, {"action": "score", "job_application": job_application, "ja_extracted_text": ja_extracted_text})
#             self.become(self.wait_for_scoring)
#         except Exception as e:
#             logger.error(f"Error in process_parsing_result: {str(e)}")
#             self.update_job_application_status(job_application, "ERROR")
#             self.send(self.original_sender, {"status": "error", "message": str(e)})
#             self.send(self.myAddress, ActorExitRequest())

#     def wait_for_scoring(self, message, sender):
#         try:
#             if isinstance(message, dict) and "factor_score" in message:
#                 factor_score = message["factor_score"]
#                 summary = message["summary"]
#                 logger.info(f"Factor Score: {factor_score}, Summary: {summary}")
#                 self.send(sender, {"status": "completed", "factor_score": factor_score, "summary": summary})
#                 self.send(self.myAddress, ActorExitRequest())
#         except Exception as e:
#             logger.error(f"Error in wait_for_scoring: {str(e)}")
#             self.update_job_application_status(message["job_application"], "ERROR")
#             self.send(sender, {"status": "error", "message": str(e)})
#             self.send(self.myAddress, ActorExitRequest())

#     def update_job_application_status(self, job_application, status):
#         try:
#             job_application.status = status
#             job_application.save_to_db()
#         except Exception as e:
#             logger.error(f"Error updating job application status: {str(e)}")

# # Example usage

    
