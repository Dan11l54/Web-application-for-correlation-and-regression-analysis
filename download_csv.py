import yfinance as yf
import pandas as pd

# Задаем тикер и период
ticker_symbol = "AAPL"
start_date = "2023-05-01"
end_date = "2025-05-01"

# Скачиваем данные
data = yf.download(ticker_symbol, start=start_date, end=end_date)

# Сохраняем в CSV
data.to_csv(f"{ticker_symbol}_data.csv")
print(f"Данные для {ticker_symbol} сохранены в {ticker_symbol}_data.csv")

# Для примера скачаем еще одну бумагу для корреляции
ticker_symbol_2 = "MSFT"
data2 = yf.download(ticker_symbol_2, start=start_date, end=end_date)
data2.to_csv(f"{ticker_symbol_2}_data.csv")
print(f"Данные для {ticker_symbol_2} сохранены в {ticker_symbol_2}_data.csv")