// ============================================================
// SITREP Assistant — Google Apps Script backend
// ============================================================
// SETUP STEPS:
//   1. In the Apps Script editor, click the gear (⚙) icon → "Script properties"
//   2. Add a property: Name = OPENAI_API_KEY, Value = sk-...your key...
//   3. Add a property: Name = ADMIN_PASSWORD,  Value = FDSwVSTr8595%$%
//   4. Click Deploy → New deployment → Web app
//      - Execute as: Me
//      - Who has access: Anyone
//   5. Copy the web app URL → paste into Google Sites via Insert → Embed → Embed code
// ============================================================

// ── System prompt ────────────────────────────────────────────
const SITREP_SYSTEM_PROMPT = `You are the SITREP Assistant, an internal AI helper \
for Project SITREP — your company's internal resource hub. Your job is to answer \
employee questions based on the content of the SITREP intranet site.

Guidelines:
- Answer only from the knowledge base provided. If something isn't covered, say so \
  and suggest the employee contact the relevant team directly.
- Be concise, friendly, and professional.
- Use bullet points for multi-step processes or lists.
- Never make up policies, links, names, or dates that are not in the knowledge base.
- If an employee asks about something sensitive (HR, personal data, etc.), direct \
  them to the appropriate contact instead of speculating.`;

// ── Knowledge base ───────────────────────────────────────────
// Paste your Google Sites content here. Replace the [placeholder] lines.
const SITREP_KNOWLEDGE_BASE = `\
=== PROJECT SITREP OVERVIEW ===
[Paste your "About SITREP" or homepage content here]

Example:
Project SITREP is the internal resource hub for [Company Name]. It serves as the
single source of truth for company policies, team directories, project updates, and
operational resources.


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
`;

// ── Serve the chat UI ─────────────────────────────────────────
function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('SITREP Assistant')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ── Called from the browser via google.script.run ─────────────
function getReply(messages) {
  const props = PropertiesService.getScriptProperties();
  const apiKey = props.getProperty('OPENAI_API_KEY');

  if (!apiKey) {
    return {
      error: 'OpenAI API key not configured. ' +
             'Ask your admin to add OPENAI_API_KEY to Script Properties.'
    };
  }

  // Merge base KB with any admin-added content stored in Script Properties
  const extraKb = props.getProperty('EXTRA_KB') || '';
  let fullKb = SITREP_KNOWLEDGE_BASE.trim();
  if (extraKb.trim()) {
    fullKb += '\n\n=== ADDITIONAL CONTENT (Admin-added) ===\n' + extraKb.trim();
  }

  const systemContent =
    SITREP_SYSTEM_PROMPT +
    '\n\n--- KNOWLEDGE BASE ---\n' +
    fullKb +
    '\n--- END KNOWLEDGE BASE ---';

  const payload = JSON.stringify({
    model: 'gpt-4o-mini',
    messages: [{ role: 'system', content: systemContent }, ...messages],
    max_tokens: 1200,
    temperature: 0.3
  });

  const options = {
    method: 'post',
    headers: {
      Authorization: 'Bearer ' + apiKey,
      'Content-Type': 'application/json'
    },
    payload: payload,
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch(
      'https://api.openai.com/v1/chat/completions',
      options
    );
    const json = JSON.parse(response.getContentText());
    if (json.error) return { error: json.error.message };
    return { reply: json.choices[0].message.content };
  } catch (err) {
    return { error: err.toString() };
  }
}

// ── Admin: save extra knowledge base content ──────────────────
function saveExtraKb(content, password) {
  const props = PropertiesService.getScriptProperties();
  const expected = props.getProperty('ADMIN_PASSWORD') || 'sitrep2024';
  if (password !== expected) return { error: 'Incorrect password.' };
  props.setProperty('EXTRA_KB', content || '');
  return { ok: true };
}

// ── Admin: load extra knowledge base content ──────────────────
function getExtraKb(password) {
  const props = PropertiesService.getScriptProperties();
  const expected = props.getProperty('ADMIN_PASSWORD') || 'sitrep2024';
  if (password !== expected) return { error: 'Incorrect password.' };
  return { content: props.getProperty('EXTRA_KB') || '' };
}
