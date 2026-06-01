import streamlit as st
import pandas as pd
import random

# Force wide layout for easy data viewing
st.set_page_config(page_title="Grid Rush Multiplayer", layout="wide", initial_sidebar_state="expanded")

# --- GLOBAL GAME STATE MANAGER (Simulated Cloud Database) ---
if "global_state" not in st.session_state:
    st.session_state.global_state = {
        "current_round": 0,       # 0 = Setup, 1-6 = Active Rounds
        "current_phase": "Setup",  # Setup, Invest, Shock, Scoreboard
        "last_dice_roll": 0,
        "last_event_name": "Game not started yet.",
        "last_event_desc": "Waiting for the Game Master to initialize the grid.",
        "market_calm_skies": False,
        "players": {}
    }

gs = st.session_state.global_state

# Event Reference Deck
EVENTS_DECK = {
    1: {"name": "Heatwave 🔥", "desc": "High AC usage! If Stability < 50%, you lose $20,000 in grid repairs."},
    2: {"name": "Carbon Tax 💸", "desc": "Government penalty! Pay $5,000 for every Fossil Token you own."},
    3: {"name": "Tech Breakthrough 🚀", "desc": "Green subsidy! Gain $10,000 for every Green Token you own."},
    4: {"name": "Calm Skies ☁️", "desc": "No wind or solar! Green Tokens yield $0 income next round."},
    5: {"name": "Market Boom 📈", "desc": "Energy demand spikes! Everyone receives an extra $15,000."},
    6: {"name": "Grid Failure 💥", "desc": "Major blackout! Grid Stability drops -15% across the board."}
}

# --- APPLICATION ROUTING (LOGIN) ---
st.sidebar.title("⚡ Grid Rush Login")
user_role = st.sidebar.selectbox("Identify your role:", ["Choose...", "Game Master (Host)", "Player Terminal"])

if user_role == "Choose...":
    st.info("### Welcome to Grid Rush!\nSelect your role in the sidebar to log into the energy network control panel.")
    st.stop()

