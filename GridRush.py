import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Grid Rush Synchronized", layout="wide")

# --- GLOBAL SYNCHRONIZED STORAGE ENGINE ---
# This decorator forces Streamlit to share this exact memory block across ALL connected devices.
@st.cache_resource
def get_global_game_state():
    return {
        "current_round": 0,       # 0 = Setup, 1-6 = Active Rounds
        "current_phase": "Setup",  # Setup, Investment Phase, Shock & Payout Phase
        "last_dice_roll": 0,
        "last_event_name": "Game not started yet.",
        "last_event_desc": "Waiting for the Game Master to initialize the grid.",
        "market_calm_skies": False,
        "players": {}
    }

# Connect to the universal global dictionary
gs = get_global_game_state()

EVENTS_DECK = {
    1: {"name": "Heatwave 🔥", "desc": "High AC usage! If Stability < 50%, you lose $20,000 in grid repairs."},
    2: {"name": "Carbon Tax 💸", "desc": "Government penalty! Pay $5,000 for every Fossil Token you own."},
    3: {"name": "Tech Breakthrough 🚀", "desc": "Green subsidy! Gain $10,000 for every Green Token you own."},
    4: {"name": "Calm Skies ☁️", "desc": "No wind or solar! Green Tokens yield $0 income next round."},
    5: {"name": "Market Boom 📈", "desc": "Energy demand spikes! Everyone receives an extra $15,000."},
    6: {"name": "Grid Failure 💥", "desc": "Major blackout! Grid Stability drops -15% across the board."}
}

# --- APPS HEADER UI ---
st.title("⚡ Grid Rush: Synchronized Multiplayer Panel")
st.caption("All changes made here update live across all connected player devices instantly.")

# --- NAVIGATION ROUTING ---
st.sidebar.title("🕹️ System Portal")
user_role = st.sidebar.selectbox("Select Role:", ["Choose...", "Game Master (Host)", "Player Terminal"])

# Dynamic Auto-Refresh Button (Helps players pull live data manually if needed)
if st.sidebar.button("🔄 Refresh Global Screen Data", use_container_width=True):
    st.rerun()

if user_role == "Choose...":
    st.info("### Welcome!\nSelect **Game Master** if hosting on a main screen/projector, or **Player Terminal** to play on your mobile phone.")
    st.stop()

