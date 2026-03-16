# 🛡️ SENTINEL — Guide de déploiement Railway

## Structure des services

Chaque agent = un service Railway séparé :

```
sentinel-manager   → sentinel_manager.py  (port 5001)
sentinel-skills    → sentinel_skills.py   (port 5002)  
sentinel-trading   → sentinel_trading.py  (port 5003)
```

---

## Variables d'environnement Railway

### Variables communes (tous les agents)
```
DISCORD_WEBHOOK_URL = https://discord.com/api/webhooks/...
DISCORD_TOKEN       = ton_token_discord
DISCORD_CHANNEL_ID  = ton_channel_id
GROQ_API_KEY        = gsk_...  ← depuis console.groq.com
AGENT_SECRET        = sentinel-secret-key  ← même valeur partout !
```

### Variables Manager
```
SKILLS_URL  = https://sentinel-skills.railway.app
TRADING_URL = https://sentinel-trading.railway.app
```

### Variables Skills Hunter
```
MANAGER_URL  = https://sentinel-manager.railway.app
GITHUB_TOKEN = ton_github_token (optionnel mais recommandé)
```

### Variables Trading Agent
```
MANAGER_URL  = https://sentinel-manager.railway.app
IB_HOST      = ton_ip_locale  ← si IB Local
IB_PORT      = 7496           ← live | 7497 = paper
IB_CLIENT_ID = 1
```

---

## Commandes de démarrage Railway

| Service | Start Command |
|---------|--------------|
| Manager | `python sentinel_manager.py` |
| Skills  | `python sentinel_skills.py` |
| Trading | `python sentinel_trading.py` |

---

## Flux de communication

```
Skills Hunter
    → trouve skill
    → POST /skill_found → Manager
    → Manager → Discord boutons ✅/❌ → Samet

Trading Agent  
    → détecte signal
    → POST /trade_signal → Manager
    → Manager → Discord boutons ✅/❌ → Samet

Manager
    → coordonne les 2 agents
    → POST /task → Skills ou Trading
    → rapports matin/soir/hebdo → Discord
```

---

## Obtenir la clé Groq (gratuit)

1. Va sur **console.groq.com**
2. Créer un compte
3. API Keys → Create API Key
4. Copie la clé `gsk_...`
5. Ajoute dans Railway : `GROQ_API_KEY = gsk_...`

---

## Ordre de déploiement recommandé

1. Skills Hunter en premier (autonome)
2. Trading Agent (connexion IB locale)
3. Manager en dernier (se connecte aux 2 autres)
