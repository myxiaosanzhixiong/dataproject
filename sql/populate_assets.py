"""
Populate Assets table with real stock data from yfinance.
Covers S&P 500, major HK stocks, ETFs, FX, Futures, Bonds.
"""
import yfinance as yf
import pymysql
import time

DB = dict(host="127.0.0.1", port=3307, user="trader",
          password="traderpass123", database="portfolio_mgmt",
          cursorclass=pymysql.cursors.DictCursor, autocommit=True)

# ── Ticker lists ─────────────────────────────────────────────
SP500 = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","BRK-B","LLY","AVGO","TSLA",
    "JPM","UNH","XOM","V","MA","COST","HD","PG","JNJ","ABBV",
    "MRK","CRM","BAC","ORCL","CVX","MCD","NFLX","KO","PEP","TMO",
    "ACN","ADBE","WMT","LIN","ABT","MS","GE","AMD","PM","TXN",
    "CSCO","DHR","ISRG","GS","RTX","AMGN","HON","INTU","BLK","BKNG",
    "PFE","SYK","VRTX","SPGI","T","MDT","DE","LOW","CAT","SCHW",
    "CB","MMC","PLD","GILD","TJX","C","ETN","BSX","SO","BDX",
    "DUK","AON","ZTS","REGN","ICE","CME","WM","NOC","PNC","USB",
    "ITW","FCX","MCO","TGT","FI","AXP","OXY","MO","HCA","PSA",
    "ELV","CI","KMB","NSC","APD","EMR","ADI","KLAC","LRCX","SNPS",
    "CDNS","MCHP","TEL","FDX","GD","MMM","NKE","SBUX","MDLZ","CL",
    "ADP","HUM","TFC","MTB","WFC","WELL","DLR","EQR","AVB","SPG",
    "VTR","HIG","AFL","ALL","TRV","MET","PRU","LHX","TDG","FICO",
    "IDXX","IQV","A","DXCM","MTCH","ANSS","ENPH","ALGN","CZR","MGM",
    "LVS","WYNN","MAR","HLT","CCL","RCL","NCLH","DAL","UAL","AAL",
    "LUV","BA","GE","HON","UPS","FDX","JBHT","XPO","R","CHRW",
    "EOG","PXD","DVN","HAL","SLB","BKR","MPC","PSX","VLO","COP",
    "WMB","KMI","OKE","ET","EPD","TRGP","LNG","EXC","NEE","AEP",
    "PCG","PEG","ED","ES","WEC","DTE","CMS","NI","ATO","SRE",
]

HK = [
    "0700.HK","0941.HK","1299.HK","0005.HK","2318.HK","0388.HK",
    "2628.HK","1398.HK","0939.HK","3988.HK","0883.HK","0002.HK",
    "0003.HK","0006.HK","0016.HK","0027.HK","0066.HK","0688.HK",
    "0762.HK","1038.HK","1044.HK","1088.HK","1093.HK","1177.HK",
    "1928.HK","2020.HK","2269.HK","2382.HK","2899.HK","3690.HK",
    "9988.HK","9618.HK","9999.HK","0291.HK","1810.HK",
]

ETF = [
    "SPY","QQQ","IWM","DIA","VTI","VOO","VEA","VWO","EEM","GLD",
    "SLV","USO","UNG","TLT","IEF","SHY","HYG","LQD","VNQ","XLF",
    "XLK","XLE","XLV","XLI","XLY","XLP","XLU","XLB","XLRE","XLC",
    "ARKK","ARKG","ARKW","ARKF","ARKQ","SOXX","SMH","XBI","IBB","HACK",
    "KWEB","MCHI","FXI","EWJ","EWG","EWU","EWC","EWA","EWZ","RSX",
    "GOVT","TIPS","VTIP","BND","AGG","MUB","EMB","BNDX",
]

FX = [
    "EURUSD=X","GBPUSD=X","USDJPY=X","USDCAD=X","AUDUSD=X","NZDUSD=X",
    "USDCHF=X","USDCNY=X","USDHKD=X","USDSGD=X","USDINR=X","USDKRW=X",
    "EURGBP=X","EURJPY=X","GBPJPY=X","AUDJPY=X","CADJPY=X",
]

FUTURES = [
    "ES=F","NQ=F","YM=F","RTY=F","GC=F","SI=F","CL=F","NG=F",
    "ZB=F","ZN=F","ZF=F","ZT=F","HG=F","PL=F","PA=F",
    "ZC=F","ZS=F","ZW=F","KC=F","SB=F","CT=F","CC=F",
]

