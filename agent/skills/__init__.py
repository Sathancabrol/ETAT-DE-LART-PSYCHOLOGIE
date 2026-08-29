"""Import de toutes les compétences pour déclencher l'enregistrement."""

from agent.skills import search_literature    # noqa: F401
from agent.skills import enrich_doi           # noqa: F401
from agent.skills import citation_metrics     # noqa: F401
from agent.skills import deduplicate          # noqa: F401
from agent.skills import validate_entries     # noqa: F401
from agent.skills import trust_scoring        # noqa: F401
from agent.skills import bias_assessment      # noqa: F401
from agent.skills import prisma_flow          # noqa: F401
from agent.skills import synthesize           # noqa: F401
from agent.skills import visualize            # noqa: F401
from agent.skills import monitor_watch        # noqa: F401
