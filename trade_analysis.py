def simulate_trades(buy_trades, sell_trades, initial_hbd=6):
    """
    Simulates trades based on buy and sell trades using an initial portfolio of HBD.
    Avoids forced selling and provides an estimated portfolio value.
    """
    hbd_balance = initial_hbd  # Start with 6 HBD
    hive_balance = 0  # Initially, no HIVE owned
    trade_log = []  # To log all trades
    portfolio_value = []  # To track portfolio value over time

    for i in range(len(buy_trades)):
        # Get current buy and sell prices
        current_buy_price = buy_trades[i]['price']  # HBD per HIVE
        current_sell_price = sell_trades[i]['price']  # HBD per HIVE

        # Decision: Buy HIVE
        if hbd_balance > 0 and current_buy_price < current_sell_price:
            # Buy as much HIVE as possible with available HBD
            hive_purchased = hbd_balance / current_buy_price
            hbd_balance = 0  # All HBD spent
            hive_balance += hive_purchased
            trade_log.append(
                f"Bought {hive_purchased:.4f} HIVE at {current_buy_price:.6f} HBD per HIVE."
            )

        # Decision: Sell HIVE
        elif hive_balance > 0 and current_sell_price > current_buy_price:
            # Sell all HIVE for HBD
            hbd_earned = hive_balance * current_sell_price
            hive_balance = 0  # All HIVE sold
            hbd_balance += hbd_earned
            trade_log.append(
                f"Bought {hbd_earned:.4f} HBD at {current_sell_price:.6f} HBD per HIVE."
            )

        # Track portfolio value (in HBD terms, estimating HIVE using sell price)
        estimated_value = hbd_balance + (hive_balance * current_sell_price)
        portfolio_value.append(estimated_value)

    # Final Portfolio Evaluation
    # Use the last known sell price to estimate HIVE value
    final_estimated_value = hbd_balance + (hive_balance * current_sell_price)
    initial_value = initial_hbd
    profit_or_loss = final_estimated_value - initial_value

    return {
        "trade_log": trade_log,
        "initial_value": initial_value,
        "final_estimated_value": final_estimated_value,
        "profit_or_loss": profit_or_loss,
        "portfolio_value": portfolio_value,
    }


