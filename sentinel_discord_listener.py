"""
🎮 SENTINEL — Discord Bot Listener
Écoute les boutons ✅/❌ et exécute les décisions approuvées.
Tourne en parallèle du Manager Agent.
"""

import os, json, requests, threading
import discord
from discord.ext import commands
from pathlib import Path
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────
BOT_TOKEN    = os.getenv("BT", "")
MANAGER_URL  = os.getenv("MANAGER_URL", "http://localhost:5001")
TRADING_URL  = os.getenv("TRADING_URL", "http://localhost:5003")
AGENT_SECRET = os.getenv("SS", "sentinel-secret-key")
STATE_FILE   = Path("manager_state.json")

# ─── INIT ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"pending": [], "approved": [], "rejected": []}

def save_state(s: dict):
    s["last_updated"] = now_str()
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False))

# ─── ÉCOUTE DES BOUTONS ───────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Discord Bot connecté : {bot.user}")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Gère les clics sur les boutons ✅/❌"""
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id", "")

    # ─── APPROBATION ──────────────────────────────────────
    if custom_id.startswith("approve_"):
        decision_id = custom_id.replace("approve_", "")
        await interaction.response.defer()

        s = load_state()
        decision = next((d for d in s["pending"] if d["id"] == decision_id), None)

        if not decision:
            await interaction.followup.send("❌ Décision introuvable ou déjà traitée.")
            return

        # Marque comme approuvée
        decision["status"] = "approved"
        decision["approved_by"] = str(interaction.user)
        decision["approved_at"] = now_str()
        s["approved"].append(decision)
        s["pending"] = [d for d in s["pending"] if d["id"] != decision_id]
        save_state(s)

        # Exécute selon le type
        action_type = decision.get("type", "")
        action_data = decision.get("data", {})

        if action_type.startswith("trade_"):
            # Envoie au Trading Agent pour exécution
            try:
                r = requests.post(
                    f"{TRADING_URL}/execute",
                    json=action_data,
                    headers={"X-Secret": AGENT_SECRET},
                    timeout=10
                )
                if r.status_code == 200:
                    await interaction.followup.send(
                        f"✅ **Ordre exécuté !**\n"
                        f"**{action_data.get('action', '').upper()} {action_data.get('symbol', '')}**\n"
                        f"💰 Montant : {action_data.get('amount', 0)}€\n"
                        f"👤 Approuvé par : {interaction.user}"
                    )
                else:
                    await interaction.followup.send(f"⚠️ Trading Agent a répondu : {r.status_code}")
            except Exception as e:
                await interaction.followup.send(f"❌ Trading Agent injoignable : {e}")

        elif action_type == "integrate_skill":
            await interaction.followup.send(
                f"✅ **Skill approuvé !**\n"
                f"📦 **{action_data.get('title', '')}**\n"
                f"🧪 Passage en paper trading 14 jours\n"
                f"👤 Approuvé par : {interaction.user}"
            )

        elif action_type == "rebalance":
            await interaction.followup.send(
                f"✅ **Rebalancement approuvé !**\n"
                f"⚖️ Sera effectué au prochain DCA\n"
                f"👤 Approuvé par : {interaction.user}"
            )

        else:
            await interaction.followup.send(
                f"✅ **Décision approuvée** : {decision.get('title', '')}\n"
                f"👤 Par : {interaction.user}"
            )

    # ─── REFUS ────────────────────────────────────────────
    elif custom_id.startswith("reject_"):
        decision_id = custom_id.replace("reject_", "")
        await interaction.response.defer()

        s = load_state()
        decision = next((d for d in s["pending"] if d["id"] == decision_id), None)

        if not decision:
            await interaction.followup.send("❌ Décision introuvable ou déjà traitée.")
            return

        decision["status"] = "rejected"
        decision["rejected_by"] = str(interaction.user)
        decision["rejected_at"] = now_str()
        s["rejected"].append(decision)
        s["pending"] = [d for d in s["pending"] if d["id"] != decision_id]
        save_state(s)

        await interaction.followup.send(
            f"❌ **Décision refusée** : {decision.get('title', '')}\n"
            f"👤 Par : {interaction.user}\n"
            f"📁 Archivée"
        )

# ─── COMMANDES SLASH ──────────────────────────────────────
@bot.command(name="status")
async def cmd_status(ctx):
    """Statut des 3 agents"""
    agents = {}
    for name, url in [("Manager", MANAGER_URL),
                      ("Skills Hunter", os.getenv("SKILLS_URL", "")),
                      ("Trading", TRADING_URL)]:
        if not url:
            agents[name] = "⚠️ URL manquante"
            continue
        try:
            r = requests.get(f"{url}/health",
                           headers={"X-Secret": AGENT_SECRET}, timeout=5)
            agents[name] = "✅ Online" if r.status_code == 200 else "⚠️ Erreur"
        except:
            agents[name] = "❌ Offline"

    s = load_state()
    msg = "**🛡️ SENTINEL — Statut**\n\n"
    for name, status in agents.items():
        msg += f"{status} **{name}**\n"
    msg += f"\n⏳ Décisions en attente : **{len(s['pending'])}**"
    await ctx.send(msg)

@bot.command(name="pause")
async def cmd_pause(ctx):
    """Met le bot en pause"""
    await ctx.send("⏸️ **SENTINEL mis en pause** — Aucun ordre ne sera exécuté.")

@bot.command(name="pending")
async def cmd_pending(ctx):
    """Liste les décisions en attente"""
    s = load_state()
    if not s["pending"]:
        await ctx.send("✅ Aucune décision en attente.")
        return
    msg = f"**⏳ {len(s['pending'])} décision(s) en attente :**\n\n"
    for d in s["pending"][:5]:
        msg += f"• **{d['title']}** — `{d['id']}`\n"
    await ctx.send(msg)

# ─── MAIN ─────────────────────────────────────────────────
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BT (Discord token) manquant !")
        exit(1)
    print(f"🎮 SENTINEL Discord Listener démarré — {now_str()}")
    bot.run(BOT_TOKEN)
