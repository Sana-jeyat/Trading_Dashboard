// components/BotCard.tsx

import { Play, Pause, Trash2, Bot as BotIcon } from "lucide-react";
import { useBotContext } from "../context/BotContext";

interface BotCardProps {
  bot: {
    id: string;
    name: string;
    token_pair: string;
    balance: number;
    total_profit: number;
    volatility_percent: number; // Volatilité
  };
}

function BotCard({ bot }: BotCardProps) {
  const { activeBots, toggleBot, deleteBot } = useBotContext();

  const isActive = activeBots.includes(bot.id);

  return (
    <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
      {/* En-tête du bot */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <BotIcon className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{bot.name}</h3>
            <p className="text-gray-600">{bot.token_pair}</p>
          </div>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => toggleBot(bot.id)}
            className={`p-2 rounded-lg ${
              isActive
                ? "bg-yellow-500 hover:bg-yellow-600"
                : "bg-green-500 hover:bg-green-600"
            } text-white`}
          >
            {isActive ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </button>

          <button
            onClick={() => deleteBot(bot.id)}
            className="p-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Statut */}
      <div className="flex items-center space-x-2 mb-4">
        <div
          className={`w-2 h-2 rounded-full ${
            isActive ? "bg-green-400" : "bg-gray-400"
          } animate-pulse`}
        ></div>
        <span className="text-sm font-medium text-gray-700">
          {isActive ? "En ligne" : "Hors ligne"}
        </span>
      </div>

      {/* Statistiques du bot */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">Solde</p>
          <p className="font-semibold text-gray-900">
            €{bot.balance.toLocaleString()}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">Profit</p>
          <p className="font-semibold text-green-600">
            €{bot.total_profit.toLocaleString()}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">Volatilité</p>
          <p className="font-semibold text-purple-600">
            {bot.volatility_percent}%
          </p>
        </div>
      </div>
    </div>
  );
}

export default BotCard;
