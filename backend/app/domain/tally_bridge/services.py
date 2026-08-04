# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, SystemMessage
# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.domain.tally_bridge.circuit_breaker import ExponentialBackoffCircuitBreaker
from app.domain.tally_bridge.models import JobStatus, TallySyncJob
from app.domain.tally_bridge.repositories import TallyJobRepository


class TallyBridgeService:
    def __init__(self, job_repo: TallyJobRepository):
        self.job_repo = job_repo
        self.circuit_breaker = ExponentialBackoffCircuitBreaker()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.0,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    async def process_natural_language_query(
        self, tenant_id: str, prompt_text: str
    ) -> TallySyncJob:
        """Translate English audit queries into Tally Definition Language (TDL) XML."""
        
        # 1. Ask Gemini to generate valid Tally XML
        tdl_xml = self._translate_to_tdl_xml(prompt_text)

        # 2. Check if Tally's local server is safe to talk to
        current_cb_state = self.circuit_breaker.state
        if not self.circuit_breaker.can_execute():
            # Tally is offline! We save the job as QUEUED so a background worker can retry later
            job_status = JobStatus.QUEUED
        else:
            # Safe to execute! In a live app, we would make the HTTP POST to http://localhost:9000 here
            job_status = JobStatus.COMPLETED
            self.circuit_breaker.record_success()

        # 3. Save job state in database
        job = await self.job_repo.create({
            "tenant_id": tenant_id,
            "tdl_query_xml": tdl_xml,
            "status": job_status,
            "circuit_breaker_state": current_cb_state,
        })
        return job

    def _translate_to_tdl_xml(self, query: str) -> str:
        prompt = (
            f"Translate this accounting audit request into valid Tally Definition Language (TDL) XML export envelope:\n"
            f"Request: '{query}'\n"
            "Output ONLY the raw <ENVELOPE>...</ENVELOPE> XML string without Markdown formatting."
        )
        response = self.llm.invoke([
            SystemMessage(content="You are an expert TallyPrime TDL Developer."),
            HumanMessage(content=prompt),
        ])
        return str(response.content).strip("` \nxml")