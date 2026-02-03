"use client";

import React, { useState } from "react";
import { useBotContext, BotConfig } from "../context/BotContext";
import { Plus, Trash2, Settings, Power, Bot } from "lucide-react";
// import { BotConfig } from "../services/api";

// Définir l’état initial du bot
const initialBotState: Omit<BotConfig, "id"> = {
  name: "",
  token_pair: "",
  volatility_percent: 0,
  random_trades_count: 0,
  trading_duration_hours: 0,
  balance: 0,
  total_profit: 0,
  isActive: false,
  status: "paused",

  // Wallet & blockchain
  swap_amount: 0.1,
  wallet_address: "",
  wallet_private_key: "",
  rpc_endpoint: "https://polygon-rpc.com",

  // Contracts
  wpol_address: "",
  kno_address: "",
  router_address: "",
  quoter_address: "",

  // Trading config
  slippage_tolerance: 1,
  gas_limit: 300000,
  gas_price: 30,
  buy_amount: 0.01,
  sell_amount: 0.01,
  min_swap_amount: 0,
  reference_price: null,
  last_buy_price: null,
  last_sell_price: null,
  // buy_percentage_drop: null,
  // sell_percentage_gain: null,
  // buy_price_threshold: null,
  // sell_price_threshold: null,
  // created_at: null,
  // updated_at: null,
  // last_heartbeat: null,
};

function BotManager() {
  const { bots, addBot, deleteBot, toggleBot, selectBot } = useBotContext();
  const [showAddForm, setShowAddForm] = useState(false);
  const [newBot, setNewBot] = useState<Omit<BotConfig, "id">>(initialBotState);

  const getTokenBase = (token_pair: string) => {
    if (!token_pair) return "token";
    return token_pair.split("/")[0] || "token";
  };

  // const handleAddBot = async () => {
  //   if (newBot.name && newBot.token_pair) {
  //     try {
  //       await addBot(newBot);
  //       setNewBot(initialBotState);
  //       setShowAddForm(false);
  //       alert("Bot créé avec succès! 🚀");
  //     } catch (error: any) {
  //       console.error("Erreur création bot:", error);
  //       alert("Erreur lors de la création: " + error.message);
  //     }
  //   } else {
  //     alert("Veuillez renseigner le nom et la paire de trading.");
  //   }
  // };

  const handleAddBot = async () => {
    if (!newBot.name || !newBot.token_pair) {
      alert("Veuillez renseigner le nom et la paire de trading.");
      return;
    }

    try {
      // 🔹 Récupérer le prix actuel du marché
      const { getKnoPrice } = useBotContext(); // ou ta fonction de récupération
      const marketPrice = await getKnoPrice(); // peut retourner null si erreur

      // 🔹 Calculer les montants selon le marché
      const buyAmount = Math.max(0.01, (marketPrice ?? 1) * 0.05); // 5% du prix ou minimum 0.01
      const sellAmount = Math.max(0.01, (marketPrice ?? 1) * 0.05);

      const botToCreate = {
        ...newBot,
        buy_amount: buyAmount,
        sell_amount: sellAmount,
      };

      await addBot(botToCreate);
      setNewBot(initialBotState);
      setShowAddForm(false);
      alert("Bot créé avec succès! 🚀");
    } catch (error: any) {
      console.error("Erreur création bot:", error);
      alert("Erreur lors de la création: " + error.message);
    }
  };

  const statusColors = {
    active: "bg-green-100 text-green-800",
    paused: "bg-yellow-100 text-yellow-800",
    error: "bg-red-100 text-red-800",
  } as const;

  const statusLabels = {
    active: "Actif",
    paused: "En pause",
    error: "Erreur",
  } as const;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Bot className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Gestion des Bots
            </h1>
            <p className="text-gray-600">Créer et gérer vos bots de trading</p>
          </div>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors font-medium"
        >
          <Plus className="w-4 h-4" />
          <span>Nouveau Bot</span>
        </button>
      </div>

      {/* Add Bot Form */}
      {showAddForm && (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Créer un nouveau bot
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* Nom */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nom du bot
              </label>
              <input
                type="text"
                value={newBot.name}
                onChange={(e) =>
                  setNewBot((prev) => ({ ...prev, name: e.target.value }))
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Bot ETH/USDC"
              />
            </div>

            {/* Paire de trading */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Paire de trading
              </label>
              <input
                type="text"
                value={newBot.token_pair}
                onChange={(e) =>
                  setNewBot((prev) => ({ ...prev, token_pair: e.target.value }))
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="KNO/WMATIC"
              />
            </div>

            {/* Volatility */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Volatility (%)
              </label>
              <input
                type="number"
                min={1}
                max={100}
                value={newBot.volatility_percent}
                onChange={(e) =>
                  setNewBot((prev) => ({
                    ...prev,
                    volatility_percent: parseFloat(e.target.value),
                  }))
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Trade si le prix varie de ce pourcentage par rapport à la
                référence
              </p>
            </div>

            {/* Random trades */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trades aléatoires
              </label>
              <input
                type="number"
                min={1}
                max={100}
                value={newBot.random_trades_count}
                onChange={(e) =>
                  setNewBot((prev) => ({
                    ...prev,
                    random_trades_count: parseInt(e.target.value),
                  }))
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Trading duration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Durée trading (heures)
              </label>
              <input
                type="number"
                min={1}
                max={168}
                value={newBot.trading_duration_hours}
                onChange={(e) =>
                  setNewBot((prev) => ({
                    ...prev,
                    trading_duration_hours: parseInt(e.target.value),
                  }))
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleAddBot}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors font-medium"
            >
              Créer le bot
            </button>
            <button
              onClick={() => setShowAddForm(false)}
              className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-6 py-2 rounded-lg transition-colors font-medium"
            >
              Annuler
            </button>
          </div>
        </div>
      )}

      {/* Bots List */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Tous les bots ({bots.length})
          </h2>
        </div>
        <div className="space-y-4">
          {bots.map((bot) => (
            <div
              key={bot.id}
              className="flex justify-between items-center p-4 border rounded hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <Bot className="w-6 h-6 text-blue-600" />
                <div>
                  <h3 className="font-semibold">{bot.name}</h3>
                  <p className="text-sm text-gray-500">{bot.token_pair}</p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span
                  className={`px-2 py-1 rounded-full text-sm font-medium ${
                    statusColors[bot.status]
                  }`}
                >
                  {statusLabels[bot.status]}
                </span>
                <button onClick={() => selectBot(bot.id)} title="Configurer">
                  <Settings className="w-5 h-5 text-gray-500 hover:text-blue-600" />
                </button>
                <button
                  onClick={() => toggleBot(bot.id)}
                  title={bot.isActive ? "Arrêter" : "Démarrer"}
                  className={`p-2 transition-colors ${
                    bot.isActive
                      ? "text-red-500 hover:text-red-700"
                      : "text-green-500 hover:text-green-700"
                  }`}
                >
                  <Power className="w-5 h-5" />
                </button>
                <button onClick={() => deleteBot(bot.id)} title="Supprimer">
                  <Trash2 className="w-5 h-5 text-gray-500 hover:text-red-600" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default BotManager;