ASSET_CLASS_MAP = {
    "equity": ["AAPL","MSFT"],  # fallback
}

def get_asset_class(ticker, info):
    qt = info.get("quoteType","")
    if qt == "EQUITY":       return "equity"
    if qt == "ETF":          return "etf"
    if qt == "FUTURE":       return "derivative"
    if qt == "CURRENCY":     return "fx"
    if qt == "BOND":         return "bond"
    if ticker.endswith("=X"): return "fx"
    if ticker.endswith("=F"): return "derivative"
    if ticker.endswith(".HK"): return "equity"
    return "equity"

def get_market(ticker, info):
    ex = info.get("exchange","")
    mapping = {
        "NMS":"NASDAQ","NGM":"NASDAQ","NCM":"NASDAQ",
        "NYQ":"NYSE","NYB":"NYSE","PCX":"NYSE",
        "HKG":"HKEX","SHH":"SSE","SHZ":"SZSE",
        "LSE":"LSE","FRA":"FSE","TOR":"TSX","ASX":"ASX",
    }
    if ticker.endswith("=X"): return "OTC"
    if ticker.endswith("=F"): return "CME"
    return mapping.get(ex, ex or "NYSE")

def upsert_asset(cur, ticker, name, asset_class, market, currency, price):
    cur.execute("SELECT asset_id FROM Assets WHERE ticker=%s", (ticker,))
    existing = cur.fetchone()
    if existing:
        cur.execute(
            "UPDATE Assets SET name=%s, asset_class=%s, market=%s, currency=%s, last_price=%s, price_updated_at=NOW(), status='active' WHERE ticker=%s",
            (name, asset_class, market, currency, price, ticker)
        )
        return "updated"
    else:
        cur.execute(
            "INSERT INTO Assets (ticker, name, asset_class, market, currency, last_price, price_updated_at, status) VALUES (%s,%s,%s,%s,%s,%s,NOW(),'active')",
            (ticker, name, asset_class, market, currency, price)
        )
        return "inserted"

def process_batch(tickers, label):
    print(f"\n── {label} ({len(tickers)} tickers) ──")
    ok = err = 0
    conn = pymysql.connect(**DB)
    cur  = conn.cursor()

    # yfinance batch download for speed
    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        try:
            data = yf.download(batch, period="2d", interval="1d",
                               group_by="ticker", progress=False, threads=True, auto_adjust=True)
        except Exception as e:
            print(f"  batch download error: {e}")
            continue

        for tk in batch:
            try:
                # Get last close price
                if len(batch) == 1:
                    price_series = data["Close"]
                else:
                    price_series = data[tk]["Close"] if tk in data else None

                if price_series is None or price_series.dropna().empty:
                    err += 1
                    continue

                price = float(price_series.dropna().iloc[-1])
                if price <= 0:
                    err += 1
                    continue

                # Fetch info (name, exchange, etc.)
                try:
                    info = yf.Ticker(tk).fast_info
                    name = getattr(info, "display_name", None) or tk
                    currency = getattr(info, "currency", "USD") or "USD"
                except:
                    name = tk
                    currency = "USD"

                # Determine fields
                asset_class = get_asset_class(tk, {})
                if tk.endswith("=X"): asset_class = "fx"
                if tk.endswith("=F"): asset_class = "derivative"
                if tk.endswith(".HK"): asset_class = "equity"

                market = "NYSE"
                if tk.endswith("=X"): market = "OTC"
                if tk.endswith("=F"): market = "CME"
                if tk.endswith(".HK"): market = "HKEX"

                # Clean ticker for DB (remove =X =F suffix display)
                display = tk.replace("=X","").replace("=F","")

                action = upsert_asset(cur, display, name or display, asset_class, market, currency, round(price,4))
                print(f"  {action:8s} {display:12s} {price:>12.4f} {currency}")
                ok += 1
            except Exception as e:
                print(f"  ERROR {tk}: {e}")
                err += 1

        time.sleep(0.3)

    conn.close()
    print(f"  Done: {ok} ok, {err} failed")
    return ok

if __name__ == "__main__":
    total = 0
    total += process_batch(SP500,   "S&P 500")
    total += process_batch(HK,      "Hong Kong")
    total += process_batch(ETF,     "ETFs")
    total += process_batch(FX,      "FX Pairs")
    total += process_batch(FUTURES, "Futures")
    print(f"\n✓ Total assets processed: {total}")

    # Final count
    conn = pymysql.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM Assets WHERE status='active'")
        print(f"✓ Total active assets in DB: {cur.fetchone()['cnt']}")
    conn.close()
