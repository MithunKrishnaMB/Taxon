# app/domain/tds_align/services.py
# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, SystemMessage
# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.domain.tds_align.ml_engine import TdsAutoencoder
from app.domain.tds_align.models import TdsAnomaly, TdsLedger
from app.domain.tds_align.repositories import TdsAnomalyRepository


class TdsAlignService:
    def __init__(self, anomaly_repo: TdsAnomalyRepository):
        self.anomaly_repo = anomaly_repo
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    async def inspect_ledger_entry(self, ledger: TdsLedger) -> TdsAnomaly:
        """Run Autoencoder anomaly detection and draft a RAG rectification letter if flagged."""
        ratio = float(ledger.tds_deducted / ledger.amount_paid) if ledger.amount_paid > 0 else 0.0
        features = [
            float(ledger.amount_paid) / 100000.0,
            float(ledger.tds_deducted) / 10000.0,
            ratio,
            1.0 if ledger.section == "194C" else 2.0,
        ]

        mse_loss, is_anomalous = TdsAutoencoder.calculate_reconstruction_loss(features)

        draft_text = None
        if is_anomalous:
            # Await our non-blocking draft generator
            draft_text = await self._generate_rectification_draft(ledger, ratio)

        anomaly = await self.anomaly_repo.create({
            "ledger_id": ledger.id,
            "reconstruction_loss": mse_loss,
            "is_anomalous": is_anomalous,
            "rag_rectification_draft": draft_text,
        })
        return anomaly

    async def _generate_rectification_draft(self, ledger: TdsLedger, ratio: float) -> str:
        prompt = (
            f"Draft a concise Indian Income Tax TDS rectification letter to vendor PAN: '{ledger.pan}'.\n"
            f"Issue: Under Section {ledger.section}, expected TDS rate was not matched. "
            f"Paid: INR {ledger.amount_paid}, Deducted: INR {ledger.tds_deducted} (Effective rate: {ratio:.2%}).\n"
            "Request them to revise Form 26Q / TRACES TDS return immediately."
        )
        # Use .ainvoke() so the asyncio event loop remains non-blocking!
        response = await self.llm.ainvoke([
            SystemMessage(content="You are an Indian Tax Attorney drafting statutory communication."),
            HumanMessage(content=prompt),
        ])
        return str(response.content)