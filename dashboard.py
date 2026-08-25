import streamlit as st
from database import FantaDatabase

# 1. Configurazione Pagina
st.set_page_config(
    page_title="FantaAsta Live Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def render_html(html_str: str) -> None:
    """Renderizza HTML pulito senza che il parser Markdown lo interpreti come blocco di codice."""
    cleaned = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    if hasattr(st, 'html'):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)

# 2. CSS Personalizzato Dark Theme ad alta leggibilità per 12 squadre
render_html("""
<style>
    /* Rimozione margini superiori per massimizzare lo spazio schermo */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    
    /* Live Ticker Header */
    .ticker-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-left: 5px solid #10b981;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    .ticker-title {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #10b981;
        letter-spacing: 0.05em;
    }
    
    .ticker-content {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f8fafc;
    }
    
    /* Grid 12 Squadre Responsive */
    .teams-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 14px;
        margin-top: 10px;
    }
    
    /* Card Squadra */
    .team-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 260px;
    }
    
    .team-card:hover {
        border-color: #3b82f6;
    }
    
    .team-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #334155;
        padding-bottom: 8px;
        margin-bottom: 8px;
    }
    
    .team-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: #60a5fa;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 160px;
    }
    
    .team-credits {
        font-size: 1.1rem;
        font-weight: 700;
        color: #10b981;
        text-align: right;
    }
    
    .team-credits-sub {
        font-size: 0.72rem;
        color: #94a3b8;
    }
    
    /* Ruoli Badges */
    .roles-bar {
        display: flex;
        justify-content: space-between;
        gap: 4px;
        margin-bottom: 8px;
        background: #0f172a;
        padding: 4px 6px;
        border-radius: 6px;
    }
    
    .role-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 5px;
        border-radius: 4px;
        text-align: center;
        flex: 1;
    }
    
    .badge-p { background: rgba(234, 179, 8, 0.15); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); }
    .badge-d { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .badge-c { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-a { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    
    .badge-full {
        background: #059669 !important;
        color: #ffffff !important;
        border: 1px solid #10b981 !important;
    }
    
    /* Lista Giocatori Micro-Scroll */
    .roster-box {
        max-height: 170px;
        overflow-y: auto;
        font-size: 0.8rem;
        padding-right: 4px;
    }
    
    .roster-box::-webkit-scrollbar {
        width: 4px;
    }
    .roster-box::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 3px;
    }
    
    .roster-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 3px 0;
        border-bottom: 1px solid #1e293b;
    }
    
    .player-tag {
        display: inline-block;
        width: 18px;
        height: 18px;
        line-height: 18px;
        text-align: center;
        border-radius: 3px;
        font-size: 0.68rem;
        font-weight: bold;
        margin-right: 6px;
    }
    
    .tag-P { background: #eab308; color: #000; }
    .tag-D { background: #22c55e; color: #000; }
    .tag-C { background: #3b82f6; color: #fff; }
    .tag-A { background: #ef4444; color: #fff; }
    
    .player-name {
        color: #f1f5f9;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 140px;
    }
    
    .player-price {
        font-weight: 700;
        color: #f87171;
    }
</style>
""")

@st.cache_resource
def get_db():
    """Singleton della connessione DB — evita di riaprire ad ogni refresh."""
    return FantaDatabase('asta.db')

