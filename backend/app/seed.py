import asyncio
import random
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, Base, engine
from app.domain.auth.models import Tenant
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice, ImsReconciliation, ReconStatus
from app.domain.tds_align.models import TdsLedger

# Fixed Test Tenant UUID from our earlier tests
TEST_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

# Sample Indian Vendor names to make our UI look realistic
VENDOR_NAMES = [
    "TATA MOTORS LIMITED",
    "INFOSYS TECHNOLOGIES LTD",
    "RELIANCE RETAIL VENTURES",
    "LARSEN & TOUBRO INFOTECH",
    "WIPRO ENTERPRISES INDIA",
    "HDFC BANK LIMITED",
    "BHARTI AIRTEL SERVICES",
    "MAHINDRA & MAHINDRA LTD",
]


def generate_fake_1536_vector() -> list[float]:
    """Generate a random 1536-dimensional normalized vector for HNSW index testing."""
    return [round(random.uniform(-1.0, 1.0), 4) for _ in range(1536)]


def generate_indian_gstin(index: int) -> str:
    """Generate a valid-looking 15-character Indian GST Identification Number."""
    state_code = "32"  # Kerala GST State Code
    pan_part = f"ABCDE{index:04d}F"
    return f"{state_code}{pan_part}1Z5"


async def seed_database(num_invoices: int = 1000, num_tds_ledgers: int = 200):
    """Seed PostgreSQL with realistic tenants, invoices and tripartite ledgers.

    Why we do this:
    Enables us to benchmark HNSW vector search speed and test TanStack Table
    virtualized rendering with thousands of rows.
    """
    print("🌱 Starting High-Performance Database Seeding...")

    async with AsyncSessionLocal() as session:
        # 1. Ensure our Test Tenant exists
        tenant = await session.get(Tenant, TEST_TENANT_ID)
        if not tenant:
            tenant = Tenant(
                id=TEST_TENANT_ID,
                gstin="32ABCDE1234F1Z5",
                legal_name="Taxon Associates Kerala",
            )
            session.add(tenant)
            await session.commit()
            print("✅ Created default Test Tenant.")

        # 2. Seed ERP Invoices and GSTR-2B Invoices in bulk
        print(f"📦 Generating {num_invoices} ERP & GSTR-2B Invoices...")
        for i in range(1, num_invoices + 1):
            amount = Decimal(str(random.randint(10000, 500000)))
            gst_amount = amount * Decimal("0.18")  # 18% standard GST
            vendor_name = random.choice(VENDOR_NAMES)

            # Create internal ERP record
            erp_inv = ErpInvoice(
                id=uuid.uuid4(),
                tenant_id=TEST_TENANT_ID,
                doc_no=f"INV-2026-{i:05d}",
                amount=amount,
                gst_amount=gst_amount,
                vector_embed=generate_fake_1536_vector(),
            )
            session.add(erp_inv)

            # Create matching government GSTR-2B record (80% of the time)
            if random.random() > 0.2:
                gstr_inv = Gstr2bInvoice(
                    id=uuid.uuid4(),
                    tenant_id=TEST_TENANT_ID,
                    supplier_gstin=generate_indian_gstin(i),
                    irn=f"IRN-{uuid.uuid4()}",
                    vector_embed=generate_fake_1536_vector(),
                )
                session.add(gstr_inv)

            # Commit in batches of 250 so we don't overload RAM
            if i % 250 == 0:
                await session.commit()
                print(f"  -> Inserted {i} / {num_invoices} invoice pairs...")

        # 3. Seed Tripartite TDS Ledgers (with intentional 5% anomaly rate)
        print(f"📊 Generating {num_tds_ledgers} TDS Ledger Records...")
        for j in range(1, num_tds_ledgers + 1):
            amount_paid = Decimal(str(random.randint(50000, 1000000)))
            
            # Intentionally create under-deduction anomalies for 5% of records
            is_error = random.random() < 0.05
            tds_rate = Decimal("0.001") if is_error else Decimal("0.02")  # 0.1% vs 2%
            tds_deducted = amount_paid * tds_rate

            ledger = TdsLedger(
                id=uuid.uuid4(),
                tenant_id=TEST_TENANT_ID,
                pan=f"ABCDE{j:04d}F",
                section="194C",
                amount_paid=amount_paid,
                tds_deducted=tds_deducted,
            )
            session.add(ledger)

            if j % 100 == 0:
                await session.commit()

        await session.commit()
        print("🎉 Seeding Complete! Database is ready for UI high-load testing.")


if __name__ == "__main__":
    asyncio.run(seed_database(num_invoices=1000, num_tds_ledgers=200))