# ==========================================
# 👑 VIEW: GAME MASTER DASHBOARD
# ==========================================
if user_role == "Game Master (Host)":
    st.header("🕹️ Game Master Control Center")
    
    # Global Telemetry Grid
    m1, m2, m3 = st.columns(3)
    m1.metric("Global Sync Round", f"{gs['current_round']} / 6")
    m2.metric("Universal Phase Tracker", gs["current_phase"])
    m3.metric("Registered Grids", len(gs["players"]))
    
    st.divider()
    st.subheader("⚙️ Global State Override Controls")
    
    # State Machine Flow Control
    if gs["current_round"] == 0:
        st.info("Waiting for all 20 players to type their names on their phones and hit 'Confirm'. Check the scoreboard below to see them join live.")
        if st.button("🚀 Lock Player Sign-ups & Launch Round 1", type="primary", use_container_width=True):
            gs["current_round"] = 1
            gs["current_phase"] = "Investment Phase"
            st.rerun()
            
    elif gs["current_round"] in range(1, 7) and gs["current_phase"] == "Investment Phase":
        st.warning("Ensure all players have completed their investment transactions before rolling.")
        if st.button("🎲 Roll Dice & Process Global Round Payouts", type="primary", use_container_width=True):
            roll = random.randint(1, 6)
            evt = EVENTS_DECK[roll]
            gs["last_dice_roll"] = roll
            gs["last_event_name"] = evt["name"]
            gs["last_event_desc"] = evt["desc"]
            gs["market_calm_skies"] = (roll == 4)
            
            # RUN GLOBAL MULTIPLAYER MATH ENGINE
            for name, p in gs["players"].items():
                # Phase 2 Revenue Computations
                inc = 20000 + (p["fossil_tokens"] * 10000)
                if not gs["market_calm_skies"]:
                    inc += (p["green_tokens"] * 5000)
                p["cash"] += inc
                p["last_payout"] = inc
                
                # Phase 3 Shock Event Computations
                if roll == 1 and p["stability"] < 50:
                    p["cash"] -= 20000
                elif roll == 2:
                    p["cash"] -= (p["fossil_tokens"] * 5000)
                elif roll == 3:
                    p["cash"] += (p["green_tokens"] * 10000)
                elif roll == 5:
                    p["cash"] += 15000
                elif roll == 6:
                    p["stability"] -= 15
                
                # Boundaries checks
                p["stability"] = max(0, min(100, p["stability"]))
                p["cash"] = max(0, p["cash"])
                
            gs["current_phase"] = "Shock & Payout Phase"
            st.rerun()

    elif gs["current_round"] in range(1, 7) and gs["current_phase"] == "Shock & Payout Phase":
        st.success(f"Executed: {gs['last_event_name']} — {gs['last_event_desc']}")
        btn_txt = "🏁 Compute Final Game Standings" if gs["current_round"] == 6 else f"➡️ Clear Board: Unlock Round {gs['current_round'] + 1} Investments"
        
        if st.button(btn_txt, type="primary", use_container_width=True):
            if gs["current_round"] == 6:
                gs["current_phase"] = "Game Over"
                for name, p in gs["players"].items():
                    p["final_score"] = p["stability"] + (p["cash"] // 5000) - (p["fossil_tokens"] * 5)
            else:
                gs["current_round"] += 1
                gs["current_phase"] = "Investment Phase"
            st.rerun()

    if st.button("🚨 System Wide Full Wipe / New Game", type="secondary"):
        gs["current_round"] = 0
        gs["current_phase"] = "Setup"
        gs["players"].clear()
        gs["last_event_name"] = "Game Reset!"
        st.rerun()

# ==========================================
# 📱 VIEW: PLAYER TERMINAL INTERFACE
# ==========================================
if user_role == "Player Terminal":
    st.header("📟 Remote Grid Terminal")
    
    player_id = st.text_input("Enter Unique Player ID Profile Name:", value="", key="player_unique_id").strip()
    if not player_id:
        st.warning("Connection Blocked: Enter a username to register your pipeline on the central server.")
        st.stop()
        
    # Auto-generate profile inside global dictionary if it doesn't exist
    if player_id not in gs["players"]:
        gs["players"][player_id] = {
            "strategy": "Unchosen", "cash": 0, "stability": 50,
            "fossil_tokens": 0, "green_tokens": 0, "last_payout": 0, "final_score": 0
        }
        
    p_data = gs["players"][player_id]
    
    # Network Banner Feed
    st.info(f"🛰️ **Server Data Sync:** Round **{gs['current_round']}** | Step Status: **{gs['current_phase']}**")

    # PHASE 0: SETUP
    if gs["current_round"] == 0:
        st.subheader("🛠️ Phase 0: Initialize Infrastructure Matrix")
        if p_data["strategy"] == "Unchosen":
            strat = st.radio("Choose Strategy Matrix Profile:", ["Option A (Fossil Fast-Track: $50k Cash, 30% Base Grid)", "Option B (Green Startup: $10k Cash, 70% Base Grid)"])
            if st.button("Deploy Hardware to Server"):
                if "Fossil" in strat:
                    p_data["strategy"] = "Fossil"
                    p_data["cash"] = 50000
                    p_data["stability"] = 30
                else:
                    p_data["strategy"] = "Green"
                    p_data["cash"] = 10000
                    p_data["stability"] = 70
                st.success("Configuration Uploaded! Please wait for GM to hit start.")
                st.rerun()
        else:
            st.success(f"System Ready! Mode: **{p_data['strategy']}**. Initial Capital Confirmed.")
            st.caption("Please refresh your browser window using the sidebar button once the Game Master launches the match.")

    # ACTIVE ROUND RULES
    elif gs["current_round"] in range(1, 7):
        # Local Node Analytics Readout
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Available Operating Capital", f"${p_data['cash']:,}")
        c2.metric("Local Node Stability", f"{p_data['stability']}%")
        c3.metric("Fossil Infrastructure Assets", p_data["fossil_tokens"])
        c4.metric("Renewable Grid Assets", p_data["green_tokens"])
        
        st.divider()

        if gs["current_phase"] == "Investment Phase":
            st.subheader(f"⚡ Round {gs['current_round']}: Open Asset Procurement Order")
            
            f_buy = st.number_input("Purchase Fossil Blocks ($10,000 / Yield +$10k / Stability -10%)", min_value=0, step=1, key=f"f_b_{gs['current_round']}")
            g_buy = st.number_input("Purchase Green Blocks ($20,000 / Yield +$5k / Stability +10%)", min_value=0, step=1, key=f"g_b_{gs['current_round']}")
            
            req_cash = (f_buy * 10000) + (g_buy * 20000)
            st.markdown(f"Total Order Cost Summary: `${req_cash:,}`")
            
            if st.button("Transmit Purchases to Master Grid"):
                if req_cash > p_data["cash"]:
                    st.error("Transaction Error: Local vault does not contain enough liquidity.")
                else:
                    p_data["cash"] -= req_cash
                    p_data["fossil_tokens"] += f_buy
                    p_data["green_tokens"] += g_buy
                    p_data["stability"] += (g_buy * 10) - (f_buy * 10)
                    p_data["stability"] = max(0, min(100, p_data["stability"]))
                    st.success("Transmission successful! Wait for GM to execute the Grid Shock phase.")
                    st.rerun()

        elif gs["current_phase"] == "Shock & Payout Phase":
            st.subheader("📊 Central Server Computation Output")
            o1, o2 = st.columns(2)
            o1.metric("Automated Cash Infusion Collected", f"+${p_data['last_payout']:,}")