# ==========================================
# 👑 VIEW: GAME MASTER DASHBOARD
# ==========================================
if user_role == "Game Master (Host)":
    st.title("🕹️ Game Master Control Center")
    
    # Grid Status Overview
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Round", f"{gs['current_round']} / 6")
    col2.metric("Active Phase", gs["current_phase"])
    col3.metric("Total Connected Grids", len(gs["players"]))
    
    st.divider()
    
    # Round Progression Logic Controls
    st.subheader("⚙️ Control Panel Operations")
    
    if gs["current_round"] == 0:
        if st.button("🚀 Lock Setup & Start Round 1", type="primary", use_container_width=True):
            gs["current_round"] = 1
            gs["current_phase"] = "Investment Phase"
            st.rerun()
            
    elif gs["current_round"] <= 6 and gs["current_phase"] == "Investment Phase":
        st.warning("Ensure all players have keyed in their token investments before proceeding.")
        if st.button("🎲 Roll Dice & Trigger Phase 3 (Grid Shock)", type="primary", use_container_width=True):
            # Roll Die
            roll = random.randint(1, 6)
            evt = EVENTS_DECK[roll]
            gs["last_dice_roll"] = roll
            gs["last_event_name"] = evt["name"]
            gs["last_event_desc"] = evt["desc"]
            
            # Reset Calm Skies tracker flag from previous rounds
            gs["market_calm_skies"] = (roll == 4)
            
            # PROCESS GLOBAL COMPUTATION FOR ALL PLAYER TERMINALS
            for name, p in gs["players"].items():
                # Phase 2: Income Calculation
                inc = 20000 + (p["fossil_tokens"] * 10000)
                if not gs["market_calm_skies"]:
                    inc += (p["green_tokens"] * 5000)
                p["cash"] += inc
                p["last_payout"] = inc
                
                # Phase 3: Apply Shock Modifiers
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
                
                # Enforce system thresholds
                p["stability"] = max(0, min(100, p["stability"]))
                p["cash"] = max(0, p["cash"])
                
            gs["current_phase"] = "Shock & Payout Phase"
            st.rerun()

    elif gs["current_round"] <= 6 and gs["current_phase"] == "Shock & Payout Phase":
        st.info(f"**Last Event Resolution:** Rolled {gs['last_dice_roll']} -> {gs['last_event_name']}")
        btn_text = "🏁 End Game & View Final Scoreboard" if gs["current_round"] == 6 else f"➡️ Advance to Round {gs['current_round'] + 1} Investment"
        
        if st.button(btn_text, type="primary", use_container_width=True):
            if gs["current_round"] == 6:
                gs["current_phase"] = "Game Over"
                # Compute Final Scores
                for name, p in gs["players"].items():
                    p["final_score"] = p["stability"] + (p["cash"] // 5000) - (p["fossil_tokens"] * 5)
            else:
                gs["current_round"] += 1
                gs["current_phase"] = "Investment Phase"
            st.rerun()

    if st.button("🚨 Hard Reset Game Engine", type="secondary"):
        st.session_state.clear()
        st.rerun()

# ==========================================
# 📱 VIEW: PLAYER TERMINAL INTERFACE
# ==========================================
if user_role == "Player Terminal":
    st.title("📟 Energy Grid Terminal")
    
    # Player Identity Registration
    player_id = st.text_input("Enter Unique Player Name/Number (e.g., Player 05):", "").strip()
    if not player_id:
        st.warning("Please enter your assigned identifier name to connect your grid terminal to the host.")
        st.stop()
        
    # Register player into global pool data structure if new
    if player_id not in gs["players"]:
        gs["players"][player_id] = {
            "strategy": "Unchosen", "cash": 0, "stability": 50,
            "fossil_tokens": 0, "green_tokens": 0, "last_payout": 0, "final_score": 0
        }
        
    p_data = gs["players"][player_id]
    
    # DISPLAY GLOBAL ENGINE STATUS
    st.info(f"### **Global Sync Status**\n* **Round:** {gs['current_round']} / 6 | **Active Step:** {gs['current_phase']}")

    # STEP 0: INITIAL STRATEGY SELECTION
    if gs["current_round"] == 0:
        st.subheader("⚙️ Step 1: Initialize System Infrastructure Strategy")
        if p_data["strategy"] == "Unchosen":
            strat = st.radio("Choose Starting Asset Tech Matrix:", ["Option A (Fossil Fast-Track)", "Option B (Green Startup)"])
            if st.button("Confirm Starting Footprint"):
                if "Fossil" in strat:
                    p_data["strategy"] = "Fossil"
                    p_data["cash"] = 50000
                    p_data["stability"] = 30
                else:
                    p_data["strategy"] = "Green"
                    p_data["cash"] = 10000
                    p_data["stability"] = 70
                st.success("Configuration sent! Wait for Game Master to kick off Round 1.")
                st.rerun()
        else:
            st.success(f"Config Locked: **{p_data['strategy']} Strategy**. Capital: ${p_data['cash']:,} | Stability: {p_data['stability']}%")
            st.caption("Waiting for Game Master to launch Round 1...")

    # STEPS 1-6: ACTIVE GAMEPLAY ENGINE
    elif gs["current_round"] in range(1, 7):
        # Persistent Top Status Row Matrix Display for Player
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Your Liquid Cash", f"${p_data['cash']:,}")
        sc2.metric("Grid Stability (%)", f"{p_data['stability']}%")
        sc3.metric("Owned Fossil Units", p_data["fossil_tokens"])
        sc4.metric("Owned Renewable Units", p_data["green_tokens"])
        
        st.divider()

        # PHASE A: INVESTMENT INTERFACE WINDOW
        if gs["current_phase"] == "Investment Phase":
            st.subheader(f"🛠️ Round {gs['current_round']}: Buy Grid Assets")
            st.write("Allocate your funds. Changes are real-time until GM triggers the dice roll.")
            
            f_buy = st.number_input("Purchase Fossil Tokens ($10,000 each / +$10k Yield / -10% Stability)", min_value=0, step=1, key="f_buy_input")
            g_buy = st.number_input("Purchase Green Tokens ($20,000 each / +$5k Yield / +10% Stability)", min_value=0, step=1, key="g_buy_input")
            
            total_cost = (f_buy * 10000) + (g_buy * 20000)
            st.markdown(f"**Total Capital Required:** `${total_cost:,}`")
            
            if st.button("Lock Investments for this Round"):
                if total_cost > p_data["cash"]:
                    st.error("Transaction Aborted: Insufficient liquidity reserves.")
                else:
                    p_data["cash"] -= total_cost
                    p_data["fossil_tokens"] += f_buy
                    p_data["green_tokens"] += g_buy
                    p_data["stability"] += (g_buy * 10) - (f_buy * 10)
                    p_data["stability"] = max(0, min(100, p_data["stability"]))
                    st.success("Assets integrated! Awaiting GM Grid Shock Execution phase.")
                    st.rerun()

        # PHASE B: SHOCK & REVENUE RESOLUTION VIEW
        elif gs["current_phase"] == "Shock & Payout Phase":
            st.subheader("⚡ Phase 2 & 3 Output Resolution Dashboard")
            
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.metric("Phase 2 Automated Income Yield", f"+${p_data['last_payout']:,}")
            with r_col2:
                st.error(f"Phase 3 Event Result: {gs['last_event_name']}")
                st.caption(gs["last_event_desc"])
