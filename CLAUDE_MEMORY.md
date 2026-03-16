# 🧠 CLAUDE MEMORY — SENTINEL Project
> Généré automatiquement | Dernière mise à jour : 15/03/2026 — session en cours

---

## 📌 Identité du projet
- **Nom** : SENTINEL
- **Propriétaire** : Samet (GitHub : sameulas43)
- **Objectif** : Système d'investissement éthique automatisé + 3 agents IA
- **Broker** : Interactive Brokers (Cash Account EUR, fractional shares)
- **Compte Forex** : PUPrime islamique (swap-free) — mis de côté pour l'instant

---

## 🤖 Les 3 Agents

| Agent | Fichier | Port | Statut | LLM actuel | LLM futur |
|-------|---------|------|--------|------------|-----------|
| Manager | sentinel_manager.py | 5001 | ✅ Railway | Groq gratuit | Claude Haiku ~2€/mois |
| Skills Hunter | sentinel_skills.py | 5002 | ✅ Railway | Groq gratuit | Groq gratuit |
| Trading Agent | sentinel_trading.py | 5003 | 🆕 À déployer | Groq gratuit | Groq gratuit |

> ⚠️ Le code actuel utilise Groq pour les 3 agents.
> Claude Haiku pour le Manager est prévu dans token-management.md (vendredi)

---

## 📋 Tâches détaillées par agent

### 🧠 Agent Manager
1. Coordonne Skills Hunter + Trading Agent
2. Décision finale avant exécution
3. Tableau de bord journalier Discord
4. Priorités du jour — urgent / rien à faire
5. Mémorise les décisions et apprend les préférences Samet
6. Rapports matin 09h00 / soir 20h00
7. Planning hebdo Samet chaque lundi 08:30
8. Analyse marché intelligente via Groq

### 🔍 Skills Hunter
1. Cherche GitHub + Reddit + StackOverflow chaque lundi
2. Scan sécurité ligne par ligne /100 — bloque < 80
3. Analyse pertinence via Groq
4. Email Gmail hebdomadaire avec rapport HTML + pièce jointe .md
5. Signale les meilleurs skills au Manager pour validation Samet
6. Blacklist automatique des sources dangereuses
7. Vérifie la conformité éthique de chaque ressource

### 📈 Trading Agent
1. Connexion IBBot via ib_insync (local terminal)
2. Scan H4 EMA 50/200 + RSI — 09:30 et 14:00
3. Détection dips > 5% toutes les 2h
4. DCA mensuel 50€ le 1er du mois
5. Analyse Groq de chaque signal
6. Journal de trades JSON
7. Rapport quotidien Discord 09:00
8. JAMAIS d'ordre sans validation Samet ✅/❌

---

## 📁 Fichiers SENTINEL (tous prêts)

```
sentinel_config.py    → Config partagée (portefeuille, risque, LLM)
sentinel_manager.py   → Cerveau central + Groq + planning hebdo Samet
sentinel_skills.py    → Skills Hunter + Groq + email Gmail + sécurité
sentinel_trading.py   → Trading Agent + IBBot + signaux H4 + DCA
requirements.txt      → Dépendances Python
README.md             → Guide déploiement Railway
CLAUDE_MEMORY.md      → Ce fichier (mémoire du projet)
```

---

## 🔄 Améliorations vs anciens agents

### Agent Manager (avant → après)
| Avant | Après |
|-------|-------|
| Python pur, règles fixes | ✅ Groq LLM — analyse intelligente |
| Aucune communication inter-agents | ✅ API Flask — parle aux 2 autres agents |
| Rapport basique | ✅ Analyse marché IA + conseil quotidien |
| Pas de planning | ✅ Planning hebdo Samet chaque lundi 08:30 |
| Nom "halal-manager" | ✅ SENTINEL Manager |

### Skills Hunter (avant → après)
| Avant | Après |
|-------|-------|
| Scraping basique sans jugement | ✅ Groq analyse pertinence de chaque ressource |
| Scan sécurité < 50 bloque | ✅ Scan < 80 bloque (plus strict) + Groq double check |
| Fichiers .md locaux seulement | ✅ Email Gmail automatique chaque lundi |
| Rapport Discord simple | ✅ Email HTML pro + pièce jointe .md |
| Aucune communication Manager | ✅ Signale chaque skill validé au Manager |

### Trading Agent (nouveau — from scratch)
```
✅ Connexion IBBot via ib_insync
✅ Signaux H4 — EMA 50/200 + RSI
✅ Détection dips > 5%
✅ DCA mensuel 50€ automatique
✅ Analyse Groq de chaque signal
✅ JAMAIS d'ordre sans Samet ✅/❌
✅ Journal de trades JSON
✅ Rapport quotidien Discord
```

---

## 🏗️ Architecture de communication

```
Samet (Discord)
      ↕️ ✅/❌
  Manager Agent (5001)
      ↕️              ↕️
Skills Hunter (5002) ↔️ Trading Agent (5003)
      ↕️                      ↕️
   GitHub/Reddit           IBBot (local)
```

---

## ⚙️ Variables Railway à configurer

