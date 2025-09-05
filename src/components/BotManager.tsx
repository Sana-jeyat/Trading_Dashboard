import React, { useState } from 'react';
import { useBotContext } from '../context/BotContext';
import { Plus, Trash2, Settings, Power, Bot } from 'lucide-react';

function BotManager() {
  const { bots, addBot, deleteBot, toggleBot, selectBot } = useBotContext();
  const [showAddForm, setShowAddForm] = useState(false);
  const [newBot, setNewBot] = useState({
    name: '',
    tokenPair: '',
    buyPriceThreshold: 0,
    buyPercentageDrop: 10,
    sellPriceThreshold: 0,
    sellPercentageGain: 10,
    randomTradesCount: 20,
    tradingDurationHours: 24,
    balance: 0,
    totalProfit: 0,
    isActive: false,
    status: 'paused' as const
  });

  const handleAddBot = () => {
    if (newBot.name && newBot.tokenPair) {
      addBot(newBot);
      setNewBot({
        name: '',
        tokenPair: '',
        buyPriceThreshold: 0,
        buyPercentageDrop: 10,
        sellPriceThreshold: 0,
        sellPercentageGain: 10,
        randomTradesCount: 20,
        tradingDurationHours: 24,
        balance: 0,
        totalProfit: 0,
        isActive: false,
        status: 'paused'
      });
      setShowAddForm(false);
    }
  };

  const statusColors = {
    active: 'bg-green-100 text-green-800',
    paused: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800'
  };

  const statusLabels = {
    active: 'Actif',
    paused: 'En pause',
    error: 'Erreur'
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Bot className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Gestion des Bots</h1>
            <p className="text-gray-600">Créer, configurer et gérer vos bots de trading</p>
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
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Créer un nouveau bot</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Nom du bot</label>
              <input
                type="text"
                value={newBot.name}
                onChange={(e) => setNewBot(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Bot ETH/USDC"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Paire de trading</label>
              <input
                type="text"
                value={newBot.tokenPair}
                onChange={(e) => setNewBot(prev => ({ ...prev, tokenPair: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="ETH/USDC"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Prix d'achat max (€)</label>
              <input
                type="number"
                value={newBot.buyPriceThreshold}
                onChange={(e) => setNewBot(prev => ({ ...prev, buyPriceThreshold: parseFloat(e.target.value) }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="2800"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Prix de vente min (€)</label>
              <input
                type="number"
                value={newBot.sellPriceThreshold}
                onChange={(e) => setNewBot(prev => ({ ...prev, sellPriceThreshold: parseFloat(e.target.value) }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="3200"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Baisse pour re-achat (%)</label>
              <input
                type="number"
                value={newBot.buyPercentageDrop}
                onChange={(e) => setNewBot(prev => ({ ...prev, buyPercentageDrop: parseFloat(e.target.value) }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="10"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Hausse pour vente (%)</label>
              <input
                type="number"
                value={newBot.sellPercentageGain}
                onChange={(e) => setNewBot(prev => ({ ...prev, sellPercentageGain: parseFloat(e.target.value) }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="10"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Trades aléatoires</label>
              <input
                type="number"
                min="1"
                max="100"
                value={newBot.randomTradesCount}
                onChange={(e) => setNewBot(prev => ({ ...prev, randomTradesCount: parseInt(e.target.value) }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="20"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Durée trading (heures)</label>
              <input
                type="number"
                min="1"
                max="168"
                value={newBot.tradingDurationHours}
                onChange={(e) => setNewBot(prev => ({ ...prev, tradingDurationHours: parseInt(e.target.value) }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="24"
              />
            </div>
          </div>
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
          <h2 className="text-xl font-semibold text-gray-900">Tous les bots ({bots.length})</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {bots.map((bot) => (
            <div key={bot.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <Bot className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{bot.name}</h3>
                    <p className="text-gray-600">{bot.tokenPair}</p>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className="text-sm text-gray-500">
                        Solde: {"€" + bot.balance.toLocaleString()}
                      </span>
                      <span className="text-sm text-green-600">
                        Profit: {"€" + bot.totalProfit.toLocaleString()}
                      </span>
                      <span className="text-sm text-purple-600">
                        {bot.randomTradesCount} trades/{bot.tradingDurationHours}h
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[bot.status]}`}>
                    {statusLabels[bot.status]}
                  </div>
                  <button
                    onClick={() => selectBot(bot.id)}
                    className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Configurer"
                  >
                    <Settings className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => toggleBot(bot.id)}
                    className={`p-2 transition-colors ${
                      bot.isActive 
                        ? 'text-red-500 hover:text-red-700' 
                        : 'text-green-500 hover:text-green-700'
                    }`}
                    title={bot.isActive ? 'Arrêter' : 'Démarrer'}
                  >
                    <Power className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => deleteBot(bot.id)}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                    title="Supprimer"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default BotManager;