import shlex
from prompt_toolkit.completion import Completer, Completion, CompleteEvent
from prompt_toolkit.document import Document
from database import FantaDatabase
from typing import Iterable

class FantaCompleter(Completer):
    """
    Gestisce l'autocompletamento in linea per prompt_toolkit.
    Suggerisce i comandi, i nomi dei calciatori e i nomi delle squadre in base al contesto.
    """
    
    def __init__(self, db: FantaDatabase) -> None:
        """
        Inizializza il completer.
        
        Args:
            db (FantaDatabase): L'istanza del database da cui leggere giocatori e squadre.
        """
        self.db = db
        self.commands = [
            'setup', 'buy', 'price', 'move', 'remove', 'status', 'recap_roles', 'recap_budget', 
            'roster', 'undo', 'export', 'backup', 'reset', 'restore', 'exit', 'help'
        ]

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        """
        Genera i suggerimenti per l'autocompletamento in base a ciò che l'utente sta scrivendo.
        """
        word = document.get_word_before_cursor(WORD=True)
        text_before = document.text_before_cursor

        # Completamento dei comandi base (se non ci sono spazi)
        if not ' ' in text_before:
            for cmd in self.commands:
                if cmd.startswith(word.lower()):
                    yield Completion(cmd, start_position=-len(word))
            return
            
        # Completamento intelligente per il comando 'buy'
        if text_before.startswith('buy '):
            try:
                # Gestiamo il caso in cui l'utente stia scrivendo dentro delle virgolette non chiuse
                to_parse = text_before
                if to_parse.count('"') % 2 != 0:
                    to_parse += '"'
                args = shlex.split(to_parse)
            except Exception:
                args = text_before.split()

            # Argomento 1: Nome Giocatore (stiamo scrivendo il secondo token)
            if len(args) == 2 or (len(args) == 1 and text_before.endswith(' ')):
                search = word.replace('"', '')
                if len(search) >= 2:
                    players = self.db.search_players_by_name(search, limit=15)
                    for pid, name, team, role in players:
                        name_esc = f'"{name}"'
                        display_text = f'[{role}] {name} ({team})'
                        yield Completion(name_esc, start_position=-len(word), display=display_text)
            
            # Argomento 2: Nome Squadra (stiamo scrivendo il terzo token)
            elif len(args) == 3 or (len(args) == 2 and text_before.endswith(' ')):
                search = word.replace('"', '')
                teams = self.db.search_teams_by_name(search)
                for team_name in teams:
                    # Se il nome della squadra ha spazi, lo avvolgiamo nelle virgolette per sicurezza
                    if ' ' in team_name:
                        team_name = f'"{team_name}"'
                    yield Completion(team_name, start_position=-len(word))

        # Completamento intelligente per il comando 'remove'
        elif text_before.startswith('remove '):
            try:
                to_parse = text_before
                if to_parse.count('"') % 2 != 0:
                    to_parse += '"'
                args = shlex.split(to_parse)
            except Exception:
                args = text_before.split()

            # Argomento 1: Nome Giocatore acquistato
            if len(args) == 2 or (len(args) == 1 and text_before.endswith(' ')):
                search = word.replace('"', '')
                purchased_players = self.db.search_purchased_players(search, limit=15)
                for pid, name, team, role, fanta_team, price in purchased_players:
                    name_esc = f'"{name}"'
                    display_text = f'[{role}] {name} ({fanta_team} - {price} cr)'
                    yield Completion(name_esc, start_position=-len(word), display=display_text)

            # Argomento 2: Nome Squadra (opzionale)
            elif len(args) == 3 or (len(args) == 2 and text_before.endswith(' ')):
                search = word.replace('"', '')
                teams = self.db.search_teams_by_name(search)
                for team_name in teams:
                    if ' ' in team_name:
                        team_name = f'"{team_name}"'
                    yield Completion(team_name, start_position=-len(word))

        # Completamento intelligente per il comando 'price' / 'edit_price'
        elif text_before.startswith('price ') or text_before.startswith('edit_price '):
            try:
                to_parse = text_before
                if to_parse.count('"') % 2 != 0:
                    to_parse += '"'
                args = shlex.split(to_parse)
            except Exception:
                args = text_before.split()

            # Argomento 1: Nome Giocatore acquistato
            if len(args) == 2 or (len(args) == 1 and text_before.endswith(' ')):
                search = word.replace('"', '')
                purchased_players = self.db.search_purchased_players(search, limit=15)
                for pid, name, team, role, fanta_team, price in purchased_players:
                    name_esc = f'"{name}"'
                    display_text = f'[{role}] {name} ({fanta_team} - {price} cr)'
                    yield Completion(name_esc, start_position=-len(word), display=display_text)

            # Argomento 3: Nome Squadra (opzionale, dopo il prezzo)
            elif len(args) == 4 or (len(args) == 3 and text_before.endswith(' ')):
                search = word.replace('"', '')
                teams = self.db.search_teams_by_name(search)
                for team_name in teams:
                    if ' ' in team_name:
                        team_name = f'"{team_name}"'
                    yield Completion(team_name, start_position=-len(word))

        # Completamento intelligente per il comando 'move'
        elif text_before.startswith('move '):
            try:
                to_parse = text_before
                if to_parse.count('"') % 2 != 0:
                    to_parse += '"'
                args = shlex.split(to_parse)
            except Exception:
                args = text_before.split()

            # Argomento 1: Nome Giocatore acquistato
            if len(args) == 2 or (len(args) == 1 and text_before.endswith(' ')):
                search = word.replace('"', '')
                purchased_players = self.db.search_purchased_players(search, limit=15)
                for pid, name, team, role, fanta_team, price in purchased_players:
                    name_esc = f'"{name}"'
                    display_text = f'[{role}] {name} ({fanta_team} - {price} cr)'
                    yield Completion(name_esc, start_position=-len(word), display=display_text)

            # Argomento 2: Nuova Squadra
            elif len(args) == 3 or (len(args) == 2 and text_before.endswith(' ')):
                search = word.replace('"', '')
                teams = self.db.search_teams_by_name(search)
                for team_name in teams:
                    if ' ' in team_name:
                        team_name = f'"{team_name}"'
                    yield Completion(team_name, start_position=-len(word))

            # Argomento 3: Vecchia Squadra (opzionale)
            elif len(args) == 4 or (len(args) == 3 and text_before.endswith(' ')):
                search = word.replace('"', '')
                teams = self.db.search_teams_by_name(search)
                for team_name in teams:
                    if ' ' in team_name:
                        team_name = f'"{team_name}"'
                    yield Completion(team_name, start_position=-len(word))