```
GROQ_API_KEY         → groq.com (gratuit)
DISCORD_WEBHOOK_URL  → ton webhook Discord
DISCORD_TOKEN        → token bot Discord
DISCORD_CHANNEL_ID   → ID du channel
AGENT_SECRET         → sentinel-secret-key (même partout)
GMAIL_ADDRESS        → ton@gmail.com
GMAIL_APP_PASSWORD   → App Password Gmail (16 caractères)
MANAGER_URL          → https://sentinel-manager.railway.app
SKILLS_URL           → https://sentinel-skills.railway.app
TRADING_URL          → https://sentinel-trading.railway.app
IB_HOST              → IP locale IBBot
IB_PORT              → 7496 (live) / 7497 (paper)
```

---

## 📄 20 Documents à créer

### 📂 Agents
- [ ] agent-manager.md
- [ ] agent-trading.md
- [ ] agent-ecosystem.md
- [ ] agent-communication.md

### 📂 Écosystème
- [ ] skill-hunter.md
- [ ] security-engine.md
- [ ] paper-trading.md
- [ ] self-learning.md
- [ ] halal-screener-auto.md
- [ ] risk-engine.md
- [ ] sadaqa-engine.md
- [ ] ibbot-integration.md

### 📂 Monitoring
- [ ] performance-tracking.md
- [ ] backtesting.md
- [ ] benchmark.md
- [ ] memory-journal.md

### 📂 Discord & Interface
- [ ] discord-commands.md
- [ ] alerts-unified.md

### 📂 Global
- [ ] roadmap.md
- [ ] token-management.md

---

## 💰 Budget LLM mensuel
| Agent | LLM actuel | LLM futur | Coût |
|-------|-----------|-----------|------|
| Manager | Groq gratuit | Claude Haiku | ~2€/mois |
| Skills Hunter | Groq Llama3 | Groq Llama3 | 0€ |
| Trading Agent | Groq Llama3 | Groq Llama3 | 0€ |
| Security Engine | Python pur | Python pur | 0€ |
| **Total actuel** | | | **0€** |
| **Total futur** | | | **~2€/mois** |

---

## 🎯 Portefeuille cible
| Actif | Allocation | Type |
|-------|-----------|------|
| SGOL | 15% | Or physique |
| PHAG | 10% | Argent physique |
| ICLN | 15% | Clean Energy ETF |
| ENPH | 10% | Solaire |
| MOO | 10% | Agro ETF |
| DBA | 10% | Agriculture |
| SPUS | 15% | Shariah ETF |
| HLAL | 10% | Shariah ETF |
| PHO | 5% | Water ETF |

**DCA : 50€/mois | Capital départ : 100€ | Max par ordre : 5%**

---

## 📅 Planning hebdomadaire automatique
| Jour | Heure | Action |
|------|-------|--------|
| Lundi | 08:00 | Rapport hebdo + Skills Hunter search |
| Lundi | 08:30 | Planning Samet envoyé sur Discord |
| Tous les jours | 09:00 | Rapport matinal + analyse IA |
| Tous les jours | 09:30 | Scan signaux Trading Agent |
| Toutes les heures | — | Vérif dips + surveillance agents |
| Tous les jours | 20:00 | Rapport du soir |
| 1er du mois | 08:00 | Rapport mensuel + DCA |

---

## 🔐 Règles de sécurité absolues
1. ❌ Aucun ordre sans validation Samet ✅/❌
2. ❌ Aucun actif non listé dans VALIDATED_ASSETS
3. ❌ Aucun skill avec score sécurité < 80/100
4. ❌ Jamais de levier, jamais de margin
5. ✅ Paper trading 14 jours avant toute intégration live
6. ✅ Max 5% du capital par ordre
7. ✅ IBBot tourne en LOCAL via terminal — pas sur Railway

---

## 🤖 Bots MT5 existants (mis de côté)

| Bot | Actifs | Source prix | Discord | Statut |
|-----|--------|-------------|---------|--------|
| EMA FLOW | XAU/USD | Kraken | #général | ✅ Railway — en attente signaux |
| IRR RIBBON | XAU/USD + EUR/USD + US500 | Kraken + yfinance | #irr-ribbon | ✅ Railway — en attente signaux |

> ⚠️ Ces bots tournent sur Railway mais on attend de voir les signaux.
> Compte PUPrime islamique (swap-free) utilisé pour MT5.
> À NE PAS toucher pour l'instant — focus sur SENTINEL.

---

## 🧠 Philosophie du projet
- **Observer avant modifier** — Samet préfère voir tourner avant de changer
- **Construire étape par étape** — un composant validé avant le suivant
- **Pas de précipitation** — la régularité prime sur la vitesse
- **Agents proposent, Samet décide** — aucun argent ne bouge sans ✅

---

## ❌ Ce qui est discuté mais pas encore codé
- Paper trading sandbox (14 jours avant live)
- Self-learning — boucle d'auto-amélioration
- Sadaqa engine — calcul purification gains (% gains → charité)
- Backtesting — tests historiques des stratégies
- Memory journal — mémoire long terme des agents
- Halal screener automatique
- Risk engine centralisé
- Les 20 documents — pas encore rédigés

---

## 🚀 Prochaines étapes (dans l'ordre)
1. Créer compte Groq → groq.com
2. Upload fichiers sur GitHub sameulas43
3. Déployer sentinel_skills sur Railway
4. Déployer sentinel_trading sur Railway  
5. Mettre à jour sentinel_manager sur Railway
6. Configurer toutes les variables Railway
7. Tester communication inter-agents
8. Commencer les 20 documents avec Claude

---
*🧠 Ce fichier est la mémoire vivante du projet SENTINEL*
*À uploader dans le projet Claude après chaque session importante*
