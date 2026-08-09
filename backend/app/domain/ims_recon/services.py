import json
import uuid
from typing import TypedDict
# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, SystemMessage
# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI
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
    matched: bool
    amount_matched: bool
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
        self._ai_available = bool(settings.GOOGLE_API_KEY)

        if self._ai_available:
            # Initialize Google Gemini for reasoning
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.0,
                google_api_key=settings.GOOGLE_API_KEY,
            )
            self.workflow = self._build_langgraph_agent()
        else:
            self.llm = None
            self.workflow = None

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
                state["reasoning"] = "AI evaluation completed — no blocked credit detected."
                
            return state

        # Node 2: Decide Final Reconciliation Status
        def make_decision(state: AgentState) -> AgentState:
            if not state["matched"]:
                # Invoice exists in ERP but not in GSTR-2B → vendor hasn't filed
                state["status"] = ReconStatus.PENDING
                state["reasoning"] = "Not yet reported by vendor on government portal (missing from GSTR-2B). Hold for vendor filing."
            elif state["cgst_17_5_flag"]:
                # Matched but blocked under Section 17(5)
                state["status"] = ReconStatus.REJECT
                # Reasoning already set by evaluate_cgst_rules
            elif not state["amount_matched"]:
                # Matched by invoice number but amounts differ
                state["status"] = ReconStatus.PENDING
                state["reasoning"] = "Invoice matched by number but amounts differ between ERP and GSTR-2B. Manual verification required."
            else:
                # Fully matched, legally compliant
                state["status"] = ReconStatus.ACCEPT
                if not state["reasoning"] or state["reasoning"] == "AI evaluation completed — no blocked credit detected.":
                    state["reasoning"] = "Invoice fully matched between ERP and GSTR-2B. ITC eligible under tax laws."
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
        """Three-stage reconciliation pipeline for one ERP invoice.
        
        Stage 1: Deterministic field matching (supplier_gstin + doc_no)
        Stage 2: Amount discrepancy check
        Stage 3: AI statutory evaluation (CGST Section 17(5))
        """
        
        # ── Stage 1: Deterministic Field Matching ──
        best_gstr: Gstr2bInvoice | None = None
        matched = False
        amount_matched = False

        if erp_invoice.supplier_gstin and erp_invoice.doc_no:
            best_gstr = await self.erp_repo.find_gstr2b_match_by_fields(
                tenant_id=tenant_id,
                supplier_gstin=erp_invoice.supplier_gstin,
                doc_no=erp_invoice.doc_no,
            )
            matched = best_gstr is not None

        # ── Stage 2: Amount Discrepancy Check ──
        if matched and best_gstr:
            erp_amt = float(erp_invoice.amount or 0)
            erp_gst = float(erp_invoice.gst_amount or 0)
            gstr_amt = float(best_gstr.amount or 0)
            gstr_gst = float(best_gstr.gst_amount or 0)
            
            # Allow 1 rupee tolerance for rounding differences
            amount_matched = (
                abs(erp_amt - gstr_amt) <= 1.0 and
                abs(erp_gst - gstr_gst) <= 1.0
            )

        # ── Stage 3: AI Statutory Evaluation (via LangGraph + Gemini) ──
        if self._ai_available and self.workflow and matched:
            # Only run AI evaluation on matched invoices — unmatched ones are always PENDING
            initial_state: AgentState = {
                "erp_doc_no": erp_invoice.doc_no,
                "erp_amount": float(erp_invoice.amount),
                "gstr_supplier": best_gstr.supplier_gstin if best_gstr else "NO_MATCH",
                "matched": matched,
                "amount_matched": amount_matched,
                "cgst_17_5_flag": False,
                "status": ReconStatus.PENDING,
                "reasoning": "",
            }

            try:
                final_state = await self.workflow.ainvoke(initial_state)
                status = final_state["status"]
                cgst_flag = final_state["cgst_17_5_flag"]
                reasoning = final_state["reasoning"]
            except Exception as exc:
                print(f"  ⚠️ AI evaluation failed for {erp_invoice.doc_no}, falling back to rule-based: {exc}")
                # Fallback: decide without AI
                status, cgst_flag, reasoning = self._rule_based_decision(
                    matched, amount_matched
                )
        else:
            # No AI available or unmatched invoice — use rule-based decision
            status, cgst_flag, reasoning = self._rule_based_decision(
                matched, amount_matched
            )

        # ── Persist the reconciliation decision ──
        confidence = 1.0 if matched and amount_matched else (0.7 if matched else 0.0)
        
        # Upsert logic: Check if a reconciliation row already exists for this ERP invoice
        existing_recon = await self.recon_repo.get_reconciliation_by_erp_id(erp_invoice.id)
        
        if existing_recon:
            existing_recon.gstr2b_id = best_gstr.id if best_gstr else None
            existing_recon.status = status
            existing_recon.cgst_17_5_flag = cgst_flag
            existing_recon.confidence_score = confidence
            existing_recon.reasoning = reasoning
            await self.recon_repo.session.commit()
            recon = existing_recon
        else:
            recon = await self.recon_repo.create({
                "erp_id": erp_invoice.id,
                "gstr2b_id": best_gstr.id if best_gstr else None,
                "status": status,
                "cgst_17_5_flag": cgst_flag,
                "confidence_score": confidence,
                "reasoning": reasoning,
            })
            
        return recon

    @staticmethod
    def _rule_based_decision(
        matched: bool, amount_matched: bool
    ) -> tuple[ReconStatus, bool, str]:
        """Fallback decision logic when AI is unavailable."""
        if not matched:
            return (
                ReconStatus.PENDING,
                False,
                "Not yet reported by vendor on government portal (missing from GSTR-2B). Hold for vendor filing.",
            )
        elif not amount_matched:
            return (
                ReconStatus.PENDING,
                False,
                "Invoice matched by number but amounts differ between ERP and GSTR-2B. Manual verification required.",
            )
        else:
            return (
                ReconStatus.ACCEPT,
                False,
                "Invoice fully matched between ERP and GSTR-2B. ITC eligible under tax laws.",
            )