"""
Script to generate the Amazon Developer Hackathon Submission PDF for Alexa Warranty Vault.
"""
import base64
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
COVER_IMG_PATH = BASE_DIR / "cover.jpg"
HTML_OUTPUT_PATH = BASE_DIR / "hackathon_submission_temp.html"
PDF_OUTPUT_PATH = BASE_DIR / "Alexa_Warranty_Vault_Amazon_Hackathon_Submission.pdf"

# Encode cover image as base64
cover_b64 = ""
if COVER_IMG_PATH.exists():
    cover_b64 = base64.b64encode(COVER_IMG_PATH.read_bytes()).decode("ascii")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Alexa Warranty Vault - Amazon Developer Hackathon Submission</title>
  <style>
    @page {{
      size: A4;
      margin: 14mm 14mm 14mm 14mm;
      @bottom-right {{
        content: counter(page);
      }}
    }}
    
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #0f172a;
      background-color: #ffffff;
      line-height: 1.55;
      font-size: 13.5px;
    }}
    
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #00caff;
      padding-bottom: 12px;
      margin-bottom: 16px;
    }}
    
    .title-block h1 {{
      font-size: 24px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.5px;
    }}
    
    .title-block .tagline {{
      font-size: 13px;
      color: #0284c7;
      font-weight: 600;
      margin-top: 2px;
    }}
    
    .badge-container {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 8px;
    }}
    
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    
    .badge-primary {{
      background: #e0f2fe;
      color: #0369a1;
      border: 1px solid #7dd3fc;
    }}
    
    .badge-mini {{
      background: #fef3c7;
      color: #b45309;
      border: 1px solid #fcd34d;
    }}
    
    .badge-license {{
      background: #dcfce7;
      color: #15803d;
      border: 1px solid #86efac;
    }}
    
    .banner-container {{
      width: 100%;
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 16px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      border: 1px solid #e2e8f0;
    }}
    
    .banner-container img {{
      width: 100%;
      height: auto;
      display: block;
    }}
    
    .meta-box {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-left: 4px solid #00caff;
      border-radius: 6px;
      padding: 10px 14px;
      margin-bottom: 16px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      font-size: 12px;
    }}
    
    .meta-item strong {{
      color: #334155;
    }}
    
    .meta-item a {{
      color: #0284c7;
      text-decoration: none;
      word-break: break-all;
    }}
    
    h2 {{
      font-size: 16px;
      font-weight: 700;
      color: #0f172a;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
      margin-top: 18px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    
    h3 {{
      font-size: 13.5px;
      font-weight: 700;
      color: #1e293b;
      margin-top: 10px;
      margin-bottom: 4px;
    }}
    
    p {{
      margin-bottom: 8px;
      color: #334155;
    }}
    
    ul {{
      margin-left: 18px;
      margin-bottom: 8px;
      color: #334155;
    }}
    
    li {{
      margin-bottom: 4px;
    }}
    
    .highlight-card {{
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-left: 4px solid #22c55e;
      border-radius: 6px;
      padding: 10px 14px;
      margin: 12px 0;
    }}
    
    .challenge-card {{
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-left: 4px solid #f59e0b;
      border-radius: 6px;
      padding: 10px 14px;
      margin: 12px 0;
    }}
    
    .table-container {{
      width: 100%;
      margin: 10px 0;
      border-collapse: collapse;
      font-size: 12px;
    }}
    
    .table-container th, .table-container td {{
      border: 1px solid #cbd5e1;
      padding: 6px 10px;
      text-align: left;
    }}
    
    .table-container th {{
      background-color: #f1f5f9;
      font-weight: 700;
      color: #1e293b;
    }}
    
    .table-container tr:nth-child(even) {{
      background-color: #f8fafc;
    }}
    
    .code-pill {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 11px;
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      padding: 2px 5px;
      border-radius: 4px;
      color: #0369a1;
    }}
    
    .architecture-box {{
      background: #0f172a;
      color: #f8fafc;
      padding: 12px;
      border-radius: 6px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 11px;
      line-height: 1.45;
      margin: 10px 0;
      overflow-x: auto;
    }}
    
    .page-break {{
      page-break-before: always;
    }}
    
    .avoid-break {{
      page-break-inside: avoid;
    }}
    
    .footer-note {{
      font-size: 11px;
      color: #64748b;
      text-align: center;
      margin-top: 20px;
      border-top: 1px solid #e2e8f0;
      padding-top: 8px;
    }}
  </style>
</head>
<body>

  <!-- HEADER -->
  <div class="header">
    <div class="title-block">
      <h1>Alexa Warranty Vault</h1>
      <div class="tagline">Voice-First Home Appliance Companion & Grounded FastMCP Server</div>
      <div class="badge-container">
        <span class="badge badge-primary">Primary Track: Alexa+</span>
        <span class="badge badge-mini">Mini Challenge: Open Source</span>
        <span class="badge badge-license">License: MIT Open Source</span>
      </div>
    </div>
    <div style="text-align: right; font-size: 11.5px; color: #64748b;">
      <strong>Amazon Developer Hackathon</strong><br>
      Submission Dossier & Specification
    </div>
  </div>

  <!-- COVER BANNER -->
  {"<div class='banner-container'><img src='data:image/jpeg;base64," + cover_b64 + "' alt='Alexa Warranty Vault Cover Banner'></div>" if cover_b64 else ""}

  <!-- SUBMISSION METADATA -->
  <div class="meta-box">
    <div class="meta-item"><strong>GitHub Username:</strong> aaryansingh200617-cyber</div>
    <div class="meta-item"><strong>License:</strong> MIT Open Source License (included in root)</div>
    <div class="meta-item"><strong>Repository URL:</strong> <a href="https://github.com/aaryansingh200617-cyber/Alexa-Warranty-Vault">https://github.com/aaryansingh200617-cyber/Alexa-Warranty-Vault</a></div>
    <div class="meta-item"><strong>Contribution Branch:</strong> <a href="https://github.com/aaryansingh200617-cyber/Alexa-Warranty-Vault/tree/main">main (committed & pushed during hackathon)</a></div>
  </div>

  <!-- SECTION 1: EXECUTIVE SUMMARY -->
  <div class="avoid-break">
    <h2>1. Executive Summary & Inspiration</h2>
    <p>
      Every household manages dozens of appliances and electronics—from dishwashers and refrigerators to smart TVs, laptops, and coffee makers. When a device malfunctions, homeowners face a frustrating ordeal: paper receipts are lost, digital invoices are buried in email archives, warranty deadlines pass unnoticed, and filing a manufacturer claim requires digging for serial numbers and writing tedious formal emails.
    </p>
    <p>
      Inspired by the natural, ambient voice intelligence of <strong>Amazon Alexa</strong> (<em>"Your Home, Your Love"</em>), <strong>Alexa Warranty Vault</strong> was engineered as an intelligent, voice-first home appliance companion. It proactively tracks warranty expirations, monitors coverage health with visual countdowns, and autonomously drafts airtight, professional warranty claim emails the moment an appliance exhibits issues.
    </p>
  </div>

  <!-- SECTION 2: TRACK 1 ALIGNMENT (ALEXA+) -->
  <div class="highlight-card avoid-break">
    <h3 style="color: #15803d; margin-top: 0; font-size: 14px;">🎯 Primary Track Alignment: Alexa+</h3>
    <p style="font-size: 12.5px; margin-bottom: 6px;">
      <em>"Build a self-hosted MCP server (spec 2025-11-25 or later, Streamable HTTP) or an Agent Skill. MCP is the open standard that powers Alexa+ integrations. Build a simulated Alexa+ experience in a web app using your preferred agentic tool."</em>
    </p>
  </div>

  <div class="avoid-break">
    <p><strong>Alexa Warranty Vault directly satisfies and demonstrates the Alexa+ track requirements through two core pillars:</strong></p>
    
    <h3>A. Self-Hosted Model Context Protocol (FastMCP) Server</h3>
    <ul>
      <li><strong>Standard Compliance:</strong> Implements a dedicated FastMCP server over <strong>Streamable HTTP</strong> (Server-Sent Events / SSE) at endpoint <span class="code-pill">/mcp</span> compliant with the modern MCP specification.</li>
      <li><strong>Deterministic Anti-Hallucination Grounding:</strong> Alexa+ agents cannot guess purchase dates or fabricate coverage terms. Every warranty duration, status badge, and email draft is computed strictly through executable MCP tools connected to an ACID-compliant SQLite datastore.</li>
      <li><strong>Published MCP Tool Catalog:</strong></li>
    </ul>

    <table class="table-container">
      <thead>
        <tr>
          <th>Tool Name</th>
          <th>Input Parameters</th>
          <th>Description & Execution Logic</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><span class="code-pill">log_purchase</span></td>
          <td><span class="code-pill">item_name</span>, <span class="code-pill">category</span>, <span class="code-pill">price</span>, <span class="code-pill">purchase_date</span>, <span class="code-pill">warranty_months</span>, <span class="code-pill">retailer</span>, <span class="code-pill">serial_number</span></td>
          <td>Registers appliance purchases, stores receipt metadata, and automatically calculates future expiration dates.</td>
        </tr>
        <tr>
          <td><span class="code-pill">check_warranty</span></td>
          <td><span class="code-pill">query</span> (e.g., "dishwasher", "Sony TV")</td>
          <td>Queries active coverage, computes days remaining until expiry, and returns status: <em>active</em>, <em>expiring_soon</em>, or <em>expired</em>.</td>
        </tr>
        <tr>
          <td><span class="code-pill">expiring_soon</span></td>
          <td><span class="code-pill">days_ahead</span> (default: 30)</td>
          <td>Scans household inventory for warranties nearing their expiration window to trigger proactive ambient alerts.</td>
        </tr>
        <tr>
          <td><span class="code-pill">draft_claim</span></td>
          <td><span class="code-pill">product_name</span>, <span class="code-pill">issue_description</span></td>
          <td>Autonomously synthesizes a formal manufacturer claim email pre-filled with order ID, purchase date, serial number, and symptom analysis.</td>
        </tr>
      </tbody>
    </table>

    <h3>B. Simulated Alexa+ Web Experience</h3>
    <ul>
      <li><strong>Voice-First Alexa Interaction:</strong> Integrates the browser Web Speech API for voice recognition and fine-tuned natural Alexa speech synthesis, delivering hands-free assistance.</li>
      <li><strong>Hybrid Dual-Engine Architecture:</strong>
        <ul>
          <li><em>Online AI Mode:</em> Connects an LLM agent (Groq / OpenRouter) to the FastMCP server via tool-calling loops.</li>
          <li><em>Offline Edge Mode:</em> Built-in deterministic regex and date-engine for 100% private, zero-latency local operation without requiring any API keys or internet connection.</li>
        </ul>
      </li>
      <li><strong>Segmented Sliding Toggle:</strong> Seamlessly switches between Online AI and Offline Mode with real-time health telemetry (<span class="code-pill">/api/health</span>).</li>
    </ul>
  </div>

  <div class="page-break"></div>

  <!-- SECTION 3: MINI CHALLENGE ALIGNMENT (OPEN SOURCE) -->
  <div class="challenge-card avoid-break">
    <h3 style="color: #b45309; margin-top: 0; font-size: 14px;">🌟 Mini Challenge Alignment: Open Source</h3>
    <p style="font-size: 12.5px; margin-bottom: 6px;">
      <em>"Ship a new, additional open-source project (include an open-source license) or a contribution during the hackathon window. Include contribution URL, repo URL, GitHub username, and a short description of what you did, how it works, and why it matters."</em>
    </p>
  </div>

  <div class="avoid-break">
    <table class="table-container">
      <tbody>
        <tr>
          <td style="width: 25%; font-weight: 700;">GitHub Username</td>
          <td><span class="code-pill">aaryansingh200617-cyber</span></td>
        </tr>
        <tr>
          <td style="font-weight: 700;">Repository URL</td>
          <td><a href="https://github.com/aaryansingh200617-cyber/Alexa-Warranty-Vault">https://github.com/aaryansingh200617-cyber/Alexa-Warranty-Vault</a></td>
        </tr>
        <tr>
          <td style="font-weight: 700;">Contribution Branch</td>
          <td><a href="https://github.com/aaryansingh200617-cyber/Alexa-Warranty-Vault/tree/main">https://github.com/aaryansingh200617-cyber/Alexa-Warranty-Vault/tree/main</a></td>
        </tr>
        <tr>
          <td style="font-weight: 700;">Open-Source License</td>
          <td><strong>MIT License</strong> (Full permissive open-source license committed in root <span class="code-pill">LICENSE</span>)</td>
        </tr>
      </tbody>
    </table>

    <h3>What We Did</h3>
    <p>
      During the Amazon Developer Hackathon window, we developed and publicly released <strong>Alexa Warranty Vault</strong> as an open-source reference project. We authored the complete codebase from scratch, including the FastMCP server, the dual-router FastAPI agent bridge, the responsive React glassmorphic web frontend, Docker configuration, and comprehensive documentation. All development was pushed to GitHub with verified commit authorship by <span class="code-pill">aaryansingh200617-cyber</span> under the permissive MIT License.
    </p>

    <h3>How It Works</h3>
    <p>
      The open-source repository implements a clean, decoupled three-tier architecture:
    </p>
    <ol style="margin-left: 20px; margin-bottom: 8px; color: #334155;">
      <li><strong>Frontend Layer (<span class="code-pill">web-app/</span>):</strong> A React + Vite SPA styled with Tailwind CSS, utilizing Web Speech recognition and synthesis. Deployed with automated CI/CD on Vercel.</li>
      <li><strong>Agent Orchestrator (<span class="code-pill">agent-api/</span>):</strong> A FastAPI service providing dynamic CORS, session history memory, and an intelligent router that routes requests either to an LLM tool-calling loop or to a local rule engine.</li>
      <li><strong>FastMCP Server (<span class="code-pill">mcp-server/</span>):</strong> A standalone FastMCP server over Streamable HTTP with SQLite persistence, exposing standardized MCP tool definitions that any MCP-compliant client or Alexa+ runtime can connect to.</li>
    </ol>

    <h3>Why It Matters</h3>
    <p>
      As voice assistants evolve into agentic systems with the launch of Alexa+, developers need open-source, reproducible blueprints that illustrate how the Model Context Protocol (MCP) bridges generative AI with deterministic external tools. Alexa Warranty Vault demonstrates how to eliminate AI hallucinations in mission-critical applications (such as warranty dates and financial receipts) while ensuring consumer privacy through a reliable offline-first fallback. It serves as an accessible learning template and foundation for the global Alexa developer community.
    </p>
  </div>

  <!-- SECTION 4: ARCHITECTURE DIAGRAM -->
  <div class="avoid-break">
    <h2>2. System Architecture & Data Flow</h2>
    <div class="architecture-box">
+-----------------------------------------------------------------------------------+
|                        ALEXA+ SIMULATED WEB EXPERIENCE                            |
|             React (Vite) + Tailwind CSS + Web Speech API (Voice / Audio)          |
|                   Segmented Mode Toggle: [ ONLINE AI | OFFLINE ]                  |
+-----------------------------------------------------------------------------------+
                                       |
                     REST API / JSON (Over CORS / HTTPS)
                                       v
+-----------------------------------------------------------------------------------+
|                     AGENT ORCHESTRATION LAYER (FastAPI)                           |
|       - Session Memory (Multi-turn conversations)                                 |
|       - Mode Router:                                                              |
|           [Online Mode]  --> LLM Tool-Calling Loop (Groq / OpenRouter / OpenAI)   |
|           [Offline Mode] --> Deterministic Regex & Date Inference Rule Agent      |
+-----------------------------------------------------------------------------------+
                                       |
                   Streamable HTTP (FastMCP Client / SSE)
                                       v
+-----------------------------------------------------------------------------------+
|                     SELF-HOSTED FastMCP SERVER (Port 8765)                        |
|   Tools: log_purchase() | check_warranty() | expiring_soon() | draft_claim()      |
+-----------------------------------------------------------------------------------+
                                       |
                                SQLite Database
                      (Purchases, Warranties, Claims)
    </div>
  </div>

  <!-- SECTION 5: KEY FEATURES & INNOVATION -->
  <div class="avoid-break">
    <h2>3. Key Features & Innovations</h2>
    <ul>
      <li><strong>🎙️ Ambient Voice Interaction:</strong> Hands-free voice recognition and female Alexa voice synthesis tuned to match Amazon Echo's conversational persona.</li>
      <li><strong>🛡️ Universal 1-Click Claim Drafting:</strong> Works for any registered appliance (dishwashers, TVs, blenders, laptops). Extracts serial numbers, order IDs, and generates a structured, professional claim email ready for manufacturer submission.</li>
      <li><strong>⚡ 100% Offline Edge Capability:</strong> Even during internet outages or without an LLM API key, homeowners can slide to Offline mode for zero-latency, private warranty tracking.</li>
      <li><strong>☁️ Cloud-Native Deployment:</strong> Fully containerized with Docker, backend hosted on Render, and frontend deployed on Vercel with automated GitHub CI/CD webhooks.</li>
    </ul>
  </div>

  <!-- SECTION 6: VERIFICATION & SETUP -->
  <div class="avoid-break">
    <h2>4. Quick Verification & Installation</h2>
    <p style="font-size: 12px;"><strong>Clone & Run Locally:</strong></p>
    <div class="architecture-box" style="font-size: 10.5px; padding: 8px 12px;">
# 1. Clone repository
git clone https://github.com/aaryansingh200617-cyber/Alexa-Warranty-Vault.git
cd Alexa-Warranty-Vault

# 2. Run with automated setup script
start.bat            # (Windows: starts MCP Server, Agent API, and Vite web UI)
./start.sh           # (macOS/Linux)
    </div>
  </div>

  <div class="footer-note">
    Alexa Warranty Vault &bull; Built for Amazon Developer Hackathon 2026 &bull; Track: Alexa+ &bull; MIT Open Source License
  </div>

</body>
</html>
"""

# Write HTML file
HTML_OUTPUT_PATH.write_text(html_content, encoding="utf-8")
print(f"HTML generated at: {HTML_OUTPUT_PATH}")

# Convert HTML to PDF using headless Edge
edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not Path(edge_exe).exists():
    edge_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

print(f"Printing PDF using: {edge_exe}")
cmd = [
    edge_exe,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={PDF_OUTPUT_PATH}",
    str(HTML_OUTPUT_PATH)
]

res = subprocess.run(cmd, capture_output=True, text=True)
if PDF_OUTPUT_PATH.exists():
    print(f"SUCCESS: PDF created at: {PDF_OUTPUT_PATH} (Size: {PDF_OUTPUT_PATH.stat().st_size} bytes)")
    # Clean up temporary HTML
    if HTML_OUTPUT_PATH.exists():
        HTML_OUTPUT_PATH.unlink()
else:
    print(f"FAILED: PDF not created. Return code: {res.returncode}")
    print("Stderr:", res.stderr)
