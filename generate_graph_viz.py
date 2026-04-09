"""
Script xuat do thi LangGraph ra file PNG co day du edges.
Chay: python generate_graph_viz.py

Ly do viet tay Mermaid:
  app.get_graph().draw_mermaid() khong capture duoc conditional edges
  dang function reference (router_start, router_after_brief) nen output
  chi co nodes ma KHONG CO edges.
  Giai phap: viet dung cau truc that cua graph.py + render qua mermaid.ink API.
"""
import os
import base64
import requests
from dotenv import load_dotenv
load_dotenv()

# ==========================================
# 1. Dinh nghia Mermaid DUNG VOI GRAPH.PY
# ==========================================
MERMAID_CODE = """graph TD
    START(["▶ __start__"])
    parse_attachment["parse_attachment"]
    prioritize_notification["prioritize_notification"]
    summarize_brief["summarize_brief"]
    summarize_detailed["summarize_detailed"]
    scheduler["scheduler"]
    handle_feedback["handle_feedback"]
    END(["⏹ __end__"])

    START -->|"attachments != empty"| parse_attachment
    START -->|"attachments == empty"| prioritize_notification
    parse_attachment --> prioritize_notification
    prioritize_notification --> summarize_brief
    summarize_brief -->|"user_request_detail = False"| END
    summarize_brief -->|"user_request_detail = True"| summarize_detailed
    summarize_detailed --> scheduler
    scheduler --> handle_feedback
    handle_feedback --> END

    classDef startEnd fill:#1A5276,color:#fff,stroke:#154360,stroke-width:2px,rx:20
    classDef phase1 fill:#EAFAF1,stroke:#27AE60,stroke-width:2px,color:#145A32,rx:6
    classDef phase2 fill:#EBF5FB,stroke:#2E86C1,stroke-width:2px,color:#1B4F72,rx:6

    class START,END startEnd
    class parse_attachment,prioritize_notification,summarize_brief phase1
    class summarize_detailed,scheduler,handle_feedback phase2
"""

# ==========================================
# 2. Luu file .mmd de xem thu cong
# ==========================================
with open("graph_diagram.mmd", "w", encoding="utf-8") as f:
    f.write(MERMAID_CODE)
print("[OK] Da luu: graph_diagram.mmd")

# ==========================================
# 3. Render PNG qua mermaid.ink REST API
# ==========================================
# Su dung theme 'neutral' de text ro net hon
encoded = base64.urlsafe_b64encode(MERMAID_CODE.encode("utf-8")).decode("utf-8")
url = f"https://mermaid.ink/img/{encoded}?type=png&theme=neutral"

print(f"Dang render PNG voi mau moi (High Contrast) ...")
try:
    resp = requests.get(url, timeout=20)
    if resp.status_code == 200:
        with open("graph_diagram.png", "wb") as f:
            f.write(resp.content)
        print("[OK] Da luu: graph_diagram.png")
        print("     => Graph moi da duoc cap nhat voi mau sac ro rang hon!")
    else:
        print(f"[LOI] HTTP {resp.status_code}")
except requests.exceptions.RequestException as e:
    print(f"[LOI] Khong ket noi duoc: {e}")
