import React from "react";
import { BarChart3, Bot, History, Settings, Power, Plus } from "lucide-react";
import { useBotContext } from "../context/BotContext";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const { bots, selectedBot, selectedBotId, toggleBot, selectBot } =
    useBotContext();

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: BarChart3 },
    { id: "bots", label: "Gestion Bots", icon: Bot },
    { id: "config", label: "Configuration", icon: Settings },
    { id: "history", label: "Historique", icon: History },
  ];

  return (
    <div className="w-64 bg-white shadow-lg border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-2 mb-4">
          <Bot className="w-8 h-8 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900">TradingBot Pro</h1>
        </div>

        {/* Bot Selector */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Bot actuel
          </label>
          <select
            value={selectedBotId}
            onChange={(e) => selectBot(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          >
            {bots.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {bot.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => toggleBot(selectedBotId)}
          className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
            selectedBot.isActive
              ? "bg-red-500 hover:bg-red-600 text-white"
              : "bg-green-500 hover:bg-green-600 text-white"
          }`}
        >
          <Power className="w-4 h-4" />
          <span>{selectedBot.isActive ? "Arrêter" : "Démarrer"}</span>
        </button>
      </div>

      <nav className="flex-1 p-4">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 text-left rounded-lg transition-all duration-200 mb-2 ${
                activeTab === item.id
                  ? "bg-blue-50 text-blue-700 shadow-sm border border-blue-200"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="text-center">
          <div
            className={`w-3 h-3 rounded-full mx-auto mb-2 ${
              selectedBot.isActive
                ? "bg-green-400 animate-pulse"
                : "bg-gray-400"
            }`}
          ></div>
          <p className="text-sm text-gray-600">
            {selectedBot.isActive ? "Bot en ligne" : "Bot hors ligne"}
          </p>
          <p className="text-xs text-gray-500 mt-1">{selectedBot.token_pair}</p>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
