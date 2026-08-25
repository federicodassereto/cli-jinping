import atexit
import shlex
import os
import sys
from datetime import datetime
from typing import List, Optional

try:
    from prompt_toolkit import PromptSession
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("Errore: mancano delle librerie ('prompt_toolkit' o 'rich').")
    print("Avvia l'applicazione tramite il file run.sh per installarle in automatico.")
    sys.exit(1)

from database import FantaDatabase
from completer import FantaCompleter

console = Console()

class FantaCLI:
    """
    Gestisce l'interfaccia utente a riga di comando per l'Asta del Fantacalcio,
    effettuando il parsing dei comandi e formattando l'output tramite Rich.
    """
    
    def __init__(self) -> None:
        """Inizializza la CLI, il database e l'autocompletamento."""
        self.db = FantaDatabase('asta.db')
        atexit.register(self.db.close)
        
        # Importazione del listone se disponibile
        success, count, msg = self.db.import_listone_csv('listone.csv')
        if success and count > 0:
            rprint(f"[bold green]{msg}[/bold green] ({count} giocatori)")
        elif not success:
            rprint(f"[bold red]Errore Listone: {msg}[/bold red]")
            
        self.session = PromptSession(completer=FantaCompleter(self.db))

    def run(self) -> None:
        """Avvia il loop principale dell'applicazione."""
        console.print("[bold cyan]Benvenuto nella CLI per l'Asta del Fantacalcio (Modular & Typed Edition).[/bold cyan]")
        console.print("Scrivi [bold yellow]help[/bold yellow] per la lista dei comandi.")
        
        while True:
            try:
                text = self.session.prompt('(fantaasta) > ')
                if not text.strip():
                    continue
                
                try:
                    args = shlex.split(text)
                except ValueError as e:
                    console.print(f"[bold red]Errore di sintassi (mancano virgolette?): {e}[/bold red]")
                    continue
                
                cmd = args[0].lower()
                self._dispatch_command(cmd, args[1:])
                    
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                console.print(f"[bold red]Errore imprevisto: {e}[/bold red]")

    def _dispatch_command(self, cmd: str, args: List[str]) -> None:
        """Esegue il comando richiesto."""
        if cmd == 'exit':
            console.print("[bold]Uscita in corso...[/bold]")
            sys.exit(0)
        elif cmd == 'help':
            self.do_help()
        elif cmd == 'setup':
            self.do_setup()
        elif cmd == 'buy':
            self.do_buy(args)
        elif cmd == 'status':
            self.do_status()
        elif cmd == 'recap_roles':
            self.do_recap_roles()
        elif cmd == 'recap_budget':
            self.do_recap_budget()
        elif cmd == 'roster':
            if len(args) < 1:
                console.print("[red]Uso: roster <nome_squadra>[/red]")
            else:
                self.do_roster(args[0])
        elif cmd == 'undo':
            self.do_undo()
        elif cmd == 'remove':
            self.do_remove(args)
        elif cmd == 'move':
            self.do_move(args)
        elif cmd in ('price', 'edit_price'):
            self.do_price(args)
        elif cmd == 'export':
            self.do_export(args[0] if args else 'rosters.csv')
        elif cmd == 'backup':
            self.do_backup(args[0] if args else None)
        elif cmd == 'reset':
            self.do_reset()
        elif cmd == 'restore':
            if len(args) < 1:
                console.print("[red]Uso: restore <nome_file.db>[/red]")
            else:
                self.do_restore(args[0])
        else:
            console.print(f"[red]Comando '{cmd}' non riconosciuto.[/red]")

    def do_help(self) -> None:
        """Mostra la tabella di aiuto."""
        table = Table(title="Comandi Disponibili", show_header=True, header_style="bold magenta", row_styles=["", "on grey15"])
        table.add_column("Comando", style="cyan")
        table.add_column("Descrizione", style="white")
        table.add_row("setup", "Configura budget iniziale e squadre.")
        table.add_row('buy "Giocatore" "Squadra" Prezzo', "Compra un giocatore.")
        table.add_row('price "Giocatore" Prezzo ["Squadra"]', "Modifica il prezzo di un giocatore acquistato.")
        table.add_row('move "Giocatore" "NuovaSquadra"', "Sposta un giocatore erroneamente assegnato a un'altra squadra.")
        table.add_row('remove "Giocatore" ["Squadra"]', "Rimuove l'acquisto di un giocatore specifico.")
        table.add_row("status", "Mostra i budget rimanenti e i giocatori totali.")
        table.add_row("recap_roles", "Tabella dei giocatori acquistati divisi per ruolo.")
        table.add_row("recap_budget", "Dettaglio spesa per ruolo (valore assoluto e percentuale).")
        table.add_row('roster "Squadra"', "Elenca i giocatori comprati da una squadra.")
        table.add_row("undo", "Annulla l'ultimo acquisto.")
        table.add_row("export [file.csv]", "Esporta in formato $,$,$ per app desktop.")
        table.add_row("backup [file.db]", "Forza il salvataggio manuale del database.")
        table.add_row("reset", "Azzera l'asta corrente, salvando un file di backup .db")
        table.add_row("restore [file.db]", "Ripristina un file di backup generato col reset.")
        table.add_row("exit", "Chiude l'applicazione.")
        console.print(table)

    def do_setup(self) -> None:
        """Configura interattivamente l'asta (budget e squadre)."""
        try:
            credits_str = input("Inserisci il numero di crediti iniziali (es. 500): ")
            credits_val = int(credits_str)
            self.db.set_config('budget', credits_val)
        except ValueError:
            console.print("[red]Errore: devi inserire un numero intero.[/red]")
            return

        choice = input("Vuoi leggere le squadre da un file di testo (S/N)? ").strip().lower()
        teams_list = []
        if choice == 's':
            filename = input("Inserisci il percorso del file: ")
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    teams_list = [line.strip() for line in f if line.strip()]
            else:
                console.print("[red]File non trovato.[/red]")
                return
        else:
            print("Inserisci i nomi delle squadre (lascia vuoto per terminare):")
            while True:
                t = input("> ").strip()
                if not t:
                    break
                teams_list.append(t)
        
        self.db.setup_teams(teams_list)
        
        # Importazione del listone se disponibile
        success, count, msg = self.db.import_listone_csv('listone.csv')
        if success and count > 0:
            rprint(f"[bold green]{msg}[/bold green] ({count} giocatori)")
        elif not success:
            rprint(f"[bold yellow]Attenzione Listone: {msg}[/bold yellow]")
        
        console.print("[bold green]Setup completato! Dati salvati nel database SQLite permanente.[/bold green]")

    def do_buy(self, args: List[str]) -> None:
        """Gestisce l'acquisto di un giocatore."""
        if len(args) < 3:
            console.print("[red]Errore. Uso: buy <giocatore> <squadra> <prezzo>[/red]")
            return
        
        player_query = args[0]
        team_name = args[1]
        
        try:
            price = int(args[2])
        except ValueError:
            console.print("[red]Errore: il prezzo deve essere un numero intero.[/red]")
            return
            
        if not self.db.team_exists(team_name):
            console.print(f"[red]Errore: squadra '{team_name}' non trovata.[/red]")
            return

        player_data = self.db.get_player_by_exact_name(player_query)
        if not player_data:
            console.print(f"[red]Errore: giocatore '{player_query}' non trovato nel database.[/red]")
            console.print("[yellow]Assicurati di usare l'autocompletamento (freccia su/giù e TAB).[/yellow]")
            return
            
        player_id, player_name, player_role = player_data

        # Verifica acquisto duplicato
        existing_team = self.db.is_player_purchased(player_id)
        if existing_team:
            console.print(f"[bold red]❌ Errore: {player_name} è già stato acquistato da '{existing_team}'.[/bold red]")
            return

        # Verifica limiti ruolo
        role_limits = {'P': 3, 'D': 8, 'C': 8, 'A': 6}
        current_count = self.db.count_team_role(team_name, player_role)
        max_allowed = role_limits.get(player_role, 0)
        
        if max_allowed > 0 and current_count >= max_allowed:
            console.print(f"[bold red]❌ Errore: La squadra {team_name} ha già raggiunto il limite massimo ({max_allowed}) per il ruolo {player_role}.[/bold red]")
            return

        # Verifica budget
        budget = self.db.get_config('budget', 500)
        spent = self.db.get_team_spent(team_name)
        
        if spent + price > budget:
            console.print(f"[bold yellow]Attenzione: la squadra {team_name} non ha abbastanza crediti (Rimanenti: {budget - spent}).[/bold yellow]")
            confirm = input("Procedere lo stesso? (S/N) ").strip().lower()
            if confirm != 's':
                return
        
        self.db.add_purchase(player_id, team_name, price)
        console.print(f"[bold green]✅ {player_name} [{player_role}] assegnato a {team_name} per {price} crediti.[/bold green] ({current_count + 1}/{max_allowed} nel ruolo)")

    def do_status(self) -> None:
        """Mostra il budget e i giocatori totali per ogni squadra."""
        status_data = self.db.get_teams_status()
        if not status_data:
            console.print("[red]Nessuna squadra configurata. Usa il comando 'setup'.[/red]")
            return
            
        budget = self.db.get_config('budget', 500)
        table = Table(title="Stato Generale Squadre", header_style="bold magenta", row_styles=["", "on grey15"])
        table.add_column("Squadra", style="cyan", no_wrap=True)
        table.add_column("Spesi", justify="right", style="red")
        table.add_column("Rimanenti", justify="right", style="green")
        table.add_column("Giocatori", justify="right", style="yellow")
        
        for team, spent, count in status_data:
            rem = budget - spent
            table.add_row(team, str(spent), str(rem), str(count))
            
        console.print(table)

    def do_recap_roles(self) -> None:
        """Mostra quanti giocatori ha ogni squadra divisi per ruolo."""
        teams = self.db.get_all_teams()
        if not teams:
            console.print("[red]Nessuna squadra configurata.[/red]")
            return
            
        table = Table(title="Riepilogo Ruoli (Giocatori Acquistati)", header_style="bold magenta", row_styles=["", "on grey15"])
        table.add_column("Squadra", style="cyan", no_wrap=True)
        table.add_column("Portieri", justify="center")
        table.add_column("Difensori", justify="center")
        table.add_column("Centrocampisti", justify="center")
        table.add_column("Attaccanti", justify="center")
        
        def format_role(count: int, max_val: int) -> str:
            color = "green" if count == max_val else "white"
            return f"[{color}]{count}/{max_val}[/{color}]"
            
        for team in teams:
            counts = self.db.get_roles_count_by_team(team)
            p = format_role(counts.get('P', 0), 3)
            d = format_role(counts.get('D', 0), 8)
            c_m = format_role(counts.get('C', 0), 8)
            a = format_role(counts.get('A', 0), 6)
            table.add_row(team, p, d, c_m, a)
            
        console.print(table)

    def do_recap_budget(self) -> None:
        """Mostra la spesa in crediti e % per ogni ruolo."""
        budget = self.db.get_config('budget', 500)
        teams = self.db.get_all_teams()
        if not teams:
            console.print("[red]Nessuna squadra configurata.[/red]")
            return
            
        table = Table(title="Dettaglio Spesa per Reparto", header_style="bold magenta", row_styles=["", "on grey15"])
        table.add_column("Squadra", style="cyan", no_wrap=True)
        table.add_column("Tot Speso", justify="right", style="bold red")
        table.add_column("Portieri", justify="right")
        table.add_column("Difensori", justify="right")
        table.add_column("Centrocampisti", justify="right")
        table.add_column("Attaccanti", justify="right")
        
        def format_spent(spent: int, total_budget: int) -> str:
            if spent == 0:
                return "-"
            pct = (spent / total_budget * 100) if total_budget > 0 else 0
            return f"{spent} ({pct:.1f}%)"
            
        for team in teams:
            spent_by_role = self.db.get_spending_by_role(team)
            total_spent = sum(spent_by_role.values())
            
            p = format_spent(spent_by_role.get('P', 0), budget)
            d = format_spent(spent_by_role.get('D', 0), budget)
            c_m = format_spent(spent_by_role.get('C', 0), budget)
            a = format_spent(spent_by_role.get('A', 0), budget)
            
            tot_str = f"{total_spent} (Rimanenti: {budget - total_spent})"
            table.add_row(team, tot_str, p, d, c_m, a)
            
        console.print(table)

    def do_roster(self, team_name: str) -> None:
        """Stampa la rosa di una squadra."""
        rows = self.db.get_roster(team_name)
        if not rows:
            console.print(f"[yellow]Nessun giocatore acquistato da {team_name}.[/yellow]")
            return
            
        table = Table(title=f"Roster: {team_name.upper()}", header_style="bold magenta", row_styles=["", "on grey15"])
        table.add_column("Ruolo", justify="center")
        table.add_column("Nome", style="cyan")
        table.add_column("Squadra A", style="white")
        table.add_column("Costo", justify="right", style="bold red")
        
        role_colors = {'P': 'yellow', 'D': 'green', 'C': 'blue', 'A': 'red'}
        
        for name, real_team, role, price in rows:
            role_fmt = f"[{role_colors.get(role, 'white')}]{role}[/{role_colors.get(role, 'white')}]"
            table.add_row(role_fmt, name, real_team, str(price))
            
        console.print(table)

    def do_export(self, filename: str) -> None:
        """Esporta in formato rosters.csv per fantaasta desktop."""
        try:
            teams = self.db.get_all_teams()
            with open(filename, 'w', encoding='utf-8') as f:
                for team in teams:
                    f.write("$,$,$\n")
                    purchases = self.db.get_purchases_for_export(team)
                    for pid, price in purchases:
                        f.write(f"{team},{pid},{price}\n")
            console.print(f"[bold green]Esportazione completata con successo nel file '{filename}'.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Errore durante l'esportazione: {e}[/bold red]")

    def do_backup(self, filename: Optional[str] = None) -> None:
        """Esegue un dump manuale del database sqlite."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_asta_{timestamp}.db"
            
        try:
            self.db.backup_database(filename)
            console.print(f"[bold green]Backup del database creato con successo in: {filename}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Errore durante il backup del database: {e}[/bold red]")

    def do_undo(self) -> None:
        """Annulla l'ultimo acquisto inserito."""
        result = self.db.undo_last_purchase()
        if not result:
            console.print("[yellow]Nessun acquisto da annullare nel database.[/yellow]")
            return
            
        pname, team, price = result
        console.print(f"[bold yellow]Annullato l'acquisto di {pname} per {team} a {price} crediti.[/bold yellow]")

    def do_remove(self, args: List[str]) -> None:
        """Rimuove l'acquisto di uno specifico giocatore (opzionalmente filtrando per squadra)."""
        if len(args) < 1:
            console.print("[red]Uso: remove <nome_giocatore> [nome_squadra][/red]")
            return

        player_name = args[0]
        team_name = args[1] if len(args) > 1 else None

        result = self.db.remove_purchase_by_player(player_name, team_name)
        if not result:
            if team_name:
                console.print(f"[yellow]Nessun acquisto trovato per il giocatore '{player_name}' nella squadra '{team_name}'.[/yellow]")
            else:
                console.print(f"[yellow]Nessun acquisto trovato per il giocatore '{player_name}'.[/yellow]")
            return

        pname, team, price = result
        console.print(f"[bold yellow]🗑️  Rimosso l'acquisto di {pname} da {team} ({price} crediti restituiti).[/bold yellow]")

    def do_price(self, args: List[str]) -> None:
        """Modifica il prezzo di un acquisto effettuato."""
        if len(args) < 2:
            console.print("[red]Uso: price <nome_giocatore> <nuovo_prezzo> [nome_squadra][/red]")
            return

        player_name = args[0]
        try:
            new_price = int(args[1])
            if new_price < 0:
                console.print("[red]Errore: il prezzo deve essere maggiore o uguale a 0.[/red]")
                return
        except ValueError:
            console.print("[red]Errore: il nuovo prezzo deve essere un numero intero.[/red]")
            return

        team_name = args[2] if len(args) > 2 else None

        purchase = self.db.get_purchase_by_player(player_name, team_name)
        if not purchase:
            if team_name:
                console.print(f"[yellow]Nessun acquisto trovato per il giocatore '{player_name}' nella squadra '{team_name}'.[/yellow]")
            else:
                console.print(f"[yellow]Nessun acquisto trovato per il giocatore '{player_name}'.[/yellow]")
            return

        purchase_id, pname, tname, old_price, role = purchase

        if new_price == old_price:
            console.print(f"[yellow]Il prezzo di {pname} per {tname} è già {new_price} crediti.[/yellow]")
            return

        # Verifica budget se il nuovo prezzo è più alto
        diff = new_price - old_price
        if diff > 0:
            budget = self.db.get_config('budget', 500)
            spent = self.db.get_team_spent(tname)
            if spent + diff > budget:
                console.print(f"[bold yellow]Attenzione: con questo aumento ({old_price} ➔ {new_price}) la squadra {tname} sfora il budget (Rimanenti: {budget - spent}, richiesti: +{diff}).[/bold yellow]")
                confirm = input("Procedere lo stesso? (S/N) ").strip().lower()
                if confirm != 's':
                    return

        self.db.update_purchase_price(purchase_id, new_price)
        diff_str = f"+{diff}" if diff > 0 else f"{diff}"
        console.print(f"[bold green]💰 Prezzo di {pname} ({tname}) aggiornato: {old_price} ➔ {new_price} crediti ({diff_str}).[/bold green]")

    def do_move(self, args: List[str]) -> None:
        """Sposta un giocatore acquistato da una squadra a un'altra."""
        if len(args) < 2:
            console.print("[red]Uso: move <nome_giocatore> <nuova_squadra> [vecchia_squadra][/red]")
            return

        player_name = args[0]
        new_team = args[1]
        old_team_filter = args[2] if len(args) > 2 else None

        if not self.db.team_exists(new_team):
            console.print(f"[red]Errore: la squadra di destinazione '{new_team}' non esiste.[/red]")
            return

        purchase = self.db.get_purchase_by_player(player_name, old_team_filter)
        if not purchase:
            if old_team_filter:
                console.print(f"[yellow]Nessun acquisto trovato per il giocatore '{player_name}' nella squadra '{old_team_filter}'.[/yellow]")
            else:
                console.print(f"[yellow]Nessun acquisto trovato per il giocatore '{player_name}'.[/yellow]")
            return

        purchase_id, pname, old_team, price, role = purchase

        if old_team.lower() == new_team.lower():
            console.print(f"[yellow]Il giocatore {pname} appartiene già alla squadra {new_team}.[/yellow]")
            return

        # Verifica limiti di ruolo per la nuova squadra
        role_limits = {'P': 3, 'D': 8, 'C': 8, 'A': 6}
        current_count = self.db.count_team_role(new_team, role)
        max_allowed = role_limits.get(role, 0)

        if max_allowed > 0 and current_count >= max_allowed:
            console.print(f"[bold red]❌ Errore: La squadra di destinazione {new_team} ha già raggiunto il limite massimo ({max_allowed}) per il ruolo {role}.[/bold red]")
            return

        # Verifica budget per la nuova squadra
        budget = self.db.get_config('budget', 500)
        spent = self.db.get_team_spent(new_team)

        if spent + price > budget:
            console.print(f"[bold yellow]Attenzione: la squadra di destinazione {new_team} non ha abbastanza crediti (Rimanenti: {budget - spent}, prezzo giocatore: {price}).[/bold yellow]")
            confirm = input("Procedere lo stesso? (S/N) ").strip().lower()
            if confirm != 's':
                return

        self.db.update_purchase_team(purchase_id, new_team)
        console.print(f"[bold green]🔄 {pname} [{role}] spostato con successo da '{old_team}' a '{new_team}' (Costo: {price} crediti).[/bold green]")



    def do_reset(self) -> None:
        """Esegue backup e svuota le tabelle per riniziare l'asta."""
        confirm = input("Sei sicuro di voler resettare tutta l'asta? (Verrà creato un backup) [S/N]: ").strip().lower()
        if confirm != 's':
            console.print("[yellow]Reset annullato.[/yellow]")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_asta_{timestamp}.db"
        
        try:
            self.db.backup_database(backup_name)
            console.print(f"[bold green]Backup di sicurezza salvato in: {backup_name}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Errore nella creazione del backup: {e}[/bold red]")
            return

        self.db.clear_auction_data()
        console.print("[bold yellow]L'asta è stata resettata completamente (incluso il listone giocatori). Digita 'setup' per reimportare il listone e iniziare una nuova asta.[/bold yellow]")

    def do_restore(self, filename: str) -> None:
        """Sovrascrive il DB attuale con un DB di backup."""
        if not os.path.exists(filename):
            console.print(f"[bold red]File di backup '{filename}' non trovato.[/bold red]")
            return
            
        confirm = input(f"Sei sicuro di voler sovrascrivere i dati attuali ripristinando '{filename}'? [S/N]: ").strip().lower()
        if confirm != 's':
            console.print("[yellow]Ripristino annullato.[/yellow]")
            return
            
        try:
            self.db.restore_database(filename)
            console.print(f"[bold green]Dati ripristinati con successo dal file {filename}![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Errore durante il ripristino: {e}[/bold red]")

if __name__ == '__main__':
    FantaCLI().run()
