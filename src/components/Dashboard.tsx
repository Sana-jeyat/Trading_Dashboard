// Dashboard.jsx
import React, { useEffect, useState } from "react";
import { BotConfig, useBotContext } from "../context/BotContext";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Bot,
  Play,
  Pause,
  Plus,
  Zap,
  Coins,
  Fuel,
  AlertCircle,
  RefreshCw,
  BarChart3,
} from "lucide-react";

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
    getKnoPrice,
  } = useBotContext();

  const [knoPrice, setKnoPrice] = useState<number | null>(null);
  const [knoPriceLoading, setKnoPriceLoading] = useState(false);

  // Rafraîchissement automatique
  useEffect(() => {
    const interval = setInterval(() => {
      refreshData();
      fetchKnoPrice();
    }, 30000);

    return () => clearInterval(interval);
  }, [refreshData]);

  // Récupérer le prix KNO
  const fetchKnoPrice = async () => {
    setKnoPriceLoading(true);
    try {
      const price = await getKnoPrice();
      setKnoPrice(price);
    } catch (error) {
      console.error("Erreur récupération prix KNO:", error);
    } finally {
      setKnoPriceLoading(false);
    }
  };

  useEffect(() => {
    fetchKnoPrice();
  }, []);

  // Si en chargement
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Chargement du dashboard...</div>
      </div>
    );
  }

  // Si pas de bots
  if (!bots.length) {
    return (
      <div className="flex flex-col justify-center items-center h-64 space-y-4">
        <Bot className="w-12 h-12 text-gray-400" />
        <div className="text-lg text-gray-600">Aucun bot KNO disponible</div>
        {/* <button
          onClick={() => (window.location.href = "/BotManager")}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          <span>Créer votre premier bot KNO</span>
        </button> */}
      </div>
    );
  }

  const recentTransactions = transactions.slice(-3);
  const todaysPnL = transactions
    .filter((t) => t.profit)
    .reduce((acc, t) => acc + (t.profit || 0), 0);

  const statusColors = {
    active: "bg-green-100 text-green-800",
    paused: "bg-yellow-100 text-yellow-800",
    error: "bg-red-100 text-red-800",
    offline: "bg-gray-100 text-gray-800",
  };

  const statusLabels = {
    active: "Actif",
    paused: "En pause",
    error: "Erreur",
    offline: "Hors ligne",
  };

  const activeBotsCount = activeBots.length;
  const totalBalance = bots.reduce((acc, bot) => acc + bot.balance, 0);
  const totalProfit = bots.reduce((acc, bot) => acc + bot.total_profit, 0);

  // Calculer les statistiques KNO spécifiques
  const knoBots = bots.filter((bot) => bot.token_pair.includes("KNO"));
  const knoBotsCount = knoBots.length;
  const avgVolatility =
    knoBots.reduce((acc, bot) => acc + (bot.volatility_percent || 0), 0) /
      knoBotsCount || 0;

  // Fonctions pour contrôler tous les bots
  const startAllBots = () => {
    bots.forEach((bot) => {
      if (!bot.isActive) {
        startBot(bot.id);
      }
    });
  };

  const stopAllBots = () => {
    bots.forEach((bot) => {
      if (bot.isActive) {
        stopBot(bot.id);
      }
    });
  };

  // Fonction pour calculer les seuils du bot sélectionné
  const calculateBotThresholds = (bot: BotConfig) => {
    if (!bot.reference_price) return { buy: null, sell: null };

    const volatility = (bot.volatility_percent || 5) / 100;
    return {
      buy: bot.reference_price * (1 - volatility),
      sell: bot.reference_price * (1 + volatility),
    };
  };

  const selectedBotThresholds = selectedBot
    ? calculateBotThresholds(selectedBot)
    : { buy: null, sell: null };

  return (
    <div className="p-6 space-y-6">
      {/* En-tête avec contrôles globaux */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Dashboard KNO Trading
          </h1>
          <p className="text-gray-600 mt-1">
            Surveillance et contrôle des bots KNO sur Polygon
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          {/* Prix KNO actuel */}
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-3 rounded-lg min-w-[200px]">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-90">Prix KNO actuel</div>
                <div className="text-2xl font-bold">
                  {knoPriceLoading ? (
                    <div className="h-8 w-20 bg-blue-400/50 rounded animate-pulse"></div>
                  ) : knoPrice ? (
                    `${knoPrice.toFixed(6)} €`
                  ) : (
                    "N/A"
                  )}
                </div>
              </div>
              <button
                onClick={fetchKnoPrice}
                disabled={knoPriceLoading}
                className="p-2 bg-white/20 rounded-lg hover:bg-white/30 disabled:opacity-50"
              >
                <RefreshCw
                  className={`w-4 h-4 ${knoPriceLoading ? "animate-spin" : ""}`}
                />
              </button>
            </div>
          </div>

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
        </div>
      </div>

      {/* Stats Globale */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Solde Total</p>
              <p className="text-2xl font-bold text-gray-900">
                {totalBalance.toFixed(2)} €
              </p>
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
              <p
                className={`text-2xl font-bold ${
                  totalProfit >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {totalProfit >= 0 ? "+" : ""}
                {totalProfit.toFixed(2)} €
              </p>
            </div>
            <div
              className={`p-3 rounded-lg ${
                totalProfit >= 0 ? "bg-green-50" : "bg-red-50"
              }`}
            >
              <BarChart3
                className={`w-6 h-6 ${
                  totalProfit >= 0 ? "text-green-600" : "text-red-600"
                }`}
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Bots Actifs</p>
              <p className="text-2xl font-bold text-blue-600">
                {activeBotsCount}/{bots.length}
              </p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <Bot className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Volatilité Moyenne</p>
              <p className="text-2xl font-bold text-purple-600">
                {avgVolatility.toFixed(1)}%
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <Zap className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Liste des Bots KNO */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bot className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Mes Bots KNO ({knoBotsCount})
              </h3>
            </div>
            <div className="text-sm text-gray-500">
              {activeBotsCount} actif(s) sur {bots.length}
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bots.map((bot) => {
              const thresholds = calculateBotThresholds(bot);
              const botStatus =
                knoPrice && thresholds.buy && knoPrice <= thresholds.buy
                  ? "buy"
                  : knoPrice && thresholds.sell && knoPrice >= thresholds.sell
                  ? "sell"
                  : "neutral";

              return (
                <div
                  key={bot.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                    selectedBot?.id === bot.id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  } ${
                    botStatus === "buy"
                      ? "ring-2 ring-green-200"
                      : botStatus === "sell"
                      ? "ring-2 ring-red-200"
                      : ""
                  }`}
                  onClick={() => selectBot(bot.id)}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-semibold text-gray-900">
                          {bot.name}
                        </h4>
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            bot.isActive
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {bot.isActive ? "🟢 Actif" : "⚪ Inactif"}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{bot.token_pair}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleBot(bot.id);
                      }}
                      className={`p-2 rounded-lg ${
                        bot.isActive
                          ? "bg-yellow-500 hover:bg-yellow-600"
                          : "bg-green-500 hover:bg-green-600"
                      } text-white`}
                    >
                      {bot.isActive ? (
                        <Pause className="w-4 h-4" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {/* Indicateur de trading */}
                  {botStatus !== "neutral" && bot.isActive && knoPrice && (
                    <div
                      className={`mb-3 p-2 rounded-lg text-sm font-medium ${
                        botStatus === "buy"
                          ? "bg-green-50 text-green-700"
                          : "bg-red-50 text-red-700"
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        {botStatus === "buy" ? (
                          <>
                            <TrendingDown className="w-4 h-4" />
                            <span>Condition d'achat remplie</span>
                          </>
                        ) : (
                          <>
                            <TrendingUp className="w-4 h-4" />
                            <span>Condition de vente remplie</span>
                          </>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                    <div className="bg-gray-50 p-2 rounded">
                      <p className="text-gray-500 text-xs">Volatilité</p>
                      <p className="font-semibold">
                        {bot.volatility_percent || 5}%
                      </p>
                    </div>
                    <div className="bg-gray-50 p-2 rounded">
                      <p className="text-gray-500 text-xs">Prix Réf.</p>
                      <p className="font-semibold">
                        {bot.reference_price
                          ? `${bot.reference_price.toFixed(6)} €`
                          : "Non défini"}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-gray-500">Solde</p>
                      <p className="font-semibold">
                        {bot.balance.toFixed(2)} €
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Profit</p>
                      <p
                        className={`font-semibold ${
                          bot.total_profit >= 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {bot.total_profit >= 0 ? "+" : ""}
                        {bot.total_profit.toFixed(2)} €
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Détails du Bot Sélectionné */}
      {selectedBot && (
        <>
          {/* Bot Overview Card */}
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between mb-6 gap-4">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    {selectedBot.name}
                  </h2>
                  <p className="text-gray-600">Bot KNO sur Polygon</p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <div
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    statusColors[selectedBot.status] || statusColors.paused
                  }`}
                >
                  {statusLabels[selectedBot.status] || statusLabels.paused}
                </div>

                {selectedBotThresholds.buy &&
                  selectedBotThresholds.sell &&
                  knoPrice && (
                    <div className="flex items-center space-x-4 text-sm">
                      <div className="text-green-600">
                        <div className="font-medium">
                          Achat ≤ {selectedBotThresholds.buy.toFixed(6)}€
                        </div>
                        <div
                          className={`text-xs ${
                            knoPrice <= selectedBotThresholds.buy
                              ? "font-bold"
                              : ""
                          }`}
                        >
                          {knoPrice <= selectedBotThresholds.buy
                            ? "✅ Condition remplie"
                            : `(${(
                                selectedBotThresholds.buy - knoPrice
                              ).toFixed(6)}€)`}
                        </div>
                      </div>
                      <div className="text-red-600">
                        <div className="font-medium">
                          Vente ≥ {selectedBotThresholds.sell.toFixed(6)}€
                        </div>
                        <div
                          className={`text-xs ${
                            knoPrice >= selectedBotThresholds.sell
                              ? "font-bold"
                              : ""
                          }`}
                        >
                          {knoPrice >= selectedBotThresholds.sell
                            ? "✅ Condition remplie"
                            : `(+${(
                                selectedBotThresholds.sell - knoPrice
                              ).toFixed(6)}€)`}
                        </div>
                      </div>
                    </div>
                  )}
              </div>
            </div>

            {/* Configuration du bot */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Zap className="w-4 h-4 text-purple-600" />
                  <p className="text-sm text-gray-600">Volatilité</p>
                </div>
                <p className="text-lg font-semibold text-gray-900">
                  {selectedBot.volatility_percent || 5}%
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Coins className="w-4 h-4 text-blue-600" />
                  <p className="text-sm text-gray-600">Achat WPOL</p>
                </div>
                <p className="text-lg font-semibold text-gray-900">
                  {selectedBot.buy_amount || 0.05}
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Coins className="w-4 h-4 text-red-600" />
                  <p className="text-sm text-gray-600">Vente KNO</p>
                </div>
                <p className="text-lg font-semibold text-gray-900">
                  {selectedBot.sell_amount || 0.05}
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Fuel className="w-4 h-4 text-orange-600" />
                  <p className="text-sm text-gray-600">Gas Price</p>
                </div>
                <p className="text-lg font-semibold text-gray-900">
                  {selectedBot.gas_price || 30} Gwei
                </p>
              </div>
            </div>

            {/* Informations wallet */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600 font-medium">
                    Configuration Wallet
                  </p>
                  <p className="text-gray-700 text-sm mt-1">
                    {selectedBot.wallet_address ? (
                      <span className="font-mono">
                        {selectedBot.wallet_address.slice(0, 10)}...
                        {selectedBot.wallet_address.slice(-8)}
                      </span>
                    ) : (
                      <span className="text-yellow-600">Non configuré</span>
                    )}
                  </p>
                </div>
                <div className="text-xs text-gray-500">
                  {selectedBot.rpc_endpoint || "https://polygon-rpc.com"}
                </div>
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Solde du bot</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {(selectedBot.balance || 0).toFixed(2)} €
                  </p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <DollarSign className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Profit du bot</p>
                  <p
                    className={`text-2xl font-bold ${
                      (selectedBot.total_profit || 0) >= 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {((selectedBot.total_profit || 0) >= 0 ? "+" : "") +
                      (selectedBot.total_profit || 0).toFixed(2)}{" "}
                    €
                  </p>
                </div>
                <div
                  className={`p-3 rounded-lg ${
                    (selectedBot.total_profit || 0) >= 0
                      ? "bg-green-50"
                      : "bg-red-50"
                  }`}
                >
                  <BarChart3
                    className={`w-6 h-6 ${
                      (selectedBot.total_profit || 0) >= 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">PnL Aujourd'hui</p>
                  <p
                    className={`text-2xl font-bold ${
                      todaysPnL >= 0 ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {(todaysPnL >= 0 ? "+" : "") + todaysPnL.toFixed(2)} €
                  </p>
                </div>
                <div
                  className={`p-3 rounded-lg ${
                    todaysPnL >= 0 ? "bg-green-50" : "bg-red-50"
                  }`}
                >
                  {todaysPnL >= 0 ? (
                    <TrendingUp className="w-6 h-6 text-green-600" />
                  ) : (
                    <TrendingDown className="w-6 h-6 text-red-600" />
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Activité Récente */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Activité Récente
              </h3>
            </div>
            <button
              onClick={refreshData}
              className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Rafraîchir</span>
            </button>
          </div>
        </div>

        <div className="p-6">
          {recentTransactions.length > 0 ? (
            <div className="space-y-4">
              {recentTransactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className={`flex items-center justify-between p-4 rounded-lg ${
                    transaction.type === "buy" ? "bg-blue-50" : "bg-green-50"
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <div
                      className={`p-3 rounded-lg ${
                        transaction.type === "buy"
                          ? "bg-blue-100 text-blue-600"
                          : "bg-green-100 text-green-600"
                      }`}
                    >
                      {transaction.type === "buy" ? (
                        <TrendingDown className="w-5 h-5" />
                      ) : (
                        <TrendingUp className="w-5 h-5" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 capitalize">
                        {transaction.type === "buy" ? "Achat" : "Vente"}{" "}
                        {transaction.amount.toFixed(4)} KNO
                      </p>
                      <p className="text-sm text-gray-600">
                        {transaction.timestamp}
                      </p>
                      {transaction.tx_hash && (
                        <p className="text-xs text-gray-500 font-mono mt-1">
                          {transaction.tx_hash.slice(0, 10)}...
                          {transaction.tx_hash.slice(-8)}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">
                      {transaction.price.toFixed(6)} €
                    </p>
                    {transaction.profit && (
                      <p
                        className={`text-sm ${
                          transaction.profit >= 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {transaction.profit >= 0 ? "+" : ""}
                        {transaction.profit.toFixed(2)} €
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucune transaction récente</p>
              <p className="text-gray-400 text-sm mt-1">
                Les transactions apparaitront ici automatiquement
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
