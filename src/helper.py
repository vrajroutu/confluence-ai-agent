import os
from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# ================================================================
# Planning & Routing Agent: Classifies the query and later provides a final summary.
# ================================================================
class PlanningRoutingAgent:
    def __init__(self, llm):
        self.llm = llm
        # Prompt to classify the query and check for missing details.
        self.classification_prompt = PromptTemplate(
            input_variables=["query"],
            template=(
                "You are a help desk planning and routing agent. Analyze the following user query and classify "
                "the request into one of these categories: 'Password Reset', 'VDI Resource Increase', or 'Other IT Support'.\n"
                "Also, identify any missing information required to process the request. Return your answer in the format:\n\n"
                "Category: <category>\nMissing: <missing details or 'None'>\n\n"
                "User Query: {query}"
            )
        )
        self.classification_chain = LLMChain(llm=self.llm, prompt=self.classification_prompt)

        # Prompt to generate the final summary for the user.
        self.final_summary_prompt = PromptTemplate(
            input_variables=["query", "category", "verification", "resolution"],
            template=(
                "You are a help desk final summary agent. Based on the following information, generate a final summary "
                "report for the user that outlines the original request, the classification, the verification outcome, and "
                "the resolution details.\n\n"
                "User Query: {query}\n"
                "Category: {category}\n"
                "Verification Outcome: {verification}\n"
                "Resolution Details: {resolution}\n\n"
                "Final Summary Report:"
            )
        )
        self.final_summary_chain = LLMChain(llm=self.llm, prompt=self.final_summary_prompt)

    def process_query(self, query: str) -> str:
        response = self.classification_chain.run(query=query)
        return response.strip()

    def generate_final_summary(self, query: str, category: str, verification: str, resolution: str) -> str:
        summary = self.final_summary_chain.run(
            query=query, category=category, verification=verification, resolution=resolution
        )
        return summary.strip()


# ================================================================
# Verification Agent: Ensures the request details are complete (single check).
# ================================================================
class VerificationAgent:
    def __init__(self, llm):
        self.llm = llm
        self.verification_prompt = PromptTemplate(
            input_variables=["details", "category"],
            template=(
                "You are a help desk verification agent. Verify that the following request, categorized as '{category}', "
                "contains all the necessary information. If any required information is missing, list it; otherwise, reply with 'Verified'.\n\n"
                "Request Details: {details}\n\n"
                "Verification Outcome:"
            )
        )
        self.verification_chain = LLMChain(llm=self.llm, prompt=self.verification_prompt)

    def verify_request(self, details: str, category: str) -> str:
        response = self.verification_chain.run(details=details, category=category)
        return response.strip()


# ================================================================
# Specialized Agents: Handle specific IT support tasks.
# ================================================================
class PasswordResetAgent:
    def process_request(self, details: str) -> str:
        # In a real system, this would trigger a password reset workflow.
        return (
            "Password reset request has been processed. "
            "A reset link has been sent to your registered email address."
        )

class VDIResourceIncreaseAgent:
    def process_request(self, details: str) -> str:
        # In production, this might trigger a resource allocation workflow.
        return (
            "VDI resource increase request has been processed. "
            "Your VDI resources will be updated shortly."
        )


# ================================================================
# Help Desk System Coordinator: Orchestrates the entire workflow.
# ================================================================
class HelpDeskSystem:
    def __init__(self, llm):
        self.planning_agent = PlanningRoutingAgent(llm)
        self.verification_agent = VerificationAgent(llm)
        self.password_reset_agent = PasswordResetAgent()
        self.vdi_agent = VDIResourceIncreaseAgent()

    @staticmethod
    def parse_classification_response(response: str):
        """
        Expected response format:
            Category: <category>
            Missing: <missing details or 'None'>
        """
        category = "Other IT Support"
        missing = "None"
        for line in response.splitlines():
            if line.lower().startswith("category:"):
                category = line.split(":", 1)[1].strip()
            elif line.lower().startswith("missing:"):
                missing = line.split(":", 1)[1].strip()
        return category, missing

    def handle_query(self, query: str) -> str:
        # --- Step 1: Planning & Routing (Classification) ---
        classification_response = self.planning_agent.process_query(query)
        print("Classification Response:")
        print(classification_response)
        category, missing = self.parse_classification_response(classification_response)

        # If required information is missing, notify the user.
        if missing.lower() != "none":
            return f"Missing Information: {missing}. Please provide the missing details and try again."

        # --- Step 2: Verification (Single Check) ---
        verification_outcome = self.verification_agent.verify_request(query, category)
        print("Verification Outcome:")
        print(verification_outcome)
        if "missing" in verification_outcome.lower():
            return f"Verification Issue: {verification_outcome}. Please provide complete details."

        # --- Step 3: Intelligent Routing to Specialized Agent ---
        if category.lower() == "password reset":
            resolution = self.password_reset_agent.process_request(query)
        elif category.lower() == "vdi resource increase":
            resolution = self.vdi_agent.process_request(query)
        else:
            resolution = (
                "Your request has been forwarded to our general IT support team. "
                "They will get back to you shortly."
            )

        # --- Step 4: Final Summary by Planning & Routing Agent ---
        final_summary = self.planning_agent.generate_final_summary(query, category, verification_outcome, resolution)
        return final_summary


# ================================================================
# Main Application: Set up Azure OpenAI and run the help desk system.
# ================================================================
def main():
    # Set up Azure OpenAI parameters.
    # You can either set these in your environment or replace the placeholders below.
    azure_openai_api_base = os.environ.get("AZURE_OPENAI_API_BASE", "https://<your-resource>.openai.azure.com/")
    azure_openai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-03-15-preview")
    deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "your-deployment-name")
    model_name = os.environ.get("AZURE_OPENAI_MODEL_NAME", "gpt-35-turbo")

    # Initialize the Azure OpenAI Chat model via LangChain.
    llm = AzureChatOpenAI(
        deployment_name=deployment_name,
        model_name=model_name,
        temperature=0.2,
        azure_api_base=azure_openai_api_base,
        azure_api_version=azure_openai_api_version,
    )

    # Create the help desk system instance.
    help_desk = HelpDeskSystem(llm)

    print("Welcome to the Help Desk Bot powered by Azure OpenAI.")
    print("Please describe your issue below:")
    user_query = input("> ")

    # Process the query through the system and display the final summary.
    final_summary = help_desk.handle_query(user_query)
    print("\nFinal Summary:")
    print(final_summary)


if __name__ == "__main__":
    main()
