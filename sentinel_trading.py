"""
📈 SENTINEL — TRADING AGENT
Analyse les marchés et propose des ordres via Discord.
- Connexion Interactive Brokers via ib_insync
- Signaux H4 (EMA 50/200 + RSI)
- DCA mensuel automatique
- Détection dips > 5%
- JAMAIS d'exécution sans validation Samet ✅/❌
"""

import os, json, time, requests, schedule, threading
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify
from groq import Groq

try:
    from ib_insync import IB, Stock, MarketOrder, LimitOrder, util
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    print("⚠️ ib_insync non installé — mode yfinance uniquement")

import sys
sys.path.append(os.path.dirname(__file__))
from sentinel_config import *

# ─── INIT ─────────────────────────────────────────────────
app  = Flask(__name__)
groq = Groq(api_key=GROQ_API_KEY)
ib   = IB() if IB_AVAILABLE else None

JOURNAL = Path("trading_journal.json")

# ─── HELPERS ──────────────────────────────────────────────
def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def load_journal() -> dict:
    if JOURNAL.exists():
        return json.loads(JOURNAL.read_text())
    return {"trades": [], "signals": [], "portfolio": {}, "stats": {}}

def save_journal(j: dict):
    JOURNAL.write_text(json.dumps(j, indent=2, ensure_ascii=False))

def log_signal(symbol: str, action: str, price: float, reason: str):
    j = load_journal()
    j["signals"].append({
        "time": now_str(), "symbol": symbol,
        "action": action, "price": price, "reason": reason
    })
    j["signals"] = j["signals"][-100:]
    save_journal(j)

