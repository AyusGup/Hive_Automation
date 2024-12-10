import time
from datetime import datetime, timedelta
from beem.market import Market
from beem.account import Account
from beem import Steem
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

STEEM_NODE = os.getenv("STEEM_NODE")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ACCOUNT_NAME = os.getenv("ACCOUNT_NAME")
BufferError = float(os.getenv("BufferError"))

# Initialize Steem instance
steem = Steem(node=STEEM_NODE, keys=[PRIVATE_KEY])
market = Market(base="HBD", quote="HIVE", steem_instance=steem)

# Track last trade prices
last_buy_price = None
last_sell_price = None

def fetch_recent_trades(last_fetch_time=None, limit=200, batch_size=1000):
    """
    Fetch recent trades starting from last_fetch_time + 2 minutes.
    """
    all_trades = []
    
    if last_fetch_time is None:
        end_time = datetime.utcnow()
    else:
        end_time = last_fetch_time + timedelta(minutes=2)

    while len(all_trades) < limit:
        batch_limit = min(batch_size, limit - len(all_trades))
        start_time = end_time - timedelta(hours=1)

        trades = market.trades(limit=batch_limit, start=start_time, stop=end_time)
        if not trades:
            break

        all_trades.extend(trades)
        end_time = trades[-1]['date']  # Update the end time based on the last trade in the batch

    buy_trades, sell_trades = [], []

    for trade in all_trades:
        trade_data = trade.json()
        current_pays = float(trade_data['current_pays']['amount']) / (10 ** trade_data['current_pays']['precision'])
        open_pays = float(trade_data['open_pays']['amount']) / (10 ** trade_data['current_pays']['precision'])
        timestamp = trade_data['date']

        if trade_data['current_pays']['nai'] == '@@000000021':  # HIVE sold for HBD
            price = open_pays / current_pays
            buy_trades.append({'timestamp': timestamp, 'price': price, 'volume': current_pays})
        elif trade_data['current_pays']['nai'] == '@@000000013':  # HBD sold for HIVE
            price = current_pays / open_pays
            sell_trades.append({'timestamp': timestamp, 'price': price, 'volume': open_pays})

    return buy_trades, sell_trades, end_time


def predict_next_prices_with_history(buy_trades, sell_trades, last_buy_price, last_sell_price, interval_minutes=2):
    """
    Predict next buy and sell prices based on trends, historical trade prices, and recent prices.
    """
    buy_prices = [trade['price'] for trade in buy_trades]
    sell_prices = [trade['price'] for trade in sell_trades]

    # Calculate average prices over the interval
    avg_buy_price = sum(buy_prices[-interval_minutes:]) / len(buy_prices[-interval_minutes:]) if len(buy_prices) >= interval_minutes else 0
    avg_sell_price = sum(sell_prices[-interval_minutes:]) / len(sell_prices[-interval_minutes:]) if len(sell_prices) >= interval_minutes else 0

    # Fetch the most recent prices
    recent_buy_price = buy_prices[-1] if buy_prices else 0
    recent_sell_price = sell_prices[-1] if sell_prices else 0

    # Combine average and recent prices in a 0.7:0.3 ratio
    predicted_buy_price = (0.7 * avg_buy_price + 0.3 * recent_buy_price) if avg_buy_price and recent_buy_price else 0
    predicted_sell_price = (0.7 * avg_sell_price + 0.3 * recent_sell_price) if avg_sell_price and recent_sell_price else 0

    # Adjust predictions based on historical prices
    if last_sell_price and predicted_buy_price >= last_sell_price:
        predicted_buy_price = last_sell_price * 0.98  # Aim to buy slightly lower than the last sell price

    if last_buy_price and predicted_sell_price <= last_buy_price:
        predicted_sell_price = last_buy_price * 1.02  # Aim to sell slightly higher than the last buy price

    return predicted_buy_price, predicted_sell_price



