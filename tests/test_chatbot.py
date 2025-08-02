from dotenv import load_dotenv
import os
from intai.ml.bot import Chatbot
from intai.ml.llm_client import LLMClient
from intai.ml.utils import LLMModelType
from intai.ml.ai_prompt import AIPrompt, ChatbotAIPrompt
from intai.models.models import SessionLocal
from intai.utils.file_utils import get_bytes_from_file, extract_text
import pytest
from icecream import ic


class TestChatbot:
    # @pytest.mark.skip(reason="disable openai calls test")
    @classmethod
    def test_chatbot_basic(cls):
        load_dotenv()
        from pathlib import Path

        # input_jp_path = Path(os.getenv("TEST_DATA_FOLDER"), "chatbot_jp.pdf")
        # assert input_jp_path.exists()
        # # TODO Get the file from test config.
        # bytes_data, docType = get_bytes_from_file(str(input_jp_path))
        # extracted_text = extract_text(bytes_data, docType)
        # ic(extracted_text)
        # assert len(extracted_text) > 0
        # # assert "Finance" in extracted_text
        context = {}
        extracted_text = """
            # Human Resources (HR) Manager Job description\n\n
        |Company Name|Coserve Solutions|
        |---|---|
        |Job Location|Hyderabad|
        |NO of Years’ Experience Required|5-10|
        |CTC|7-10 Lacs|


        # Key Responsibilities

        - Developing and implementing HR strategies and initiatives aligned with the overall business strategy
        - Bridging management and employee relations by addressing demands, grievances or other issues
        - Managing the recruitment and selection process

        # Job brief

        We are looking for a skilled HR manager to oversee all aspects of Human Resources practices and processes. You will support business needs and ensure the proper implementation of company strategy and objectives. The goal is to promote corporate values and enable business success through human resources management, including job design, recruitment, performance management, training & development, employment cycle changes, talent management, and facilities management services.

        # Responsibilities

        - Develop and implement HR strategies and initiatives aligned with the overall business strategy
        - Bridge management and employee relations by addressing demands, grievances or other issues
        - Manage the recruitment and selection process
        - Support current and future business needs through the development, engagement, motivation and preservation of human capital
        - Develop and monitor overall HR strategies, systems, tactics and procedures across the organization
        - Nurture a positive working environment
        - Oversee and manage a performance appraisal system that drives high performance
        - Maintain pay plan and benefits program
        - Assess training needs to apply and monitor training programs
        - Report to management and provide decision support through HR metrics
        - Ensure legal compliance throughout human resource management

        # Requirements

        - Proven working experience as HR manager or other HR executive
        - People oriented and results driven
        - Demonstrable experience with human resources metrics
        - Knowledge of HR systems and databases\n- Ability to architect strategy along with leadership skills
        - Excellent active listening, negotiation and presentation skills
        - Competence to build and effectively manage interpersonal relationships at all levels of the company
        - In-depth knowledge of labour law and HR best practices
        - Bachelors/ Master’s degree in Human Resources or related field
        """
        context["JobDescription"] = extracted_text

        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            with SessionLocal() as session:
                bot = Chatbot(session, 1)
                bot.start(context)
                user_inputs = [
                    "maybe, how much experience is needed and where is it located?",
                    "yes I am interested",
                ]

                response = bot.predict("yes I am interested")
                ic(f"Bot response: {response} \n memory: {bot.memory}")
                assert len(bot.get_memory()) > 0

                ic(
                    f"q: 'yes I am interested'\nBot response: {response} \n memory: {bot.memory}"
                )
                assert len(bot.get_memory()) > 0
                current_salary_asked = False
                expected_salary_asked = False
                notice_asked = False
                tries = 0
                while (
                    not current_salary_asked
                    or not notice_asked
                    or not expected_salary_asked
                ):
                    if "current" in response:
                        current_salary_asked = True
                        inp = "50000"
                    elif "expected" in response:
                        expected_salary_asked = True
                        inp = "56000"
                    elif "notice" in response:
                        inp = "90 days"
                    elif "Thank" in response:
                        break

                    tries += 1
                    if tries > 3:
                        break
                    response = bot.predict(inp)
                    ic(f"q: {inp}\nBot response: {response} \n memory: {bot.memory}")

    def test_jobs_chatbot(cls):
        load_dotenv()
        from pathlib import Path

        context = {}
        extracted_text = """Axis Bank FAQ

        Q: How do I apply for an open role at Axis Bank?
        A: Go to Explore Opportunities -> Select your preferred state of posting -> select your skill/domain/expertise from the drop down

        Q: How do I apply for Campus/Academia roles at Axis?
        A: Click on Campus Careers -> Select your preferred campus program from the last of programs and Apply

        Q: How do I apply for GIGA F/Part time opportunities
        A: Click on GIG-A Opportunities -> Click on Find your next Challenge now

        Q: What is the hiring process at Axis?
        A: Go to "How we hire" section on Axis bank website.

        Q: Wha are the employee benefits at Axis?
        A: Go to "Perks and benefits" section at Axis bank website.

        """
        context["JobsFAQ"] = extracted_text

        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            with SessionLocal() as session:
                bot = Chatbot(session, 1, "122", chatbot_type=True)
                bot.start(
                    context,
                    "I want to find a job status at Axis bank for email fdf@gmail.com",
                )
                user_inputs = [
                    "maybe, how much experience is needed and where is it located?",
                    "yes I am interested",
                ]

                response = bot.predict("I want to find a job at Axis bank.")
                ic(response)
                response = bot.predict("5 years of experience in Sales")
                assert len(bot.get_memory()) > 0

                ic(
                    f"q: 'How do I apply for open role at Axis?'\nBot response: {response} \n memory: {bot.memory}"
                )
                assert len(bot.get_memory()) > 0

                response = bot.predict("Just get me the jobs with this information")
                ic(response)
