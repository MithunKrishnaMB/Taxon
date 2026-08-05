import json
import uuid
from typing import Annotated, TypedDict
# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, SystemMessage
# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
# pyrefly: ignore [missing-import]
from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice, ImsReconciliation, ReconStatus
from app.domain.ims_recon.repositories import ErpInvoiceRepository, ImsReconciliationRepository


# 1. Define the "Train Carriage" (State) that passes between LangGraph stations
class AgentState(TypedDict):
    erp_doc_no: str
    erp_amount: float
    gstr_supplier: str
    similarity_score: float
    cgst_17_5_flag: bool
    status: ReconStatus
    reasoning: str


class ImsReconciliationService:
    def __init__(
        self,
        erp_repo: ErpInvoiceRepository,
        recon_repo: ImsReconciliationRepository,
    ):
        self.erp_repo = erp_repo
        self.recon_repo = recon_repo

        # Initialize Google Gemini for embeddings (1536-dim equivalent) and reasoning
        self.embedder = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self.workflow = self._build_langgraph_agent()

    def _build_langgraph_agent(self):
        """Build the LangGraph state machine for CGST Section 17(5) legal compliance."""
        
        # Node 1: Evaluate Legal Compliance under CGST Act Section 17(5)
        def evaluate_cgst_rules(state: AgentState) -> AgentState:
            prompt = (
                f"Evaluate this GST invoice for Blocked Input Tax Credit under CGST Act Section 17(5).\n"
                f"Invoice Details: Supplier='{state['gstr_supplier']}', Doc='{state['erp_doc_no']}', Amount='{state['erp_amount']}'.\n"
                "Rules: Credits are BLOCKED (True) for motor vehicles, catering/food, beverages, beauty treatment and employee gifts.\n"
                "Respond strictly in JSON: {\"is_blocked\": true/false, \"reason\": \"string\"}"
            )
            response = self.llm.invoke([
                SystemMessage(content="You are an expert Indian Chartered Accountant specializing in GST compliance."),
                HumanMessage(content=prompt),
            ])
            
            try:
                # Parse structured JSON from Gemini's response
                content = response.content.strip("` \njson")
                data = json.loads(content)
                state["cgst_17_5_flag"] = bool(data.get("is_blocked", False))
                state["reasoning"] = str(data.get("reason", "Evaluated by AI."))
            except Exception:
                state["cgst_17_5_flag"] = False
                state["reasoning"] = "Manual verification required due to AI parsing ambiguity."
                
            return state

        # Node 2: Decide Final Reconciliation Status
        def make_decision(state: AgentState) -> AgentState:
            if state["cgst_17_5_flag"]:
                state["status"] = ReconStatus.REJECT  # Blocked credit cannot be claimed
            elif state["similarity_score"] >= 0.92:
                state["status"] = ReconStatus.ACCEPT  # High vector similarity & legal
            else:
                state["status"] = ReconStatus.PENDING # Moderate similarity -> human CA review
            return state

        # Connect the Train Tracks
        graph = StateGraph(AgentState)
        graph.add_node("evaluate_legal", evaluate_cgst_rules)
        graph.add_node("make_decision", make_decision)
        
        graph.set_entry_point("evaluate_legal")
        graph.add_edge("evaluate_legal", "make_decision")
        graph.add_edge("make_decision", END)
        
        return graph.compile()

    async def reconcile_single_invoice(
        self, tenant_id: uuid.UUID, erp_invoice: ErpInvoice
    ) -> ImsReconciliation:
        """Run vector matching and agentic compliance evaluation for one ERP invoice."""
        
        # 1. Execute HNSW Cosine Similarity Search in Postgres
        matches = await self.erp_repo.find_similar_gstr2b(
            tenant_id=tenant_id,
            embedding=erp_invoice.vector_embed,
            top_k=1,
            similarity_threshold=0.82,
        )

        best_gstr, similarity_score = (
            (matches[0][0], matches[0][1]) if matches else (None, 0.0)
        )

        # 2. Run LangGraph Legal Evaluation
        initial_state: AgentState = {
            "erp_doc_no": erp_invoice.doc_no,
            "erp_amount": float(erp_invoice.amount),
            "gstr_supplier": best_gstr.supplier_gstin if best_gstr else "NO_MATCH",
            "similarity_score": similarity_score,
            "cgst_17_5_flag": False,
            "status": ReconStatus.PENDING,
            "reasoning": "",
        }

        final_state = await self.workflow.ainvoke(initial_state)

        # 3. Save the reconciliation decision via Repository
        recon = await self.recon_repo.create({
            "erp_id": erp_invoice.id,
            "gstr2b_id": best_gstr.id if best_gstr else None,
            "status": final_state["status"],
            "cgst_17_5_flag": final_state["cgst_17_5_flag"],
            "confidence_score": similarity_score,
        })
        return recon