def execute_trade(action, amount, price):
    """
    Executes a buy or sell order and waits for the transaction to complete before returning.
    """
    account = ACCOUNT_NAME  # Your account name
    print(f"Attempting to {action.upper()} {amount} HIVE at {price} HBD.")

    try:
        # Execute the trade
        if action == "buy":
            transaction = market.buy(price, amount, account=account)
            print(f"Executed BUY order: {amount} HIVE at {price} HBD.")
        elif action == "sell":
            transaction = market.sell(price, amount, account=account)
            print(f"Executed SELL order: {amount} HIVE at {price} HBD.")
        else:
            raise ValueError(f"Invalid action '{action}'. Use 'buy' or 'sell'.")

        # Extract transaction ID
        transaction_id = transaction.get("trx_id")
        if not transaction_id:
            print("Transaction ID not found. Transaction details:")
            print(transaction)
            return False

        print(f"Transaction ID: {transaction_id}")
        
        # Wait for the transaction to be confirmed
        # confirmation = wait_for_transaction_confirmation(transaction_id)
        # if confirmation:
        #     print(f"Transaction {transaction_id} confirmed successfully!")
        # else:
        #     print(f"Transaction {transaction_id} failed to confirm or timed out.")
        return True

    except Exception as e:
        print(f"Error during {action.upper()} transaction: {e}")
        return False


def wait_for_transaction_confirmation(transaction_id):
    """
    Waits for the transaction to be included in a block.
    Returns True if the transaction is confirmed within the timeout, False otherwise.
    """
    while True:
        try:
            # Query the blockchain to check if the transaction is included in a block
            tx = steem.get_transaction(transaction_id)
            if tx:
                print(f"Transaction {transaction_id} confirmed in block {tx['block_num']}!")
                return True
        except Exception as e:
            print(f"Error checking transaction {transaction_id}: {e}")
            return False
        
        print(f"Waiting for transaction {transaction_id} to be confirmed...")
        time.sleep(5)  # Check every 2 seconds

def fetch_real_time_balance():
    """
    Fetch real-time balances of HBD and HIVE from the account.
    """
    account = Account(ACCOUNT_NAME, steem_instance=steem)
    hbd_balance = account.get_balance('available', 'HBD') 
    hive_balance = account.get_balance('available', 'HIVE') 
    
    return hbd_balance.amount - BufferError, hive_balance.amount - BufferError


def real_trading_with_history():
    """
    Perform real trading with historical price consideration.
    """
    global last_buy_price, last_sell_price
    last_fetch_time = None

    while True:
        try:
            # Fetch real-time account balance
            hbd_balance, hive_balance = fetch_real_time_balance()
            print(f"Current Balance: HBD: {hbd_balance}, HIVE: {hive_balance}")

            # Fetch trades
            buy_trades, sell_trades, last_fetch_time = fetch_recent_trades(last_fetch_time=last_fetch_time)

            # Predict prices considering history
            predicted_buy_price, predicted_sell_price = predict_next_prices_with_history(
                buy_trades, sell_trades, last_buy_price, last_sell_price
            )

            # Fetch the latest market prices

            ticker = market.ticker()
            current_buy_price = ticker['highest_bid']
            current_sell_price = ticker['lowest_ask']

            print(f"Predicted Buy Price: {predicted_buy_price}")
            print(f"Predicted Sell Price: {predicted_sell_price}")
            print(f"Current Buy Price: {current_buy_price}")
            print(f"Current Sell Price: {current_sell_price}")
            print(f"Last Buy Price: {last_buy_price}")
            print(f"Last Sell Price: {last_sell_price}")

            # Decision: Buy HIVE
            if hbd_balance > 0 and predicted_buy_price >= current_buy_price:
                hive_purchased = hbd_balance / predicted_buy_price
                if execute_trade("buy", hive_purchased, predicted_buy_price):
                   hbd_balance, hive_balance = fetch_real_time_balance()
                else:
                   print("Buy transaction failed. Balances not updated.")

            # Decision: Sell HIVE
            if hive_balance > 0 and predicted_sell_price <= current_sell_price:
                if execute_trade("sell", hive_balance, predicted_sell_price):
                    hbd_balance, hive_balance = fetch_real_time_balance()
                else:
                    print("Buy transaction failed. Balances not updated.")

            print(f"Portfolio: HBD: {hbd_balance}, HIVE: {hive_balance}")

            # Wait for 2 minutes before fetching new trades
            time.sleep(120)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    real_trading_with_history()
