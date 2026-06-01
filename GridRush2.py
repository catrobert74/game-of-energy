import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Grid Rush - Deadlock Free", layout="wide")

@st.cache_resource
def get_global_game_state():
    return {
        "current_round": 0,       
        "current_phase": "Setup",  
        "last_dice_roll": 0,
        "last_event_name": "Game not started yet.",
        "last_event_desc": "Waiting for the Game Master to initialize the grid.",
        "market_calm_skies": False,
        "players": {}
    }

gs = get_global_game_state()

EVENTS_DECK = {
    1: {"name": "Heatwave 🔥", "desc": "High AC usage! If Stability < 50%, you lose $20,000 in grid repairs."},
    2: {"name": "Carbon Tax 💸", "desc": "Government penalty! Pay $5,000 for every Fossil Token you own."},
    3: {"name": "Tech Breakthrough 🚀", "desc": "Green subsidy! Gain $10,000 for every Green Token you own."},
    4: {"name": "Calm Skies ☁️", "desc": "No wind or solar! Green Tokens yield $0 income next round."},
    5: {"name": "Market Boom 📈", "desc": "Energy demand spikes! Everyone receives an extra $15,000."},
    6: {"name": "Grid Failure 💥", "desc": "Major blackout! Grid Stability drops -15% across the board."}
}

st.title("⚡ Grid Rush: Live Coordination Panel")

# Navigation & Global Sync Action
st.sidebar.title("🕹️ System Portal")
user_role = st.sidebar.selectbox("Select Role:", ["Choose...", "Game Master (Host)", "Player Terminal"])

if st.sidebar.button("🔄 Refresh Global Screen Data", type="primary", use_container_width=True):
    st.rerun()

if user_role == "Choose...":
    st.info("### Choose your role in the sidebar to log in.")
    st.stop()