# 3. Fragment con Auto-Refresh ogni 2 secondi
@st.fragment(run_every=2)
def live_dashboard_fragment():
    db = get_db()
    
    # Dati generali
    teams_data = db.get_dashboard_teams_data()
    last_purchase = db.get_last_purchase()
    
    # 3.1 Top Bar & Live Ticker
    if last_purchase:
        pname, role, real_team, fanta_team, price, pid = last_purchase
        role_colors = {'P': '#eab308', 'D': '#22c55e', 'C': '#3b82f6', 'A': '#ef4444'}
        role_color = role_colors.get(role, '#fff')
        
        render_html(f"""
        <div class="ticker-box">
            <div>
                <span class="ticker-title">🔥 Ultimo Acquisto</span><br/>
                <span class="ticker-content">
                    <span style="background-color: {role_color}; color: black; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold;">{role}</span>
                    <b style="color: #ffffff; margin-left: 6px;">{pname}</b> 
                    <span style="color: #94a3b8; font-size: 0.95rem;">({real_team})</span> 
                    ➔ <span style="color: #60a5fa; font-weight: bold;">{fanta_team}</span> 
                    per <span style="color: #4ade80; font-weight: bold;">{price} crediti</span>
                </span>
            </div>
            <div style="text-align: right; color: #94a3b8; font-size: 0.8rem;">
                Live Sync ⚡ <span style="color: #10b981;">● Attivo</span>
            </div>
        </div>
        """)
    else:
        render_html("""
        <div class="ticker-box">
            <div>
                <span class="ticker-title">⚽ Asta in Corso</span><br/>
                <span class="ticker-content" style="color: #94a3b8;">In attesa del primo acquisto dalla CLI...</span>
            </div>
            <div style="text-align: right; color: #94a3b8; font-size: 0.8rem;">
                Live Sync ⚡ <span style="color: #10b981;">● Connesso</span>
            </div>
        </div>
        """)

    if not teams_data:
        st.warning("⚠️ Nessuna squadra configurata nel database. Esegui il comando `setup` nella CLI per iniziare l'asta!")
        return

    # 3.2 Metriche Globali
    num_teams = len(teams_data)
    total_slots = num_teams * 25
    total_players_bought = sum(t['total_players'] for t in teams_data)
    total_spent = sum(t['spent'] for t in teams_data)
    total_budget_circulating = sum(t['budget'] for t in teams_data)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Squadre Partecipanti", f"{num_teams}")
    with col2:
        st.metric("📋 Giocatori Assegnati", f"{total_players_bought} / {total_slots}", f"{(total_players_bought/total_slots*100):.1f}% completato" if total_slots > 0 else "0%")
    with col3:
        st.metric("💰 Crediti Spesi Totali", f"{total_spent} cr", f"Residui: {total_budget_circulating - total_spent} cr")
    with col4:
        avg_price = (total_spent / total_players_bought) if total_players_bought > 0 else 0
        st.metric("📈 Costo Medio per Giocatore", f"{avg_price:.1f} cr")

    # 3.3 Tab Principali
    tab_grid, tab_matrix, tab_free = st.tabs(["🏟️ Griglia 12 Squadre (Live)", "📊 Matrice Reparti & Spesa", "🔍 Svincolati & Listone"])

    # TAB 1: GRIGLIA 12 SQUADRE RESPONSIVE
    with tab_grid:
        cards_html = ['<div class="teams-grid">']
        for t in teams_data:
            rc = t['roles_count']
            p_cls = "role-badge badge-p badge-full" if rc['P'] == 3 else "role-badge badge-p"
            d_cls = "role-badge badge-d badge-full" if rc['D'] == 8 else "role-badge badge-d"
            c_cls = "role-badge badge-c badge-full" if rc['C'] == 8 else "role-badge badge-c"
            a_cls = "role-badge badge-a badge-full" if rc['A'] == 6 else "role-badge badge-a"
            
            # Formattazione lista giocatori
            roster_html = []
            if t['roster']:
                for pname, rteam, role, price in t['roster']:
                    roster_html.append(f"""
                        <div class="roster-row">
                            <div style="display:flex; align-items:center;">
                                <span class="player-tag tag-{role}">{role}</span>
                                <span class="player-name" title="{pname} ({rteam})">{pname}</span>
                            </div>
                            <span class="player-price">{price} cr</span>
                        </div>
                    """)
            else:
                roster_html.append('<div style="color: #64748b; text-align: center; margin-top: 20px; font-style: italic;">Nessun acquisto</div>')

            card = f"""
            <div class="team-card">
                <div>
                    <div class="team-header">
                        <div class="team-name" title="{t['name']}">{t['name']}</div>
                        <div class="team-credits">
                            {t['remaining']} cr
                            <div class="team-credits-sub">Spesi: {t['spent']}/{t['budget']}</div>
                        </div>
                    </div>
                    
                    <div class="roles-bar">
                        <div class="{p_cls}">🧤 {rc['P']}/3</div>
                        <div class="{d_cls}">🛡️ {rc['D']}/8</div>
                        <div class="{c_cls}">🎯 {rc['C']}/8</div>
                        <div class="{a_cls}">⚡ {rc['A']}/6</div>
                    </div>
                </div>
                
                <div class="roster-box">
                    {''.join(roster_html)}
                </div>
            </div>
            """
            cards_html.append(card)
            
        cards_html.append('</div>')
        render_html(''.join(cards_html))

    # TAB 2: MATRICE REPARTI & SPESA
    with tab_matrix:
        matrix_rows = []
        for t in teams_data:
            rc = t['roles_count']
            sb = t['spending_by_role']
            matrix_rows.append({
                "Squadra": t['name'],
                "Crediti Rimanenti": f"{t['remaining']} cr",
                "Spesa Totale": f"{t['spent']} cr",
                "Portieri": f"{rc['P']}/3 ({sb['P']} cr)",
                "Difensori": f"{rc['D']}/8 ({sb['D']} cr)",
                "Centrocampisti": f"{rc['C']}/8 ({sb['C']} cr)",
                "Attaccanti": f"{rc['A']}/6 ({sb['A']} cr)",
                "Tot Giocatori": f"{t['total_players']}/25"
            })
        st.dataframe(matrix_rows, use_container_width=True, hide_index=True)

    # TAB 3: SVINCOLATI & LISTONE
    with tab_free:
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            role_sel = st.selectbox("Filtra per Ruolo:", ["TUTTI", "P", "D", "C", "A"], key="role_sel")
        with col_f2:
            search_query = st.text_input("Cerca calciatore libero:", placeholder="Es. Lautaro, Dimarco...", key="free_search")
            
        free_players = db.get_free_players(role_filter=role_sel, search=search_query, limit=100)
        
        if free_players:
            free_data = [{"Ruolo": r[3], "Nome": r[1], "Squadra Serie A": r[2]} for r in free_players]
            st.dataframe(free_data, use_container_width=True, hide_index=True)
        else:
            st.info("Nessun calciatore trovato corrispondente ai filtri.")

# Avvio Fragment
live_dashboard_fragment()