def send_discord(title: str, fields: list, color: int = 0xC9A84C):
    embed = {
        "title": title, "color": color, "fields": fields,
        "footer": {"text": f"📈 SENTINEL Trading • {now_str()}"},
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
    except Exception as e:
        print(f"❌ Discord : {e}")

def report_to_manager(message: str, details: dict = None):
    try:
        requests.post(f"{MANAGER_URL}/report",
                      json={"agent": "trading_agent", "message": message, "details": details or {}},
                      headers={"X-Secret": AGENT_SECRET}, timeout=10)
    except:
        pass

def send_signal_to_manager(symbol: str, action: str, price: float,
                            amount: float, reason: str):
    """Envoie signal au Manager — qui demande validation à Samet"""
    try:
        requests.post(f"{MANAGER_URL}/trade_signal",
                      json={"symbol": symbol, "action": action,
                            "price": price, "amount": amount, "reason": reason},
                      headers={"X-Secret": AGENT_SECRET}, timeout=10)
        print(f"📡 Signal → Manager : {action} {symbol}")
    except Exception as e:
        print(f"❌ Manager injoignable : {e}")
        # Fallback : envoyer directement sur Discord
        send_discord(f"📈 Signal {action.upper()} {symbol}", [
            {"name": "💰 Prix",    "value": f"{price}$",    "inline": True},
            {"name": "💵 Montant", "value": f"{amount}€",   "inline": True},
            {"name": "💡 Raison",  "value": reason,          "inline": False},
            {"name": "⚠️ Note",   "value": "Manager offline — signal direct", "inline": False},
        ], color=0x2ECC71 if action == "buy" else 0xE74C3C)

# ─── GROQ — ANALYSE ───────────────────────────────────────
def ask_groq(prompt: str) -> str:
    try:
        r = groq.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {"role": "system",
                 "content": "Tu es le Trading Agent de SENTINEL, expert en investissement éthique. "
                             "Tu analyses les signaux techniques pour proposer des ordres sur ETFs éthiques. "
                             "Tes analyses sont courtes, précises, en français."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250, temperature=0.2
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Analyse indisponible: {e}"

def groq_signal_analysis(symbol: str, rsi: float, ema_cross: str,
                          change_pct: float, price: float) -> str:
    return ask_groq(
        f"Actif : {symbol} | Prix : {price}$ | Variation : {change_pct:+.1f}%\n"
        f"RSI : {rsi:.1f} | Signal EMA : {ema_cross}\n"
        f"Est-ce un bon signal d'achat pour un investissement DCA éthique long terme ? "
        f"Donne une recommandation claire en 2 phrases."
    )

def groq_dca_advice(portfolio_summary: str) -> str:
    return ask_groq(
        f"Portefeuille actuel : {portfolio_summary}\n"
        f"DCA mensuel de 50€ à distribuer. "
        f"Quels actifs prioriser ce mois-ci et pourquoi ? (2 phrases max)"
    )

def groq_market_context() -> str:
    return ask_groq(
        f"Date : {datetime.now().strftime('%d/%m/%Y')}. "
        f"Quel est le contexte macro actuel pour un investisseur éthique long terme ? "
        f"Points clés en 2 phrases."
    )

# ─── CONNEXION IB ─────────────────────────────────────────
def connect_ib() -> bool:
    if not IB_AVAILABLE or not ib:
        return False
    try:
        if ib.isConnected():
            return True
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID, timeout=10)
        print(f"✅ IB connecté — {IB_HOST}:{IB_PORT}")
        return True
    except Exception as e:
        print(f"❌ IB connexion échouée : {e}")
        return False

def get_ib_positions() -> dict:
    """Récupère les positions depuis IB"""
    positions = {}
    if not connect_ib():
        return positions
    try:
        for pos in ib.positions():
            symbol = pos.contract.symbol
            positions[symbol] = {
                "qty":    pos.position,
                "avg":    round(pos.avgCost, 2),
                "value":  round(pos.position * pos.avgCost, 2)
            }
    except Exception as e:
        print(f"❌ IB positions : {e}")
    return positions

def get_ib_cash() -> float:
    """Récupère le cash disponible"""
    if not connect_ib():
        return 0.0
    try:
        account = ib.accountValues()
        for av in account:
            if av.tag == "CashBalance" and av.currency == "EUR":
                return float(av.value)
    except:
        pass
    return 0.0

# ─── DONNÉES MARCHÉ ───────────────────────────────────────
def get_price(symbol: str) -> dict:
    try:
        info = yf.Ticker(symbol).fast_info
        return {
            "price":  round(info.get("lastPrice", 0), 2),
            "change": round(info.get("regularMarketChangePercent", 0), 2),
        }
    except:
        return {"price": 0, "change": 0}

def get_ohlcv(symbol: str, period: str = "3mo", interval: str = "1h") -> pd.DataFrame:
    """Récupère les données OHLCV pour analyse technique"""
    try:
        df = yf.download(symbol, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        return df
    except:
        return pd.DataFrame()

# ─── INDICATEURS TECHNIQUES ───────────────────────────────
def calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2) if not rsi.empty else 50.0

def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def get_signal(symbol: str) -> dict:
    """
    Signal H4 basé sur EMA 50/200 + RSI
    Retourne: action, raison, force
    """
    df = get_ohlcv(symbol, period="6mo", interval="4h")
    if df.empty or len(df) < 200:
        return {"action": "hold", "reason": "Données insuffisantes", "strength": 0}

    close    = df["Close"]
    ema50    = calc_ema(close, 50)
    ema200   = calc_ema(close, 200)
    rsi      = calc_rsi(close)
    price    = float(close.iloc[-1])
    prev_e50 = float(ema50.iloc[-2])
    prev_e200= float(ema200.iloc[-2])
    curr_e50 = float(ema50.iloc[-1])
    curr_e200= float(ema200.iloc[-1])

    # Golden Cross → achat
    if prev_e50 < prev_e200 and curr_e50 >= curr_e200 and rsi < 70:
        strength = min(100, int((curr_e50 - curr_e200) / curr_e200 * 10000))
        return {
            "action":   "buy",
            "reason":   f"Golden Cross EMA50/200 | RSI {rsi:.0f}",
            "strength": strength,
            "rsi":      rsi,
            "ema_cross":"golden_cross",
            "price":    price
        }

    # Death Cross → éviter
    if prev_e50 > prev_e200 and curr_e50 <= curr_e200:
        return {
            "action":   "hold",
            "reason":   f"Death Cross EMA50/200 | RSI {rsi:.0f} — Attendre",
            "strength": 0,
            "rsi":      rsi,
            "ema_cross":"death_cross",
            "price":    price
        }

    # RSI oversold (< 30) → opportunité
    if rsi < 30:
        return {
            "action":   "buy",
            "reason":   f"RSI oversold {rsi:.0f} — Opportunité de rebond",
            "strength": int((30 - rsi) * 3),
            "rsi":      rsi,
            "ema_cross":"neutral",
            "price":    price
        }

    return {
        "action":   "hold",
        "reason":   f"Pas de signal clair | RSI {rsi:.0f}",
        "strength": 0,
        "rsi":      rsi,
        "ema_cross":"neutral",
        "price":    price
    }

# ─── SCAN PRINCIPAL ───────────────────────────────────────
def scan_all_assets():
    """Scanne tous les actifs du portefeuille"""
    print(f"\n📊 Scan des actifs — {now_str()}")
    signals_found = []

    for symbol in list(PORTFOLIO.keys()):
        if symbol not in VALIDATED_ASSETS:
            continue

        print(f"  → {symbol}...")
        sig = get_signal(symbol)

        if sig["action"] == "buy" and sig["strength"] > 20:
            # Analyse Groq du signal
            analysis = groq_signal_analysis(
                symbol, sig["rsi"], sig["ema_cross"],
                get_price(symbol)["change"], sig["price"]
            )

            # Calcule le montant selon l'allocation cible
            cash    = get_ib_cash() or DCA_AMOUNT
            amount  = min(round(cash * MAX_POSITION_PCT, 2),
                         round(DCA_AMOUNT * PORTFOLIO[symbol], 2))
            amount  = max(amount, 5.0)  # Min 5€

            if amount < MIN_CASH:
                print(f"  ⏭️ {symbol} — Cash insuffisant ({amount}€ < {MIN_CASH}€)")
                continue

            log_signal(symbol, "buy", sig["price"], sig["reason"])
            signals_found.append({
                "symbol": symbol, "price": sig["price"],
                "amount": amount, "reason": analysis
            })

            # Envoie au Manager pour décision Samet
            send_signal_to_manager(
                symbol  = symbol,
                action  = "buy",
                price   = sig["price"],
                amount  = amount,
                reason  = f"{sig['reason']}\n🧠 {analysis}"
            )
            time.sleep(2)

    if signals_found:
        report_to_manager(
            f"{len(signals_found)} signaux détectés",
            {"signals": [{"symbol": s["symbol"], "price": s["price"]}
                         for s in signals_found]}
        )
    else:
        print("  ℹ️ Aucun signal fort aujourd'hui")

    return signals_found

def check_dips():
    """Détecte les dips > DIP_THRESHOLD"""
    print("📉 Vérification dips...")
    for symbol in VALIDATED_ASSETS[:10]:
        data = get_price(symbol)
        if data["change"] / 100 <= DIP_THRESHOLD and data["price"] > 0:
            cash   = get_ib_cash() or DCA_AMOUNT
            amount = round(min(cash * MAX_POSITION_PCT, DCA_AMOUNT * 0.5), 2)

            analysis = groq_signal_analysis(
                symbol, 50, "dip_detected", data["change"], data["price"]
            )

            log_signal(symbol, "dip", data["price"], f"Dip {data['change']:.1f}%")
            send_signal_to_manager(
                symbol  = symbol,
                action  = "buy",
                price   = data["price"],
                amount  = amount,
                reason  = f"DIP {data['change']:+.1f}% | {analysis}"
            )
            print(f"  📉 Dip détecté : {symbol} {data['change']:+.1f}%")

# ─── DCA MENSUEL ──────────────────────────────────────────
def run_dca():
    """Propose le DCA mensuel — exécution après validation Samet"""
    if datetime.now().day != 1:
        return

    print("💰 DCA mensuel...")
    prices = {s: get_price(s) for s in PORTFOLIO}
    positions = get_ib_positions()

    # Groq conseil allocation
    portfolio_summary = ", ".join(
        f"{s}: {d['price']}$ ({d['change']:+.1f}%)"
        for s, d in prices.items()
    )
    advice = groq_dca_advice(portfolio_summary)
    context = groq_market_context()

    # Calcule la distribution DCA
    dca_plan = []
    for symbol, alloc in PORTFOLIO.items():
        amount = round(DCA_AMOUNT * alloc, 2)
        price  = prices.get(symbol, {}).get("price", 0)
        if price > 0 and amount >= 1.0:
            dca_plan.append({
                "symbol": symbol, "amount": amount,
                "price": price, "shares": round(amount / price, 4)
            })

    # Rapport Discord DCA
    send_discord("💰 DCA Mensuel — Proposition", [
        {"name": "💵 Budget total",   "value": f"**{DCA_AMOUNT}€**",  "inline": True},
        {"name": "📅 Date",          "value": now_str(),               "inline": True},
        {"name": "🧠 Conseil IA",    "value": advice,                  "inline": False},
        {"name": "🌍 Contexte macro","value": context,                 "inline": False},
        {"name": "📋 Distribution",
         "value": "\n".join(
             f"**{p['symbol']}** : {p['amount']}€ → ~{p['shares']} parts"
             for p in dca_plan
         ), "inline": False},
        {"name": "⚠️ Action requise","value": "Valide via Manager ✅/❌", "inline": False},
    ], color=0xC9A84C)

    # Signale au Manager pour validation globale
    report_to_manager("DCA mensuel prêt pour validation", {
        "total": DCA_AMOUNT,
        "plan":  dca_plan
    })

# ─── RAPPORT QUOTIDIEN ────────────────────────────────────
def daily_report():
    print("📊 Rapport trading quotidien...")
    positions = get_ib_positions()
    j = load_journal()
    recent_signals = j["signals"][-5:]

    context = groq_market_context()

    fields = [
        {"name": "🧠 Contexte IA", "value": context, "inline": False},
        {"name": "📊 Positions IB",
         "value": "\n".join(
             f"**{s}** : {d['qty']} parts | {d['value']}€"
             for s, d in positions.items()
         ) if positions else "Aucune position ou IB offline",
         "inline": False},
        {"name": "📈 Derniers signaux",
         "value": "\n".join(
             f"**{s['symbol']}** {s['action']} @ {s['price']}$"
             for s in recent_signals
         ) if recent_signals else "Aucun signal récent",
         "inline": False},
        {"name": "💰 Cash dispo", "value": f"**{get_ib_cash():.2f}€**", "inline": True},
    ]
    send_discord("📈 Rapport Trading Quotidien — SENTINEL", fields, color=0x3B82F6)

# ─── API FLASK ────────────────────────────────────────────
def check_secret():
    return request.headers.get("X-Secret") == AGENT_SECRET

@app.route("/health")
def health():
    ib_status = "✅ Connecté" if (IB_AVAILABLE and connect_ib()) else "❌ Offline"
    return jsonify({
        "status": "online", "agent": "trading",
        "ib": ib_status, "time": now_str()
    })

@app.route("/task", methods=["POST"])
def receive_task():
    """Reçoit une instruction du Manager"""
    if not check_secret():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    task = data.get("task", "")
    dta  = data.get("data", {})

    print(f"📨 Tâche reçue du Manager : {task}")

    if task == "mode_prudent":
        send_discord("🛡️ Mode Prudent activé", [
            {"name": "⚠️ Raison", "value": dta.get("reason", "Marché baissier"), "inline": False},
            {"name": "📋 Action", "value": "Scan des actifs suspendu temporairement", "inline": False},
        ], color=0xF59E0B)
        return jsonify({"status": "ok"})

    if task == "analyze_signal":
        symbol = dta.get("symbol", "")
        if symbol:
            threading.Thread(
                target=lambda: scan_all_assets(), daemon=True
            ).start()
        return jsonify({"status": "started"})

    if task == "run_dca":
        threading.Thread(target=run_dca, daemon=True).start()
        return jsonify({"status": "started"})

    if task == "scan_now":
        threading.Thread(target=scan_all_assets, daemon=True).start()
        return jsonify({"status": "started"})

    return jsonify({"status": "unknown_task"})

@app.route("/execute", methods=["POST"])
def execute_order():
    """
    Exécute un ordre approuvé par Samet.
    UNIQUEMENT après validation via Discord ✅
    """
    if not check_secret():
        return jsonify({"error": "Unauthorized"}), 401

    data   = request.json
    symbol = data.get("symbol", "")
    action = data.get("action", "")
    amount = float(data.get("amount", 0))
    price  = float(data.get("price", 0))

    # Double vérification actif validé
    if symbol not in VALIDATED_ASSETS:
        return jsonify({"error": f"{symbol} non validé"}), 400

    # Double vérification montant
    if amount > DCA_AMOUNT * 2:
        return jsonify({"error": "Montant trop élevé"}), 400

    print(f"🔐 Ordre approuvé : {action} {symbol} {amount}€")

    j = load_journal()
    j["trades"].append({
        "time": now_str(), "symbol": symbol,
        "action": action, "amount": amount, "price": price,
        "status": "approved_by_samet"
    })
    save_journal(j)

    send_discord(f"✅ Ordre Exécuté — {action.upper()} {symbol}", [
        {"name": "💰 Montant", "value": f"**{amount}€**",  "inline": True},
        {"name": "💲 Prix",   "value": f"**{price}$**",   "inline": True},
        {"name": "✅ Statut", "value": "Validé par Samet", "inline": True},
    ], color=0x2ECC71)

    report_to_manager(f"Ordre exécuté : {action} {symbol} {amount}€", {
        "symbol": symbol, "action": action, "amount": amount
    })

    return jsonify({"status": "executed"})

# ─── PLANIFICATION ────────────────────────────────────────
def setup_schedule():
    schedule.every().day.at("09:30").do(scan_all_assets)
    schedule.every().day.at("14:00").do(scan_all_assets)
    schedule.every().day.at("09:00").do(daily_report)
    schedule.every(2).hours.do(check_dips)
    schedule.every().day.at("10:00").do(run_dca)
    print("⏰ Schedule : scan 09:30/14:00 | dips /2h | DCA 1er du mois")

# ─── MAIN ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print(f"📈 SENTINEL — TRADING AGENT v{VERSION}")
    print(f"🕐 Démarré le {now_str()}")
    print(f"🧠 LLM : Groq {GROQ_MODEL_FAST}")
    print(f"📡 IB  : {'✅ Disponible' if IB_AVAILABLE else '❌ Non installé'}")
    print("=" * 55)

    ib_status = "✅ Connecté" if connect_ib() else "❌ Offline (démarre TWS)"
    cash      = get_ib_cash()

    send_discord("🚀 SENTINEL Trading Agent — Opérationnel", [
        {"name": "✅ Status",      "value": "Online",                            "inline": True},
        {"name": "🧠 LLM",        "value": f"Groq {GROQ_MODEL_FAST}",           "inline": True},
        {"name": "📡 IB Connect", "value": ib_status,                           "inline": True},
        {"name": "💰 Cash dispo", "value": f"{cash:.2f}€",                      "inline": True},
        {"name": "📋 Rôle",
         "value": "• Scans H4 EMA50/200 + RSI\n"
                  "• Détecte dips > 5%\n"
                  "• DCA mensuel 50€\n"
                  "• JAMAIS d'ordre sans Samet ✅/❌",
         "inline": False},
    ], color=0x2ECC71)

    setup_schedule()

    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5003, debug=False),
        daemon=True
    )
    flask_thread.start()
    print("🌐 API Trading Agent démarrée sur port 5003")

    # Premier scan immédiat
    scan_all_assets()

    while True:
        schedule.run_pending()
        time.sleep(60)