# ==========================================
# 👑 VIEW: GAME MASTER DASHBOARD
# ==========================================
if user_role == "Game Master (Host)":
    st.header("🕹️ Game Master Control Center")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Round", f"{gs['current_round']} / 6")
    m2.metric("Universal Phase", gs["current_phase"])
    m3.metric("Registered Grids", len(gs["players"]))
    
    st.divider()
    
    # Check readiness of all players
    total_players = len(gs["players"])
    ready_players = sum(1 for p in gs["players"].values() if p["ready_for_phase"])
    
    st.subheader("📊 Player Readiness Monitor")
    st.progress(ready_players / max(total_players, 1), text=f"{ready_players} out of {total_players} players are ready.")

    # State Flow Buttons
    if gs["current_round"] == 0:
        if st.button("🚀 Lock Sign-ups & Launch Round 1", use_container_width=True):
            gs["current_round"] = 1
            gs["current_phase"] = "Investment Phase"
            for p in gs["players"].values():
                p["ready_for_phase"] = False  # Reset flags for new round
            st.rerun()
            
    elif gs["current_round"] in range(1, 7) and gs["current_phase"] == "Investment Phase":
        # GM can force the roll even if some players haven't submitted yet
        if st.button("🎲 Roll Dice & Process Global Round Payouts", type="primary", use_container_width=True):
            roll = random.randint(1, 6)
            evt = EVENTS_DECK[roll]
            gs["last_dice_roll"] = roll
            gs["last_event_name"] = evt["name"]
            gs["last_event_desc"] = evt["desc"]
            gs["market_calm_skies"] = (roll == 4)
            
            for name, p in gs["players"].items():
                # Process phase 2 automated revenue
                inc = 20000 + (p["fossil_tokens"] * 10000)
                if not gs["market_calm_skies"]:
                    inc += (p["green_tokens"] * 5000)
                p["cash"] += inc
                p["last_payout"] = inc
                
                # Process phase 3 shock event
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
                
                p["stability"] = max(0, min(100, p["stability"]))
                p["cash"] = max(0, p["cash"])
                p["ready_for_phase"] = False  # Reset flag for viewing results
                
            gs["current_phase"] = "Shock & Payout Phase"
            st.rerun()

    elif gs["current_round"] in range(1, 7) and gs["current_phase"] == "Shock & Payout Phase":
        st.success(f"Executed: {gs['last_event_name']} — {gs['last_event_desc']}")
        btn_txt = "🏁 Go to Final Results" if gs["current_round"] == 6 else f"➡️ Open Round {gs['current_round'] + 1} Investments"
        
        if st.button(btn_txt, use_container_width=True):
            if gs["current_round"] == 6:
                gs["current_phase"] = "Game Over"
                for name, p in gs["players"].items():
                    p["final_score"] = p["stability"] + (p["cash"] // 5000) - (p["fossil_tokens"] * 5)
            else:
                gs["current_round"] += 1
                gs["current_phase"] = "Investment Phase"
            st.rerun()

    if st.button("🚨 Emergency Hard Reset", type="secondary"):
        gs["current_round"] = 0
        gs["current_phase"] = "Setup"
        gs["players"].clear()
        st.rerun()

# ==========================================
# 📱 VIEW: PLAYER TERMINAL INTERFACE
# ==========================================
if user_role == "Player Terminal":
    st.header("📟 Remote Grid Terminal")
    
    player_id = st.text_input("Enter Your Profile Name:", value="", key="player_unique_id").strip()
    if not player_id:
        st.warning("Please enter your name to connect.")
        st.stop()
        
    if player_id not in gs["players"]:
        gs["players"][player_id] = {
            "strategy": "Unchosen", "cash": 0, "stability": 50,
            "fossil_tokens": 0, "green_tokens": 0, "last_payout": 0, "final_score": 0,
            "ready_for_phase": False
        }
        
    p_data = gs["players"][player_id]
    
    # Visual status cues to guide the user
    st.info(f"🛰️ **Server Status:** Round **{gs['current_round']}** | Current Step: **{gs['current_phase']}**")

    # PHASE 0: SETUP
    if gs["current_round"] == 0:
        st.subheader("🛠️ Setup: Choose Starting Strategy")
        if p_data["strategy"] == "Unchosen":
            strat = st.radio("Pick your footprint profile:", ["Option A (Fossil Fast-Track: $50k Cash, 30% Grid)", "Option B (Green Startup: $10k Cash, 70% Grid)"])
            if st.button("Confirm Strategy Choice"):
                if "Fossil" in strat:
                    p_data["strategy"] = "Fossil"
                    p_data["cash"] = 50000
                    p_data["stability"] = 30
                else:
                    p_data["strategy"] = "Green"
                    p_data["cash"] = 10000
                    p_data["stability"] = 70
                p_data["ready_for_phase"] = True
                st.success("Choice saved! Tell the GM you are ready, then wait for Round 1.")
                st.rerun()
        else:
            st.success(f"Strategy locked in: **{p_data['strategy']}**. Waiting for Game Master to start.")
            st.caption("Once the GM starts Round 1, click 'Refresh' in your sidebar.")

    # ACTIVE GAME LOOP (ROUNDS 1-6)
    elif gs["current_round"] in range(1, 7):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Available Cash", f"${p_data['cash']:,}")
        c2.metric("Grid Stability", f"{p_data['stability']}%")
        c3.metric("Fossil Blocks", p_data["fossil_tokens"])
        c4.metric("Renewable Blocks", p_data["green_tokens"])
        
        st.divider()

        if gs["current_phase"] == "Investment Phase":
            if p_data["ready_for_phase"]:
                st.success("⏳ Investment data sent! Waiting for the Game Master to roll the dice and resolve the phase.")
                st.caption("Click 'Refresh Global Screen Data' in your sidebar if the GM says they rolled.")
            else:
                st.subheader(f"🛠️ Round {gs['current_round']}: Buy Grid Assets")
                f_buy = st.number_input("Buy Fossil Blocks ($10,000 / Yield +$10k / Stability -10%)", min_value=0, step=1, key=f"f_b_{gs['current_round']}")
                g_buy = st.number_input("Buy Green Blocks ($20,000 / Yield +$5k / Stability +10%)", min_value=0, step=1, key=f"g_b_{gs['current_round']}")
                
                req_cash = (f_buy * 10000) + (g_buy * 20000)
                st.markdown(f"Total Bill: `${req_cash:,}`")
                
                if st.button("Transmit Investments to Host", type="primary"):
                    if req_cash > p_data["cash"]:
                        st.error("Insufficient funds in your account.")
                    else:
                        p_data["cash"] -= req_cash
                        p_data["fossil_tokens"] += f_buy
                        p_data["green_tokens"] += g_buy
                        p_data["stability"] += (g_buy * 10) - (f_buy * 10)
                        p_data["stability"] = max(0, min(100, p_data["stability"]))
                        p_data["ready_for_phase"] = True  # Tell GM this specific player is done!
                        st.success("Sent! Waiting for GM to roll.")
                        st.rerun()

        elif gs["current_phase"] == "Shock & Payout Phase":
            st.subheader("📊 Round Resolution Report")
            o1, o2 = st.columns(2)
            o1.metric("Phase 2 Cash Income Earned", f"+${p_data['last_payout']:,}")
            with o2:
                st.warning(f"Global Incident: {gs['last_event_name']}")
                st.write(gs["last_event_desc"])


