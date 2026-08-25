import sqlite3
import csv
import os
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class FantaDatabase:
    """
    Gestisce tutte le operazioni di persistenza su database SQLite per l'Asta del Fantacalcio.
    Fornisce un'interfaccia ad alto livello per le query.
    """
    
    def __init__(self, db_path: str = 'asta.db') -> None:
        """
        Inizializza la connessione al database e crea le tabelle necessarie se non esistono.
        
        Args:
            db_path (str): Il percorso del file di database SQLite.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False)
        # Abilita WAL mode per concorrenza ottimale tra CLI e Streamlit
        try:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        self._init_tables()

    def __enter__(self) -> 'FantaDatabase':
        """Supporto per l'uso come context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Chiude la connessione all'uscita dal context manager."""
        self.close()

    def _init_tables(self) -> None:
        """Crea le tabelle del database se non sono già presenti."""
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS teams (name TEXT PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY, name TEXT, team TEXT, role TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id INTEGER,
                        team_name TEXT,
                        price INTEGER,
                        FOREIGN KEY(player_id) REFERENCES players(id),
                        FOREIGN KEY(team_name) REFERENCES teams(name)
                     )''')
        # Indici per le query più frequenti
        c.execute('''CREATE INDEX IF NOT EXISTS idx_players_name ON players(name)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_players_role ON players(role)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_purchases_team ON purchases(team_name)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_purchases_player ON purchases(player_id)''')
        self.conn.commit()

    def get_config(self, key: str, default: int = 0) -> int:
        """Recupera un valore di configurazione (es. budget)."""
        c = self.conn.cursor()
        c.execute("SELECT value FROM config WHERE key=?", (key,))
        row = c.fetchone()
        return int(row[0]) if row else default

    def set_config(self, key: str, value: int) -> None:
        """Imposta un valore di configurazione."""
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def setup_teams(self, teams_list: List[str]) -> None:
        """Cancella le squadre esistenti e inserisce quelle nuove."""
        c = self.conn.cursor()
        c.execute("DELETE FROM teams")
        for t in teams_list:
            c.execute("INSERT INTO teams (name) VALUES (?)", (t,))
        self.conn.commit()

    def get_all_teams(self) -> List[str]:
        """Restituisce la lista di tutte le squadre configurate."""
        c = self.conn.cursor()
        c.execute("SELECT name FROM teams")
        return [row[0] for row in c.fetchall()]

    def team_exists(self, team_name: str) -> bool:
        """Verifica se una determinata squadra esiste."""
        c = self.conn.cursor()
        c.execute("SELECT name FROM teams WHERE name=?", (team_name,))
        return c.fetchone() is not None

    def search_players_by_name(self, name_query: str, limit: int = 15) -> List[Tuple[int, str, str, str]]:
        """Cerca giocatori nel database per nome (autocompletamento).
        Prova prima con prefisso (usa indice), poi fallback a contains se servono più risultati."""
        c = self.conn.cursor()
        # Ricerca per prefisso (index-friendly)
        c.execute("SELECT id, name, team, role FROM players WHERE name LIKE ? LIMIT ?",
                  (name_query + '%', limit))
        results = c.fetchall()
        if len(results) < limit:
            # Fallback: contains (full scan ma solo se il prefisso non basta)
            existing_ids = {r[0] for r in results}
            remaining = limit - len(results)
            c.execute("SELECT id, name, team, role FROM players WHERE name LIKE ? LIMIT ?",
                      ('%' + name_query + '%', limit))
            for row in c.fetchall():
                if row[0] not in existing_ids:
                    results.append(row)
                    if len(results) >= limit:
                        break
        return results

    def get_player_by_exact_name(self, exact_name: str) -> Optional[Tuple[int, str, str]]:
        """Recupera ID, Nome e Ruolo di un giocatore partendo dal nome esatto."""
        c = self.conn.cursor()
        c.execute("SELECT id, name, role FROM players WHERE name=?", (exact_name,))
        return c.fetchone()

    def search_teams_by_name(self, name_query: str) -> List[str]:
        """Cerca squadre per nome (autocompletamento)."""
        c = self.conn.cursor()
        c.execute("SELECT name FROM teams WHERE name LIKE ?", ('%' + name_query + '%',))
        return [row[0] for row in c.fetchall()]

    def count_team_role(self, team_name: str, role: str) -> int:
        """Conta quanti giocatori ha una squadra in uno specifico ruolo."""
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(*) FROM purchases pu 
                     JOIN players p ON pu.player_id = p.id 
                     WHERE pu.team_name=? AND p.role=?''', (team_name, role))
        return c.fetchone()[0]

    def get_team_spent(self, team_name: str) -> int:
        """Calcola i crediti totali spesi da una squadra."""
        c = self.conn.cursor()
        c.execute("SELECT SUM(price) FROM purchases WHERE team_name=?", (team_name,))
        return c.fetchone()[0] or 0

    def is_player_purchased(self, player_id: int) -> Optional[str]:
        """
        Verifica se un giocatore è già stato acquistato.
        Restituisce il nome della squadra acquirente, oppure None se è libero.
        """
        c = self.conn.cursor()
        c.execute("SELECT team_name FROM purchases WHERE player_id=?", (player_id,))
        row = c.fetchone()
        return row[0] if row else None

    def add_purchase(self, player_id: int, team_name: str, price: int) -> None:
        """Registra un acquisto nel database."""
        c = self.conn.cursor()
        c.execute("INSERT INTO purchases (player_id, team_name, price) VALUES (?, ?, ?)", (player_id, team_name, price))
        self.conn.commit()

    def get_teams_status(self) -> List[Tuple[str, int, int]]:
        """Restituisce lo stato (spesi, quanti giocatori) per ogni squadra in una singola query."""
        c = self.conn.cursor()
        c.execute('''
            SELECT t.name, COALESCE(SUM(pu.price), 0), COUNT(pu.id)
            FROM teams t
            LEFT JOIN purchases pu ON t.name = pu.team_name
            GROUP BY t.name
            ORDER BY t.name
        ''')
        return c.fetchall()

    def get_roles_count_by_team(self, team_name: str) -> Dict[str, int]:
        """Restituisce un dizionario con il conteggio dei giocatori per ogni ruolo per una squadra."""
        c = self.conn.cursor()
        c.execute('''SELECT p.role, COUNT(*) 
                     FROM purchases pu 
                     JOIN players p ON pu.player_id = p.id 
                     WHERE pu.team_name=? 
                     GROUP BY p.role''', (team_name,))
        return {row[0]: row[1] for row in c.fetchall()}

    def get_spending_by_role(self, team_name: str) -> Dict[str, int]:
        """Restituisce un dizionario con la spesa totale divisa per ruolo per una squadra."""
        c = self.conn.cursor()
        c.execute('''SELECT p.role, SUM(pu.price) 
                     FROM purchases pu 
                     JOIN players p ON pu.player_id = p.id 
                     WHERE pu.team_name=? 
                     GROUP BY p.role''', (team_name,))
        return {row[0]: row[1] for row in c.fetchall()}

    def get_roster(self, team_name: str) -> List[Tuple[str, str, str, int]]:
        """Restituisce i giocatori di una squadra ordinati per ruolo (P, D, C, A)."""
        c = self.conn.cursor()
        c.execute('''
            SELECT p.name, p.team, p.role, pu.price 
            FROM purchases pu 
            JOIN players p ON pu.player_id = p.id 
            WHERE pu.team_name = ?
            ORDER BY 
              CASE p.role 
                WHEN 'P' THEN 1 
                WHEN 'D' THEN 2 
                WHEN 'C' THEN 3 
                WHEN 'A' THEN 4 
              END
        ''', (team_name,))
        return c.fetchall()

    def get_purchases_for_export(self, team_name: str) -> List[Tuple[int, int]]:
        """Restituisce lista di (player_id, price) per esportazione."""
        c = self.conn.cursor()
        c.execute("SELECT player_id, price FROM purchases WHERE team_name=?", (team_name,))
        return c.fetchall()

    def undo_last_purchase(self) -> Optional[Tuple[str, str, int]]:
        """Annulla l'ultimo acquisto e restituisce i dati dell'acquisto (player_name, team, price)."""
        c = self.conn.cursor()
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("SELECT id, player_id, team_name, price FROM purchases ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
            if not row:
                self.conn.rollback()
                return None
                
            purchase_id, pid, team, price = row
            c.execute("DELETE FROM purchases WHERE id=?", (purchase_id,))
            
            c.execute("SELECT name FROM players WHERE id=?", (pid,))
            pname_row = c.fetchone()
            pname = pname_row[0] if pname_row else str(pid)
            
            self.conn.commit()
            return (pname, team, price)
        except Exception:
            self.conn.rollback()
            raise

    def search_purchased_players(self, name_query: str = "", limit: int = 15) -> List[Tuple[int, str, str, str, str, int]]:
        """
        Cerca tra i giocatori acquistati per nome.
        Restituisce (player_id, player_name, player_real_team, player_role, fanta_team, price).
        Prova prima con prefisso (index-friendly), poi fallback a contains.
        """
        c = self.conn.cursor()
        base_query = '''
            SELECT p.id, p.name, p.team, p.role, pu.team_name, pu.price
            FROM purchases pu
            JOIN players p ON pu.player_id = p.id
            WHERE p.name LIKE ?
            ORDER BY pu.id DESC
            LIMIT ?
        '''
        # Prefisso prima
        c.execute(base_query, (name_query + '%', limit))
        results = c.fetchall()
        if len(results) < limit:
            existing_ids = {r[0] for r in results}
            c.execute(base_query, ('%' + name_query + '%', limit))
            for row in c.fetchall():
                if row[0] not in existing_ids:
                    results.append(row)
                    if len(results) >= limit:
                        break
        return results

    def remove_purchase_by_player(self, player_name: str, team_name: Optional[str] = None) -> Optional[Tuple[str, str, int]]:
        """
        Rimuove l'acquisto di uno specifico giocatore (opzionalmente filtrando per squadra acquirente).
        Restituisce (player_name, team_name, price) o None se non trovato.
        """
        c = self.conn.cursor()
        try:
            c.execute("BEGIN IMMEDIATE")
            if team_name:
                c.execute('''
                    SELECT pu.id, p.name, pu.team_name, pu.price 
                    FROM purchases pu
                    JOIN players p ON pu.player_id = p.id
                    WHERE LOWER(p.name) = LOWER(?) AND LOWER(pu.team_name) = LOWER(?)
                    ORDER BY pu.id DESC
                    LIMIT 1
                ''', (player_name, team_name))
            else:
                c.execute('''
                    SELECT pu.id, p.name, pu.team_name, pu.price 
                    FROM purchases pu
                    JOIN players p ON pu.player_id = p.id
                    WHERE LOWER(p.name) = LOWER(?)
                    ORDER BY pu.id DESC
                    LIMIT 1
                ''', (player_name,))
            row = c.fetchone()
            if not row:
                if team_name:
                    c.execute('''
                        SELECT pu.id, p.name, pu.team_name, pu.price 
                        FROM purchases pu
                        JOIN players p ON pu.player_id = p.id
                        WHERE p.name LIKE ? AND LOWER(pu.team_name) = LOWER(?)
                        ORDER BY pu.id DESC
                        LIMIT 1
                    ''', ('%' + player_name + '%', team_name))
                else:
                    c.execute('''
                        SELECT pu.id, p.name, pu.team_name, pu.price 
                        FROM purchases pu
                        JOIN players p ON pu.player_id = p.id
                        WHERE p.name LIKE ?
                        ORDER BY pu.id DESC
                        LIMIT 1
                    ''', ('%' + player_name + '%',))
                row = c.fetchone()

            if not row:
                self.conn.rollback()
                return None
                
            purchase_id, pname, tname, price = row
            c.execute("DELETE FROM purchases WHERE id=?", (purchase_id,))
            self.conn.commit()
            return (pname, tname, price)
        except Exception:
            self.conn.rollback()
            raise

    def get_purchase_by_player(self, player_name: str, team_name: Optional[str] = None) -> Optional[Tuple[int, str, str, int, str]]:
        """
        Recupera i dettagli di un acquisto (purchase_id, player_name, team_name, price, role) per nome giocatore.
        """
        c = self.conn.cursor()
        if team_name:
            c.execute('''
                SELECT pu.id, p.name, pu.team_name, pu.price, p.role 
                FROM purchases pu
                JOIN players p ON pu.player_id = p.id
                WHERE LOWER(p.name) = LOWER(?) AND LOWER(pu.team_name) = LOWER(?)
                ORDER BY pu.id DESC
                LIMIT 1
            ''', (player_name, team_name))
        else:
            c.execute('''
                SELECT pu.id, p.name, pu.team_name, pu.price, p.role 
                FROM purchases pu
                JOIN players p ON pu.player_id = p.id
                WHERE LOWER(p.name) = LOWER(?)
                ORDER BY pu.id DESC
                LIMIT 1
            ''', (player_name,))
        row = c.fetchone()
        if not row:
            if team_name:
                c.execute('''
                    SELECT pu.id, p.name, pu.team_name, pu.price, p.role 
                    FROM purchases pu
                    JOIN players p ON pu.player_id = p.id
                    WHERE p.name LIKE ? AND LOWER(pu.team_name) = LOWER(?)
                    ORDER BY pu.id DESC
                    LIMIT 1
                ''', ('%' + player_name + '%', team_name))
            else:
                c.execute('''
                    SELECT pu.id, p.name, pu.team_name, pu.price, p.role 
                    FROM purchases pu
                    JOIN players p ON pu.player_id = p.id
                    WHERE p.name LIKE ?
                    ORDER BY pu.id DESC
                    LIMIT 1
                ''', ('%' + player_name + '%',))
            row = c.fetchone()

        return row

    def update_purchase_price(self, purchase_id: int, new_price: int) -> None:
        """Aggiorna il prezzo di un acquisto dato il purchase_id."""
        c = self.conn.cursor()
        c.execute("UPDATE purchases SET price = ? WHERE id = ?", (new_price, purchase_id))
        self.conn.commit()

    def update_purchase_team(self, purchase_id: int, new_team_name: str) -> None:
        """Aggiorna la squadra proprietaria di un acquisto dato il purchase_id."""
        c = self.conn.cursor()
        c.execute("UPDATE purchases SET team_name = ? WHERE id = ?", (new_team_name, purchase_id))
        self.conn.commit()

    def backup_database(self, backup_filename: str) -> None:
        """Esegue un backup del database SQLite nel file specificato."""
        bck_conn = sqlite3.connect(backup_filename)
        self.conn.backup(bck_conn)
        bck_conn.close()

    def restore_database(self, backup_filename: str) -> None:
        """
        Ripristina il database SQLite dal file di backup specificato.
        Chiude e riapre la connessione per garantire uno stato pulito dopo il restore.
        """
        src_conn = sqlite3.connect(backup_filename)
        src_conn.backup(self.conn)
        src_conn.close()
        
        # Riapri la connessione per stato pulito (cursori, cache, pragma)
        self.conn.close()
        self.conn = sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False)
        try:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        self._init_tables()

    def clear_auction_data(self) -> None:
        """Svuota acquisti, team, configurazione e giocatori per un reset completo."""
        c = self.conn.cursor()
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM purchases")
            c.execute("DELETE FROM teams")
            c.execute("DELETE FROM config")
            c.execute("DELETE FROM players")
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # Mappatura delle colonne attese nel CSV del listone.
    # Chiave = nome campo interno, Valore = lista di possibili header (case-insensitive).
    _CSV_COLUMN_ALIASES: Dict[str, List[str]] = {
        'id':   ['#', 'id', 'cod', 'codice'],
        'name': ['nome', 'name', 'giocatore'],
        'team': ['sq.', 'sq', 'squadra', 'team'],
        'role': ['r.', 'r', 'ruolo', 'role'],
    }

    def _resolve_csv_columns(self, header: List[str]) -> Dict[str, int]:
        """
        Dato l'header del CSV, restituisce un dizionario {campo_interno: indice_colonna}.
        Solleva ValueError se una colonna obbligatoria non viene trovata.
        """
        header_lower = [h.strip().lower() for h in header]
        mapping: Dict[str, int] = {}

        for field, aliases in self._CSV_COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in header_lower:
                    mapping[field] = header_lower.index(alias)
                    break

        missing = [f for f in self._CSV_COLUMN_ALIASES if f not in mapping]
        if missing:
            raise ValueError(
                f"Colonne obbligatorie non trovate nell'header del CSV: {missing}. "
                f"Header rilevato: {header}"
            )
        return mapping

    def import_listone_csv(self, csv_path: str = 'listone.csv') -> Tuple[bool, int, str]:
        """
        Importa i giocatori dal CSV al database.
        Il CSV deve avere un header con le colonne: #/Id, Nome, Sq./Squadra, R./Ruolo.
        Restituisce (success, count, message).
        """
        if not os.path.exists(csv_path):
            return False, 0, f"File {csv_path} non trovato."
            
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM players")
        if c.fetchone()[0] > 0:
            return True, 0, "Listone già importato in precedenza."
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)

                if not header:
                    return False, 0, "Il file CSV è vuoto."

                # Rileva la mappatura delle colonne dall'header
                try:
                    col_map = self._resolve_csv_columns(header)
                except ValueError as ve:
                    return False, 0, str(ve)

                idx_id = col_map['id']
                idx_name = col_map['name']
                idx_team = col_map['team']
                idx_role = col_map['role']
                min_cols = max(idx_id, idx_name, idx_team, idx_role) + 1

                imported = 0
                for row in reader:
                    if len(row) < min_cols:
                        continue
                    try:
                        pid = int(row[idx_id])
                    except ValueError:
                        continue
                    name = row[idx_name].strip()
                    team = row[idx_team].strip()
                    role = row[idx_role].strip()
                    if not name:
                        continue
                    c.execute(
                        "INSERT OR REPLACE INTO players (id, name, team, role) VALUES (?, ?, ?, ?)",
                        (pid, name, team, role)
                    )
                    imported += 1

            self.conn.commit()
            return True, imported, "Listone importato con successo."
        except Exception as e:
            return False, 0, str(e)

    def get_last_purchase(self) -> Optional[Tuple[str, str, str, str, int, int]]:
        """Restituisce l'ultimo acquisto effettuato: (name, role, real_team, fanta_team, price, id)."""
        c = self.conn.cursor()
        c.execute('''
            SELECT p.name, p.role, p.team, pu.team_name, pu.price, pu.id 
            FROM purchases pu 
            JOIN players p ON pu.player_id = p.id 
            ORDER BY pu.id DESC 
            LIMIT 1
        ''')
        return c.fetchone()

    def get_recent_purchases(self, limit: int = 5) -> List[Tuple[str, str, str, str, int, int]]:
        """Restituisce gli ultimi N acquisti effettuati."""
        c = self.conn.cursor()
        c.execute('''
            SELECT p.name, p.role, p.team, pu.team_name, pu.price, pu.id 
            FROM purchases pu 
            JOIN players p ON pu.player_id = p.id 
            ORDER BY pu.id DESC 
            LIMIT ?
        ''', (limit,))
        return c.fetchall()

    def get_dashboard_teams_data(self) -> List[Dict]:
        """
        Recupera in un'unica struttura completa tutti i dati di tutte le squadre per la dashboard Streamlit.
        Ottimizzato: usa poche query aggregate invece di N query per squadra.
        """
        budget = self.get_config('budget', 500)
        teams = self.get_all_teams()
        if not teams:
            return []

        c = self.conn.cursor()

        # 1. Spesa e conteggio per ruolo per tutte le squadre in una query
        c.execute('''
            SELECT pu.team_name, p.role, COUNT(*) as cnt, SUM(pu.price) as total
            FROM purchases pu
            JOIN players p ON pu.player_id = p.id
            GROUP BY pu.team_name, p.role
        ''')
        # Struttura: {team: {role: (count, spent)}}
        team_role_data: Dict[str, Dict[str, Tuple[int, int]]] = {t: {} for t in teams}
        for team_name, role, cnt, total in c.fetchall():
            if team_name in team_role_data:
                team_role_data[team_name][role] = (cnt, total)

        # 2. Roster completo per tutte le squadre in una query
        c.execute('''
            SELECT pu.team_name, p.name, p.team, p.role, pu.price
            FROM purchases pu
            JOIN players p ON pu.player_id = p.id
            ORDER BY pu.team_name,
              CASE p.role WHEN 'P' THEN 1 WHEN 'D' THEN 2 WHEN 'C' THEN 3 WHEN 'A' THEN 4 END
        ''')
        team_rosters: Dict[str, List[Tuple[str, str, str, int]]] = {t: [] for t in teams}
        for team_name, pname, pteam, role, price in c.fetchall():
            if team_name in team_rosters:
                team_rosters[team_name].append((pname, pteam, role, price))

        # 3. Assembla il risultato
        data = []
        for team in teams:
            role_data = team_role_data[team]
            spent = sum(s for _, s in role_data.values())
            roster = team_rosters[team]

            data.append({
                'name': team,
                'spent': spent,
                'remaining': budget - spent,
                'budget': budget,
                'total_players': len(roster),
                'roles_count': {
                    'P': role_data.get('P', (0, 0))[0],
                    'D': role_data.get('D', (0, 0))[0],
                    'C': role_data.get('C', (0, 0))[0],
                    'A': role_data.get('A', (0, 0))[0],
                },
                'spending_by_role': {
                    'P': role_data.get('P', (0, 0))[1],
                    'D': role_data.get('D', (0, 0))[1],
                    'C': role_data.get('C', (0, 0))[1],
                    'A': role_data.get('A', (0, 0))[1],
                },
                'roster': roster
            })
        return data

    def get_free_players(self, role_filter: Optional[str] = None, search: str = "", limit: int = 200) -> List[Tuple[int, str, str, str]]:
        """Restituisce i giocatori ancora non acquistati (svincolati)."""
        c = self.conn.cursor()
        query = '''
            SELECT p.id, p.name, p.team, p.role 
            FROM players p 
            WHERE p.id NOT IN (SELECT player_id FROM purchases)
        '''
        params: List[object] = []
        if role_filter and role_filter != 'TUTTI':
            query += ' AND p.role = ?'
            params.append(role_filter)
        if search:
            query += ' AND p.name LIKE ?'
            params.append('%' + search + '%')
        query += ' ORDER BY p.role, p.name LIMIT ?'
        params.append(limit)
        
        c.execute(query, tuple(params))
        return c.fetchall()

    def close(self) -> None:
        """Chiude la connessione al database SQLite."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()


