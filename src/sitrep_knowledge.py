# src/sitrep_knowledge.py
# Project SITREP - Internal Resource Hub Knowledge Base
#
# HOW TO USE:
#   1. Go to each page of your Google Intranet (Google Sites) for Project SITREP
#   2. Copy the page content (Ctrl+A, Ctrl+C on the page — or copy section by section)
#   3. Paste it into the appropriate section below, replacing the placeholder text
#   4. Redeploy / restart the Streamlit app for changes to take effect
#
# TIP: You can also update the knowledge base live from the Admin tab in the chat app
#      without redeploying — those changes persist for the current session only.
# ──────────────────────────────────────────────────────────────────────────────

SITREP_SYSTEM_PROMPT = """\
You are the SITREP Assistant, an internal AI helper for Project SITREP — our company's \
internal resource hub. Your job is to answer employee questions based on the content of \
the SITREP intranet site.

Guidelines:
- Answer only from the knowledge base provided. If something isn't covered, say so and \
  suggest the employee contact the relevant team directly.
- Be concise, friendly, and professional.
- Use bullet points for multi-step processes or lists.
- Never make up policies, links, names, or dates that are not in the knowledge base.
- If an employee asks about something sensitive (HR, personal data, etc.), direct them \
  to the appropriate contact instead of speculating.
"""

# ──────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE
# Paste content from each Google Sites page into the relevant section below.
# Each section uses a plain-text block.  Add as many sections as you need.
# ──────────────────────────────────────────────────────────────────────────────

SITREP_KNOWLEDGE_BASE = """\
=== PROJECT SITREP OVERVIEW ===
[Paste your "About SITREP" or homepage content here]

Example:
Project SITREP is the internal resource hub for [Company Name]. It serves as the single
source of truth for company policies, team directories, project updates, and operational
resources. All employees can access SITREP via our Google Intranet at [internal URL].


=== TEAM DIRECTORY ===
[Paste team/department directory content here]

Example:
- Quality & Regulatory: Contact quality@company.com
- Engineering: Contact engineering@company.com
- HR: Contact hr@company.com


=== POLICIES & PROCEDURES ===
[Paste policy summaries or links here]

Example:
- Time Off Policy: Employees accrue X days PTO per year. Requests submitted via [tool].
- Remote Work Policy: ...
- Expense Reimbursement: Submit receipts within 30 days via [tool].


=== ONBOARDING RESOURCES ===
[Paste onboarding guides, checklists, or new-hire information here]


=== TOOLS & SYSTEMS ===
[List internal tools, how to access them, and who to contact for support]

Example:
- JIRA: Project tracking. Access at [URL]. Contact IT for account setup.
- Confluence: Documentation. Access at [URL].
- Slack: Internal messaging. Download at slack.com and use [workspace].


=== FAQS ===
[Paste your most common internal FAQs here]

Example:
Q: How do I submit a help desk ticket?
A: Go to [IT portal URL] and click "New Ticket."

Q: Where do I find the org chart?
A: The org chart is on the SITREP homepage under "Our Team."


=== ANNOUNCEMENTS & UPDATES ===
[Paste recent announcements or update summaries here]

"""

# ──────────────────────────────────────────────────────────────────────────────
# Helper — build the full context string to pass to the AI
# ──────────────────────────────────────────────────────────────────────────────

def get_sitrep_context(extra_content: str = "") -> str:
    """Return the full knowledge-base string to inject into AI messages."""
    base = SITREP_KNOWLEDGE_BASE.strip()
    if extra_content and extra_content.strip():
        base += "\n\n=== ADDITIONAL CONTENT (Admin-added) ===\n" + extra_content.strip()
    return base
