import json
import os
import sys
from collections import Counter
from getpass import getpass
from datetime import datetime

def clear_screen() -> None:
    try:
        print("\033[2J\033[H", end="", flush=True)
    except Exception:
        pass
    if os.name == "nt":
        try:
            os.system("cls")
        except Exception:
            pass

def pause(msg: str = "Press Enter to continue...") -> None:
    try:
        input(msg)
    except EOFError:
        pass

def render_header(title: str, subtitle: str | None = None) -> None:
    clear_screen()
    print(f"=== {title} ===")
    if subtitle:
        print(subtitle)
    print()

class UserAccount:
    def __init__(self, username: str, password: str, pin: str, balance: float = 0.0) -> None:
        self.username = username
        self.password = password
        self.pin = pin
        self.balance = balance
        self.transaction_history = []
    
    def deposit(self, amount: float) -> None:
        if amount <= 0: raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.transaction_history.append({
            "type": "deposit",
            "amount": amount,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def withdraw(self, amount: float) -> None:
        if amount <= 0: raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance: raise ValueError("Insufficient balance.")
        self.balance -= amount
        self.transaction_history.append({
            "type": "withdrawal",
            "amount": amount,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def transfer(self, amount: float, recipient_account) -> None:
        if amount <= 0: raise ValueError("Transfer amount must be positive.")
        if amount > self.balance: raise ValueError("Insufficient balance.")
        self.balance -= amount
        recipient_account.balance += amount
        self.transaction_history.append({
            "type": "transfer",
            "amount": amount,
            "to": recipient_account.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        recipient_account.transaction_history.append({
            "type": "transfer",
            "amount": amount,
            "from": self.username,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

def get_top_payees(user: UserAccount, limit: int = 3) -> list[str]:
    counts = Counter()

    for t in user.transaction_history:
        if t.get("type") == "transfer" and "to" in t:
            counts[t["to"]] += 1

    return [uname for uname, _ in counts.most_common(limit)]


def _save_accounts(accounts: dict, filepath: str = 'accounts.json') -> None:
    data = {}
    for uname, acct in accounts.items():
        data[uname] = {
            'password': acct.password,
            'pin': acct.pin,
            'balance': acct.balance,
            'transaction_history': acct.transaction_history,
        }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def verify_pin(user: UserAccount):
    pin_input = getpass("Enter your 4-digit PIN to confirm (or 'b' to back): ").strip()

    if pin_input.lower() in ('b', 'back'):
        return False, "Operation cancelled by user."

    if not pin_input.isdigit() or len(pin_input) != 4:
        return False, "PIN must be a 4-digit number."

    if pin_input != str(user.pin):
        return False, "Incorrect PIN."

    return True, ""

def user_session(user: UserAccount, accounts: dict) -> None:
    status = ""
    while True:
        render_header(
            title=f"Bank of Bankers — {user.username}",
            subtitle="Logged in (Ctrl+C to exit app)"
        )
        if status:
            print(status)
            print()
        print("1) Check Balance")
        print("2) Deposit")
        print("3) Withdraw")
        print("4) Transfer")
        print("5) View Transaction History")
        print("6) Logout")
        choice = input("\nChoose an option: ").strip()
        status = ""

        if choice == '1':
            status = f"Current balance: ${user.balance:.2f}"
        elif choice == '2':
            ok, msg = verify_pin(user)
            if not ok:
                status = f"Deposit cancelled. {msg}"
            else:
                try:
                    amount_str = input("Amount to deposit (or 'b' to back): ").strip()
                    if amount_str.lower() in ('b', 'back'):
                        status = "Deposit cancelled."
                    else:
                        amount = float(amount_str)
                        user.deposit(amount)
                        _save_accounts(accounts)
                        status = f"Deposited ${amount:.2f}. New balance: ${user.balance:.2f}"
                except Exception as e:
                    status = f"Deposit failed: {e}"
        elif choice == '3':
            ok, msg = verify_pin(user)
            if not ok:
                status = f"Withdrawal cancelled. {msg}"
            else:
                try:
                    amount_str = input("Amount to withdraw (or 'b' to back): ").strip()
                    if amount_str.lower() in ('b', 'back'):
                        status = "Withdrawal cancelled."
                    else:
                        amount = float(amount_str)
                        user.withdraw(amount)
                        _save_accounts(accounts)
                        status = f"Withdrew ${amount:.2f}. New balance: ${user.balance:.2f}"
                except Exception as e:
                    status = f"Withdrawal failed: {e}"
        elif choice == '4':
            ok, msg = verify_pin(user)
            if not ok:
                status = f"Transfer cancelled. {msg}"
                continue

            top_payees = get_top_payees(user)

            print()

            if top_payees:
                print("Your top payees:")
                for i, payee in enumerate(top_payees, start=1):
                    print(f"  {i}) {payee}")
                print("\nYou can enter 1–3 to pick a payee above,")
                print("or type a username manually.")
            else:
                print("You don't have any payees yet.")
                print("Type the recipient's username to make your first transfer.")

            print()
            recipient_choice = input("Recipient (username or 1–3, or 'b' to back): ").strip()
            if recipient_choice.lower() in ('b', 'back'):
                continue

            recipient = None
            if recipient_choice.isdigit() and top_payees:
                index = int(recipient_choice)
                if 1 <= index <= len(top_payees):
                    recipient = top_payees[index - 1]
                elif 1 <= index <= 3:
                    status = "Invalid payee selection."
                    continue

            if recipient is None:
                recipient = recipient_choice

            if recipient not in accounts:
                status = "No such recipient."
            elif recipient == user.username:
                status = "Cannot transfer to yourself."
            else:
                try:
                    amount_str = input("Amount to transfer (or 'b' to back): ").strip()
                    if amount_str.lower() in ('b', 'back'):
                        status = "Transfer cancelled."
                    else:
                        amount = float(amount_str)
                        user.transfer(amount, accounts[recipient])
                        _save_accounts(accounts)
                        status = (
                            f"Transferred ${amount:.2f} to {recipient}. "
                            f"New balance: ${user.balance:.2f}"
                        )
                except Exception as e:
                    status = f"Transfer failed: {e}"
        elif choice == '5':
            render_header(title=f"{user.username} — Transactions")
            if not user.transaction_history:
                print("No transactions yet.")
            else:
                for i, t in enumerate(user.transaction_history, 1):
                    t_type = t.get('type', '?').title()
                    amount = t.get('amount', 0)
                    date_str = t.get('date', 'Unknown Date')
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        date_display = dt.strftime("%y-%m-%d %H:%M")
                    except ValueError:
                        date_display = date_str
                    
                    details = ""
                    if t.get('type') == 'transfer':
                        if 'to' in t:
                            details += f" -> {t['to']}"
                        if 'from' in t:
                            details += f" <- {t['from']}"
                    print(f"{i}. [{date_display}] {t_type}: ${amount:.2f}{details}")
            print()
            pause()
        elif choice == '6':
            return
        else:
            status = "Invalid choice."

def main() -> None:
    try:
        with open('accounts.json', 'r') as f:
            accounts_data = json.load(f)
    except FileNotFoundError:
        accounts_data = {}
    
    accounts = {}
    for username, data in accounts_data.items():
        accounts[username] = UserAccount(
            username,
            data['password'],
            data['pin'],
            data['balance']
        )
        accounts[username].transaction_history = data.get('transaction_history', [])
    
    status = ""
    while True:
        render_header(
            title="Bank of Bankers",
            subtitle="Main Menu (Ctrl+C to exit app)"
        )
        if status:
            print(status)
            print()
        print("1) Login")
        print("2) Sign Up")
        choice = input("\nChoose an option: ").strip()
        status = ""
        
        if choice == '1':
            username = input("Username (or 'b' to back): ").strip()
            if username.lower() in ('b', 'back'):
                continue
            password = getpass("Password (or 'b' to back): ").strip()
            if password.lower() in ('b', 'back'):
                continue
            if username in accounts and accounts[username].password == password:
                print(f"\nWelcome back, {username}!")
                pause("Press Enter to continue...")
                user_session(accounts[username], accounts)
                status = f"Logged out {username}."
            else:
                status = "Invalid username or password."
        elif choice == '2':
            username = input("Choose a username (or 'b' to back): ").strip()
            if username.lower() in ('b', 'back'):
                continue
            if username in accounts:
                status = "Username already exists."
                continue
            password = getpass("Choose a password (or 'b' to back): ").strip()
            if password.lower() in ('b', 'back'):
                continue
            try:
                pin = getpass("Choose a 4-digit PIN: ").strip()
            except ValueError:
                status = "PIN must be numeric."
                continue
            
            new_account = UserAccount(username, password, pin)
            accounts[username] = new_account
            accounts_data[username] = {
                'password': password,
                'pin': pin,
                'balance': 0.0,
                'transaction_history': []
            }
            with open('accounts.json', 'w') as f:
                json.dump(accounts_data, f, indent=4)
            status = f"Account created for {username}!"
        else:
            status = "Invalid choice."

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("Goodbye!")
        sys.exit(0)