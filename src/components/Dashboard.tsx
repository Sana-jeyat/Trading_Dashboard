import React from 'react';
import { useBotContext } from '../context/BotContext';
import { Activity, TrendingUp, TrendingDown, DollarSign, Bot } from 'lucide-react';

function Dashboard() {
  const { bots, selectedBot, transactions } = useBotContext();

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

  const activeBots = bots.filter(bot => bot.isActive).length;
  const totalBalance = bots.reduce((acc, bot) => acc + bot.balance, 0);
  const totalProfit = bots.reduce((acc, bot) => acc + bot.totalProfit, 0);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="text-sm text-gray-600">{activeBots}/{bots.length} bots actifs</p>
          </div>
          <div className={`px-4 py-2 rounded-full text-sm font-medium ${statusColors[selectedBot.status]}`}>
            {statusLabels[selectedBot.status]}
          </div>
        </div>
      </div>

      {/* Global Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Solde Total (Tous bots)</p>
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
              <p className="text-sm text-gray-600">Profit Total (Tous bots)</p>
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
              <p className="text-2xl font-bold text-blue-600">{activeBots}/{bots.length}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <Bot className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

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
                selectedBot.buyPriceThreshold.toLocaleString() : 
                selectedBot.buyPriceThreshold.toFixed(4))}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Baisse pour re-achat</p>
            <p className="text-lg font-semibold text-gray-900">{selectedBot.buyPercentageDrop}%</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Prix de vente min</p>
            <p className="text-lg font-semibold text-gray-900">
              {"€" + (selectedBot.tokenPair.includes('BTC') || selectedBot.tokenPair.includes('ETH') ? 
                selectedBot.sellPriceThreshold.toLocaleString() : 
                selectedBot.sellPriceThreshold.toFixed(4))}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Hausse pour vente</p>
            <p className="text-lg font-semibold text-gray-900">{selectedBot.sellPercentageGain}%</p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-purple-600">Trades aléatoires</p>
            <p className="text-lg font-semibold text-purple-900">{selectedBot.randomTradesCount}</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-purple-600">Durée de trading</p>
            <p className="text-lg font-semibold text-purple-900">
              {selectedBot.tradingDurationHours}h
              {selectedBot.tradingDurationHours === 24 ? ' (1 jour)' : 
               selectedBot.tradingDurationHours < 24 ? '' : 
               ` (${Math.round(selectedBot.tradingDurationHours / 24 * 10) / 10} jours)`}
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
              <p className="text-2xl font-bold text-gray-900">€{selectedBot.balance.toLocaleString()}</p>
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
              <p className="text-2xl font-bold text-green-600">€{selectedBot.totalProfit.toLocaleString()}</p>
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
                        <TrendingDown className={`w-4 h-4 ${transaction.type === 'buy' ? 'text-blue-600' : 'text-green-600'}`} /> :
                        <TrendingUp className={`w-4 h-4 ${transaction.type === 'buy' ? 'text-blue-600' : 'text-green-600'}`} />
                      }
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 capitalize">
                        {transaction.type === 'buy' ? 'Achat' : 'Vente'} {transaction.amount.toLocaleString()} {selectedBot.tokenPair}
                      </p>
                      <p className="text-sm text-gray-600">{transaction.timestamp}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">
                      {"€" + (selectedBot.tokenPair.includes('BTC') || selectedBot.tokenPair.includes('ETH') ? 
                        transaction.price.toLocaleString() : 
                        transaction.price.toFixed(4))}
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