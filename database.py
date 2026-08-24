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
        self.conn = sqlite3.connect(self.db_path)
        self._init_tables()

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
        """Cerca giocatori nel database per nome (autocompletamento)."""
        c = self.conn.cursor()
        c.execute("SELECT id, name, team, role FROM players WHERE name LIKE ? LIMIT ?", ('%' + name_query + '%', limit))
        return c.fetchall()

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

    def add_purchase(self, player_id: int, team_name: str, price: int) -> None:
        """Registra un acquisto nel database."""
        c = self.conn.cursor()
        c.execute("INSERT INTO purchases (player_id, team_name, price) VALUES (?, ?, ?)", (player_id, team_name, price))
        self.conn.commit()

    def get_teams_status(self) -> List[Tuple[str, int, int]]:
        """Restituisce lo stato (spesi, quanti giocatori) per ogni squadra."""
        status = []
        c = self.conn.cursor()
        for team in self.get_all_teams():
            c.execute("SELECT SUM(price), COUNT(id) FROM purchases WHERE team_name=?", (team,))
            res = c.fetchone()
            spent = res[0] or 0
            count = res[1] or 0
            status.append((team, spent, count))
        return status

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
        c.execute("SELECT id, player_id, team_name, price FROM purchases ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            return None
            
        purchase_id, pid, team, price = row
        c.execute("DELETE FROM purchases WHERE id=?", (purchase_id,))
        
        c.execute("SELECT name FROM players WHERE id=?", (pid,))
        pname_row = c.fetchone()
        pname = pname_row[0] if pname_row else str(pid)
        
        self.conn.commit()
        return (pname, team, price)

    def backup_database(self, backup_filename: str) -> None:
        """Esegue un backup del database SQLite nel file specificato."""
        bck_conn = sqlite3.connect(backup_filename)
        self.conn.backup(bck_conn)
        bck_conn.close()

    def restore_database(self, backup_filename: str) -> None:
        """Ripristina il database SQLite dal file di backup specificato."""
        src_conn = sqlite3.connect(backup_filename)
        src_conn.backup(self.conn)
        src_conn.close()

    def clear_auction_data(self) -> None:
        """Svuota gli acquisti, i team e la configurazione, mantenendo i giocatori."""
        c = self.conn.cursor()
        c.execute("DELETE FROM purchases")
        c.execute("DELETE FROM teams")
        c.execute("DELETE FROM config")
        self.conn.commit()

    def import_listone_csv(self, csv_path: str = 'listone.csv') -> Tuple[bool, int, str]:
        """
        Importa i giocatori dal CSV al database.
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
                next(reader, None) # skip header
                for row in reader:
                    if len(row) >= 4:
                        try:
                            pid = int(row[0])
                            name = row[1]
                            team = row[3]
                            role = row[5] if len(row) > 5 else ''
                            c.execute("INSERT OR REPLACE INTO players (id, name, team, role) VALUES (?, ?, ?, ?)", (pid, name, team, role))
                        except ValueError:
                            continue
            self.conn.commit()
            
            c.execute("SELECT COUNT(*) FROM players")
            count = c.fetchone()[0]
            return True, count, "Listone importato con successo."
        except Exception as e:
            return False, 0, str(e)
