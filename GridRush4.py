import streamlit as st
import random
from supabase import create_client, Client

# Page Config
st.set_page_config(page_title="Grid Tycoon", layout="centered")

# Initialize Supabase Client
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- HELPER FUNCTIONS ---
def get_game_state():
    res = supabase.table("game_state").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else None

def get_players():
    res = supabase.table("players").select("*").execute()
    return res.data

def register_player(username):
    supabase.table("players").upsert({
        "username": username, "balance": 50000, "fossil_count": 0, "green_count": 0, "submitted_choice": None
    }).execute()

# --- GAME LOGIC ENGINE ---
EVENTS = {
    "Green Subsidy 🌿": {"fossil": 0, "green": 20000},
    "Oil Spike 🛢️": {"fossil": 20000, "green": 0},
    "Carbon Tax 💸": {"fossil": -15000, "green": 0},
    "Dunkelflaute ☁️": {"fossil": 10000, "green": -10000},
    "Market Boom 📈": {"fossil": 15000, "green": 15000},
    "None": {"fossil": 0, "green": 0}
}

def process_round(event_name):
    players = get_players()
    state = get_game_state()
    
    for p in players:
        f_count = p["fossil_count"]
        g_count = p["green_count"]
        bal = p["balance"]
        choice = p["submitted_choice"]
        
        # 1. Process Choices & Upfront Costs
        if choice == "Fossil" and bal >= 20000:
            bal -= 20000
            f_count += 1
        elif choice == "Green" and bal >= 30000:
            bal -= 30000
            g_count += 1
            
        # 2. Add Base Revenues
        bal += (f_count * 15000) + (g_count * 10000)
        
        # 3. Apply Event Modifiers
        mod = EVENTS[event_name]
        bal += (f_count * mod["fossil"]) + (g_count * mod["green"])
        
        # Update database per player
        supabase.table("players").update({
            "balance": max(0, bal),
            "fossil_count": f_count,
            "green_count": g_count,
            "submitted_choice": None # Reset choice for next round
        }).eq("username", p["username"]).execute()
        
    # Advance Game State
    next_round = state["current_round"] + 1
    game_active = False if next_round > 5 else True
    
    supabase.table("game_state").update({
        "current_round": next_round,
        "current_event": event_name,
        "game_active": game_active
    }).eq("id", 1).execute()

# --- UI LOGIC ---
st.title("⚡ Grid Tycoon: Energy Matrix")

# Sidebar Login
st.sidebar.header("🚪 Login Portal")
role = st.sidebar.radio("Select Role", ["Player", "Game Master"])
username = st.sidebar.text_input("Enter Username/Access Code", "").strip()

state = get_game_state()

if not username:
    st.info("👋 Enter a username in the sidebar to join the session.")
else:
    # --- GAME MASTER DASHBOARD ---
    if role == "Game Master" and username == "admin-gm-99": # Simple GM password Protection
        st.header("👑 Game Master Control Panel")
        st.subheader(f"Current Round Status: {state['current_round']} / 5")
        
        players = get_players()
        submitted_count = sum(1 for p in players if p["submitted_choice"] is not None)
        st.metric("Players Ready", f"{submitted_count} / {len(players)}")
        
        if state["game_active"]:
            if st.button("🎲 Roll Dice & Process Round", type="primary"):
                rolled_event = random.choice([k for k in EVENTS.keys() if k != "None"])
                process_round(rolled_event)
                st.success(f"Rolled Event: {rolled_event}! Data Updated.")
                st.rerun()
        else:
            st.error("🏁 Game is finished!")
            if st.button("🔄 Reset Global Game"):
                supabase.table("game_state").update({"current_round": 1, "current_event": "None", "game_active": True}).eq("id", 1).execute()
                supabase.table("players").delete().neq("username", "keep_schema").execute()
                st.rerun()

        # GM Scoreboard View
        st.write("### 📊 Live Leaderboard")
        st.dataframe(players)

    # --- PLAYER INTERFACE ---
    elif role == "Player":
        # Register user if not exists
        player_data = next((p for p in get_players() if p["username"] == username), None)
        if not player_data:
            register_player(username)
            st.rerun()
            
        # UI Header Metrics
        st.subheader(f"Player: {username} | Round: {min(5, state['current_round'])}/5")
        
        # Metric Grid Calculations
        total_projects = player_data["fossil_count"] + player_data["green_count"]
        stability = (player_data["green_count"] / total_projects * 100) if total_projects > 0 else 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Cash Balance", f"${player_data['balance']:,}")
        col2.metric("🏭 Assets", f"🛢️ {player_data['fossil_count']} | 🌿 {player_data['green_count']}")
        col3.metric("📈 Grid Stability", f"{stability:.0f}%")
        
        st.markdown(f"**Last Event Rolled:** {state['current_event']}")
        
        # Action Step
        if state["game_active"]:
            if player_data["submitted_choice"] is None:
                st.write("### 🏗️ Step 1: Make Your Turn Choice")
                choice = st.radio("Choose your action:", [
                    "Do Nothing (Save Cash)",
                    "Build a Fossil Project (Cost: $20,000 | +$15,000 Base Rev)",
                    "Build a Renewable Project (Cost: $30,000 | +$10,000 Base Rev)"
                ])
                
                db_choice = "None"
                if "Fossil" in choice: db_choice = "Fossil"
                if "Renewable" in choice: db_choice = "Green"
                
                if st.button("🔒 Lock In Action", type="primary"):
                    supabase.table("players").update({"submitted_choice": db_choice}).eq("username", username).execute()
                    st.success("Choice Locked! Waiting for GM to roll the events...")
                    st.rerun()
            else:
                st.info("⏳ Waiting for other players and the Game Master's global event roll...")
                if st.button("🔄 Refresh Screen Status"):
                    st.rerun()
        else:
            # End Game Metric Calculation (Score = Cash * Stability Ratio)
            final_score = player_data["balance"] * (stability / 100)
            st.balloons()
            st.header("🏆 Final Game Results!")
            st.metric(label="Your Final Metric Score", value=f"{final_score:,.0f} pts")
            st.write(f"Final Balance: ${player_data['balance']:,} | Final Stability Ratio: {stability:.0f}%")
