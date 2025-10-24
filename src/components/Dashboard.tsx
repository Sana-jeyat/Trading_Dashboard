import React, { useEffect } from 'react';
import { useBotContext } from '../context/BotContext';
import { Activity, TrendingUp, TrendingDown, DollarSign, Bot, Play, Pause, Plus } from 'lucide-react';

function Dashboard() {
  const { 
    bots, 
    activeBots, 
    selectedBot, 
    transactions, 
    refreshData, 
    loading, 
    startBot, 
    stopBot, 
    toggleBot,
    selectBot,
    addBot 
  } = useBotContext();

  // Rafraîchissement automatique toutes les 30 secondes
  useEffect(() => {
    const interval = setInterval(() => {
      refreshData();
    }, 30000);

    return () => clearInterval(interval);
  }, [refreshData]);

  // Si en chargement
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Chargement...</div>
      </div>
    );
  }

  // Si pas de bots
  if (!bots.length) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Aucun bot disponible</div>
      </div>
    );
  }

  const recentTransactions = transactions.slice(-3);
  const todaysPnL = transactions
    .filter(t => t.profit)
    .reduce((acc, t) => acc + (t.profit || 0), 0);

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

  const activeBotsCount = activeBots.length;
  const totalBalance = bots.reduce((acc, bot) => acc + bot.balance, 0);
  const totalProfit = bots.reduce((acc, bot) => acc + bot.totalProfit, 0);

  // Fonctions pour contrôler tous les bots
  const startAllBots = () => {
    bots.forEach(bot => {
      if (!bot.isActive) {
        startBot(bot.id);
      }
    });
  };

  const stopAllBots = () => {
    bots.forEach(bot => {
      if (bot.isActive) {
        stopBot(bot.id);
      }
    });
  };

  return (
    <div className="p-6 space-y-6">
      {/* En-tête avec contrôles globaux */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Trading</h1>
        <div className="flex items-center space-x-4">
          {/* Contrôles globaux */}
          <div className="flex space-x-2">
            <button
              onClick={startAllBots}
              className="flex items-center space-x-2 bg-green-500 text-white px-3 py-2 rounded-lg hover:bg-green-600 text-sm"
            >
              <Play className="w-4 h-4" />
              <span>Tout démarrer</span>
            </button>
            <button
              onClick={stopAllBots}
              className="flex items-center space-x-2 bg-red-500 text-white px-3 py-2 rounded-lg hover:bg-red-600 text-sm"
            >
              <Pause className="w-4 h-4" />
              <span>Tout arrêter</span>
            </button>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <p className="text-sm text-gray-600">{activeBotsCount}/{bots.length} bots actifs</p>
            </div>
            {selectedBot && (
              <div className={`px-4 py-2 rounded-full text-sm font-medium ${statusColors[selectedBot.status] || statusColors.paused}`}>
                {statusLabels[selectedBot.status] || statusLabels.paused}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Global Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Solde Total</p>
              <p className="text-2xl font-bold text-gray-900">€{totalBalance.toLocaleString()}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Profit Total</p>
              <p className="text-2xl font-bold text-green-600">€{totalProfit.toLocaleString()}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Bots Actifs</p>
              <p className="text-2xl font-bold text-blue-600">{activeBotsCount}/{bots.length}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <Bot className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">PnL Aujourd'hui</p>
              <p className={`text-2xl font-bold ${todaysPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {"€" + todaysPnL.toFixed(2)}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${todaysPnL >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
              {todaysPnL >= 0 ? 
                <TrendingUp className="w-6 h-6 text-green-600" /> :
                <TrendingDown className="w-6 h-6 text-red-600" />
              }
            </div>
          </div>
        </div>
      </div>

      {/* Liste des Bots */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bot className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">Mes Bots de Trading</h3>
            </div>
            <button className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              <Plus className="w-4 h-4" />
              <span>Nouveau Bot</span>
            </button>
          </div>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bots.map(bot => (
              <div 
                key={bot.id} 
                className={`border rounded-lg p-4 cursor-pointer transition-all ${
                  selectedBot?.id === bot.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => selectBot(bot.id)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-semibold text-gray-900">{bot.name}</h4>
                    <p className="text-sm text-gray-600">{bot.tokenPair}</p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleBot(bot.id);
                    }}
                    className={`p-2 rounded ${
                      bot.isActive 
                        ? 'bg-yellow-500 hover:bg-yellow-600' 
                        : 'bg-green-500 hover:bg-green-600'
                    } text-white`}
                  >
                    {bot.isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                </div>
                
                <div className="flex items-center space-x-2 mb-3">
                  <div className={`w-2 h-2 rounded-full ${bot.isActive ? 'bg-green-400' : 'bg-gray-400'} animate-pulse`}></div>
                  <span className="text-sm text-gray-600">
                    {bot.isActive ? 'En ligne' : 'Hors ligne'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-gray-500">Solde</p>
                    <p className="font-semibold">€{bot.balance.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Profit</p>
                    <p className="font-semibold text-green-600">€{bot.totalProfit.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Détails du Bot Sélectionné */}
      {selectedBot && (
        <>
          {/* Bot Overview Card */}
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Bot className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">{selectedBot.name}</h2>
                  <p className="text-gray-600">Trading automatique {selectedBot.tokenPair}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${selectedBot.isActive ? 'bg-green-400' : 'bg-gray-400'} animate-pulse`}></div>
                <span className="text-sm font-medium text-gray-700">
                  {selectedBot.isActive ? 'En ligne' : 'Hors ligne'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Prix d'achat max</p>
                <p className="text-lg font-semibold text-gray-900">
                  {"€" + (selectedBot.tokenPair.includes('BTC') || selectedBot.tokenPair.includes('ETH') ? 
                    selectedBot.buyPriceThreshold?.toLocaleString() || '0' : 
                    selectedBot.buyPriceThreshold?.toFixed(4) || '0.0000')}
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Baisse pour re-achat</p>
                <p className="text-lg font-semibold text-gray-900">{selectedBot.buyPercentageDrop || 0}%</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Prix de vente min</p>
                <p className="text-lg font-semibold text-gray-900">
                  {"€" + (selectedBot.tokenPair.includes('BTC') || selectedBot.tokenPair.includes('ETH') ? 
                    selectedBot.sellPriceThreshold?.toLocaleString() || '0' : 
                    selectedBot.sellPriceThreshold?.toFixed(4) || '0.0000')}
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Hausse pour vente</p>
                <p className="text-lg font-semibold text-gray-900">{selectedBot.sellPercentageGain || 0}%</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-purple-600">Trades aléatoires</p>
                <p className="text-lg font-semibold text-purple-900">{selectedBot.randomTradesCount || 0}</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-purple-600">Durée de trading</p>
                <p className="text-lg font-semibold text-purple-900">
                  {(selectedBot.tradingDurationHours || 0)}h
                  {selectedBot.tradingDurationHours === 24 ? ' (1 jour)' : 
                  selectedBot.tradingDurationHours < 24 ? '' : 
                  ` (${Math.round((selectedBot.tradingDurationHours || 0) / 24 * 10) / 10} jours)`}
                </p>
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Solde ({selectedBot.name})</p>
                  <p className="text-2xl font-bold text-gray-900">€{(selectedBot.balance || 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <DollarSign className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Profit ({selectedBot.name})</p>
                  <p className="text-2xl font-bold text-green-600">€{(selectedBot.totalProfit || 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">PnL Aujourd'hui</p>
                  <p className={`text-2xl font-bold ${todaysPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {"€" + todaysPnL.toFixed(2)}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${todaysPnL >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  {todaysPnL >= 0 ? 
                    <TrendingUp className="w-6 h-6 text-green-600" /> :
                    <TrendingDown className="w-6 h-6 text-red-600" />
                  }
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Activité Récente</h3>
          </div>
        </div>
        <div className="p-6">
          {recentTransactions.length > 0 ? (
            <div className="space-y-4">
              {recentTransactions.map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className={`p-2 rounded-lg ${
                      transaction.type === 'buy' ? 'bg-blue-50' : 'bg-green-50'
                    }`}>
                      {transaction.type === 'buy' ? 
                        <TrendingDown className="w-4 h-4 text-blue-600" /> :
                        <TrendingUp className="w-4 h-4 text-green-600" />
                      }
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 capitalize">
                        {transaction.type === 'buy' ? 'Achat' : 'Vente'} {(transaction.amount || 0).toLocaleString()} {selectedBot?.tokenPair}
                      </p>
                      <p className="text-sm text-gray-600">{transaction.timestamp}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">
                      {"€" + ((selectedBot?.tokenPair.includes('BTC') || selectedBot?.tokenPair.includes('ETH')) ? 
                        (transaction.price || 0).toLocaleString() : 
                        (transaction.price || 0).toFixed(4))}
                    </p>
                    {transaction.profit && (
                      <p className="text-sm text-green-600">{"+€" + transaction.profit.toFixed(2)}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">Aucune transaction récente</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;