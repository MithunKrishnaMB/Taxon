from app.core.database import Base

# Import all models here to ensure they are registered with SQLAlchemy
# This is crucial to avoid "NoReferencedTableError" when creating foreign keys.

from app.domain.auth.models import Tenant
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice, ImsReconciliation
from app.domain.tds_align.models import TdsAnomaly, TdsLedger
from app.domain.tally_bridge.models import TallySyncJob

# You can add other models from different domains here as they are created.
