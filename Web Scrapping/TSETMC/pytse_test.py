from pytse.pytse import PyTse , SymbolData

if __name__ == "__main__":
    pytse = PyTse()  # read_symbol_data=True,read_client_type=False
    pytse.read_client_type()  # در صورت نیاز به اطلاعات حقیقی
    symbols = pytse.symbols_data
    # print(symbols)
    symbol = symbols["IRO1MAPN0001"]
    symbol.fill_data()  # درصورت نیاز به اطلاعات "میانگین حجم ماه" و "سهام شناور" فرخوانی شود
    print(symbol.ct.Sell_N_Volume)