import React, { useState } from 'react';
import { useBotContext } from '../context/BotContext';
import { History, Filter, TrendingUp, TrendingDown, Calendar } from 'lucide-react';

function TransactionHistory() {
  const { transactions, selectedBot } = useBotContext();
  const [filter, setFilter] = useState('all');

  const filteredTransactions = filter === 'all' 
    ? transactions 
    : transactions.filter(t => t.type === filter);

  const totalProfit = transactions
    .filter(t => t.profit)
    .reduce((acc, t) => acc + (t.profit || 0), 0);

  const totalBuys = transactions.filter(t => t.type === 'buy').length;
  const totalSells = transactions.filter(t => t.type === 'sell').length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <History className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Historique</h1>
            <p className="text-gray-600">Toutes les transactions du bot</p>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Achats</p>
              <p className="text-2xl font-bold text-blue-600">{totalBuys}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <TrendingDown className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Ventes</p>
              <p className="text-2xl font-bold text-green-600">{totalSells}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Profit Réalisé</p>
              <p className="text-2xl font-bold text-green-600">${totalProfit.toFixed(2)}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <Calendar className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Transaction List */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Transactions</h2>
            <div className="flex items-center space-x-3">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">Toutes</option>
                <option value="buy">Achats</option>
                <option value="sell">Ventes</option>
              </select>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantité (WPOL/KNO)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Prix (€)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Profit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date & Heure
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTransactions.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <div className={`p-2 rounded-lg ${
                        transaction.type === 'buy' ? 'bg-blue-50' : 'bg-green-50'
                      }`}>
                        {transaction.type === 'buy' ? 
                          <TrendingDown className="w-4 h-4 text-blue-600" /> :
                          <TrendingUp className="w-4 h-4 text-green-600" />
                        }
                      </div>
                      <span className={`font-medium capitalize ${
                        transaction.type === 'buy' ? 'text-blue-700' : 'text-green-700'
                      }`}>
                        {transaction.type === 'buy' ? 'Achat' : 'Vente'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900 font-medium">
                    {transaction.amount.toLocaleString()} {selectedBot.tokenPair}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900 font-medium">
                    {"€" + (selectedBot.tokenPair.includes('BTC') || selectedBot.tokenPair.includes('ETH') ? 
                      transaction.price.toLocaleString() : 
                      transaction.price.toFixed(4))}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {transaction.profit ? (
                      <span className="text-green-600 font-medium">
                        {"+€" + transaction.profit.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {transaction.timestamp}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredTransactions.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-gray-500">Aucune transaction trouvée pour ce filtre</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default TransactionHistory;