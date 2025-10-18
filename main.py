import json

class UserAccount:
    def __init__(self, username: str, password: str, pin: int, balance: float = 0.0) -> None:
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
            "amount": amount
        })
    
    def withdraw(self, amount: float) -> None:
        if amount <= 0: raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance: raise ValueError("Insufficient balance.")
        self.balance -= amount
        self.transaction_history.append({
            "type": "withdrawal",
            "amount": amount
        })
    
    def transfer(self, amount: float, recipient_account) -> None:
        if amount <= 0: raise ValueError("Transfer amount must be positive.")
        if amount > self.balance: raise ValueError("Insufficient balance.")
        self.balance -= amount
        recipient_account.balance += amount
        self.transaction_history.append({
            "type": "transfer",
            "amount": amount,
            "to": recipient_account.username
        })

def main() -> None:
    with open('accounts.json', 'r') as f:
        accounts_data = json.load(f)
    accounts = {}
    for username, data in accounts_data.items():
        accounts[username] = UserAccount(
            username,
            data['password'],
            data['pin'],
            data['balance']
        )
        accounts[username].transaction_history = data['transaction_history']
    
    print("Welcome to the Bank of Bankers!\n")
    print("1 - Login")
    print("2 - Sign Up")
    choice = input("Choose an option: ")
    if choice == '1':
        username = input("Username: ")
        password = input("Password: ")
        if username in accounts and accounts[username].password == password:
            user_account = accounts[username]
            print(f"Welcome back, {username}!")
        else:
            print("Invalid username or password.")
            return
    elif choice == '2':
        username = input("Choose a username: ")
        if username in accounts:
            print("Username already exists.")
            return
        password = input("Choose a password: ")
        pin = int(input("Choose a 4-digit PIN: "))
        
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
        print(f"Account created for {username}!")
    else:
        print("Invalid choice.")
        return

if __name__ == "__main__":
    main()