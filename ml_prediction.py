from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import pandas as pd
import numpy as np

def prepare_features(trade_details):
    """Prepare features and labels for machine learning."""
    df = pd.DataFrame(trade_details)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp')

    # Create features like percentage change and rolling averages
    df['price_change'] = df['price'].pct_change()
    df['rolling_avg'] = df['price'].rolling(window=5).mean()
    df['rolling_std'] = df['price'].rolling(window=5).std()
    df.dropna(inplace=True)

    # Features and target
    features = df[['price_change', 'rolling_avg', 'rolling_std']]
    target = df['price']
    return features, target

def train_model(trade_details):
    """Train the regression model."""
    features, target = prepare_features(trade_details)
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    # Evaluate the model
    r2_score = model.score(X_test, y_test)
    print(f"Model R^2 Score: {r2_score:.2f}")

    return model, features

def predict_next_10_prices(model, features):
    """Predict the next 10 prices."""
    # Use the last known data as a seed for prediction
    last_feature = features.iloc[-1:].values

    predictions = []
    for _ in range(10):
        predicted_price = model.predict(last_feature)[0]
        predictions.append(predicted_price)

        # Update the features with the predicted value for the next step
        price_change = (predicted_price - last_feature[0][0]) / last_feature[0][0] if last_feature[0][0] != 0 else 0
        rolling_avg = (last_feature[0][1] * 4 + predicted_price) / 5  # Update rolling average
        rolling_std = np.std(predictions[-5:]) if len(predictions) >= 5 else 0  # Rolling std for last 5 predictions

        last_feature = [[price_change, rolling_avg, rolling_std]]

    return predictions
