import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Energy Grid: Quick Rush", layout="wide")

# --- GLOBAL SYNCHRONISED CLOUD STORAGE ---
@st.cache_resource
def get_game_engine():
    return {
        "round": 1,
        "phase": "Action Phase",  # Action Phase, Results Phase, Game Over
        "event": "Awaiting Round 1 player investments...",
        "players": {}
    }

db = get_game_engine()

# Global Events Matrix (One rolled randomly per round)
EVENTS = [
    {"name": "Green Subsidy 🌿", "fossil": 0, "green": 20000, "desc": "$20,000 bonus for every Green Project owned!"},
    {"name": "Oil Spike 🛢️", "fossil": 20000, "green": 0, "desc": "$20,000 bonus for every Fossil Project owned!"},
    {"name": "Carbon Tax 💸", "fossil": -15000, "green": 0, "desc": "Carbon tax! Lose $15,000 per Fossil Project owned."},
    {"name": "Dunkelflaute ☁️", "fossil": 10000, "green": -10000, "desc": "No sun or wind! Green yields -$10,000; Fossil steps up with +$10,000."},
    {"name": "Market Boom 📈", "fossil": 15000, "green": 15000, "desc": "High power demand! All projects pay out an extra $15,000."}
]

st.title("⚡ Energy Grid: Quick Rush")

# --- NAVIGATION SYSTEM ---
st.sidebar.title("🎮 Network Portal")
role = st.sidebar.selectbox("Your Role:", ["Choose...", "Game Master (Host)", "Player Terminal"])

if st.sidebar.button("🔄 Refresh Data & Sync Screen", type="primary", use_container_width=True):
    st.rerun()

if role == "Choose...":
    st.info("### Welcome!\nSelect your role in the sidebar to log into the energy grid.")
    st.stop()

# ==========================================
# 👑 VIEW: GAME MASTER DASHBOARD
# ==========================================
if role == "Game Master (Host)":
    st.header("🕹️ Game Master Control Center")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Round", f"{min(db['round'], 5)} / 5")
    m2.metric("Active Stage", db["phase"])
    m3.metric("Connected Players", len(db["players"]))
    
    st.divider()
    
    # Live Player Readiness Tracking
    total_players = len(db["players"])
    ready_players = sum(1 for p in db["players"].values() if p["round_submitted"])
    
    st.subheader("📊 Round Progress Tracker")
    st.progress(ready_players / max(total_players, 1), text=f"{ready_players} out of {total_players} players have locked in their choices.")

    # Game Master State Machine
    if db["phase"] == "Action Phase" and db["round"] <= 5:
        st.warning("Ensure players have locked their choices before rolling, or force the roll to keep things moving.")
        if st.button("🎲 Roll Global Event & Calculate Results", type="primary", use_container_width=True):
            # 1. Roll Random Event
            evt = random.choice(EVENTS)
            db["event"] = f"{evt['name']} — {evt['desc']}"
            
            # 2. Process All Player Ledgers Automatically
            for name, p in db["players"].items():
                # Process active building choices if they didn't explicitly submit (safety default)
                if not p["round_submitted"]:
                    p["round_submitted"] = True # Force pass if idle
                
                # Base operational earnings
                base_income = (p["fossil_count"] * 15000) + (p["green_count"] * 10000)
                # Event modifier impacts
                event_modifier = (p["fossil_count"] * evt["fossil"]) + (p["green_count"] * evt["green"])
                
                p["last_payout"] = base_income + event_modifier
                p["cash"] += p["last_payout"]
                
                # Dynamic Stability Recalculation
                total_projects = p["fossil_count"] + p["green_count"]
                if total_projects > 0:
                    p["stability"] = int((p["green_count"] / total_projects) * 100)
                else:
                    p["stability"] = 50
                    
                # Floor check for cash balances
                if p["cash"] = 20000:  # ✅ Fixed syntax validation check
                        p["cash"] -= 20000
                        p["fossil_count"] += 1
                        p["round_submitted"] = True
                        st.rerun()
                    else:
                        st.error("Insufficient liquidity to complete investment transaction.")
                elif "Renewables" in choice or "Renewable" in choice:
                    if p["cash"] >= 30000:  # ✅ Fixed syntax validation check
                        p["cash"] -= 30000
                        p["green_count"] += 1
                        p["round_submitted"] = True
                        st.rerun()
                    else:
                        st.error("Insufficient liquidity to complete investment transaction.")
                else:
                    # Pass condition
                    p["round_submitted"] = True
                    st.rerun()

    elif db["phase"] == "Results Phase":
        st.subheader("📊 Round Financial Statement Notification")
        r1, r2 = st.columns(2)
        r1.metric("Automated Cash Earnings Applied", f"+${p['last_payout']:,}")
        with r2:
            st.warning(f"Global Impact Event Resolution")
            st.write(db["event"])
        st.caption("Review your changes above. Once the Game Master unblocks the pipeline for the next turn, hit 'Refresh' in your sidebar.")
        
    elif db["phase"] == "Game Over":
        st.success("Game Over! Review your final standing in the main ledger below.")

# ==========================================
# 📊 CENTRAL SYNCHRONISED MULTIPLAYER SCOREBOARD
# ==========================================
st.divider()
st.subheader("📊 Central Live Grid Scoreboard (Visible to All)")

if not db["players"]:
  st.caption("Awaiting player node terminal connections...")
else:
# Compile the active dictionary values into a DataFrame format
df = pd.DataFrame.from_dict(db["players"], orient="index").reset_index().rename(columns={"index": "Player Profile"})
# Sort and score changes depending on phase state
if db["phase"] == "Game Over":
df = df.sort_values(by="final_score", ascending=False)
st.balloons()
else:
df = df.sort_values(by="cash", ascending=False)
# Format numeric fields cleanly for presentation readability
df["cash"] = df["cash"].apply(lambda x: f"${x:,}")
df["stability"] = df["stability"].apply(lambda x: f"{x}%")
df["last_payout"] = df["last_payout"].apply(lambda x: f"${x:,}")
df["round_submitted"] = df["round_submitted"].apply(lambda x: "✅ Locked" if x else "⏳ Building...")
st.dataframe(
df,
column_config={
"Player Profile": "Player / Grid ID",
"cash": "Available Cash Reserves",
"stability": "Grid Stability Score",
"fossil_count": "🛢️ Fossil Fleet",
"green_count": "🌿 Renewable Fleet",
"last_payout": "Latest Income Yield",
"round_submitted": "Round Input Status",
"final_score": "🎯 Final Metrics Score"
},
hide_index=True,
use_container_width=True
)
