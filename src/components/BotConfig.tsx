// components/BotConfig.jsx
"use client";

import React, { useState, useEffect } from "react";
import { useBotContext } from "../context/BotContext";
import {
  Save,
  CheckCircle,
  Activity,
  Wallet,
  Eye,
  EyeOff,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Zap,
  Settings,
  Shield,
} from "lucide-react";

// Fonction utilitaire pour valeurs sécurisées
const getSafeValue = (value, defaultValue) => {
  if (value === undefined || value === null) return defaultValue;
  return value;
};

function BotConfig() {
  const {
    selectedBot,
    selectedBotId,
    updateBotConfig,
    updateBotReferencePrice,
    getKnoPrice,
    loading: contextLoading,
  } = useBotContext();

  const [knoPrice, setKnoPrice] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showPrivateKey, setShowPrivateKey] = useState(false);

  // Configuration locale basée sur le bot sélectionné
  const [config, setConfig] = useState({
    volatility_percent: 5,
    buy_amount: 0.05,
    sell_amount: 0.05,
    min_swap_amount: 0.01,
    reference_price: null as number | null,
    slippage_tolerance: 1,
    gas_limit: 300000,
    gas_price: 30,
    random_trades_count: 0,
    trading_duration_hours: 24,
  });

  const [walletConfig, setWalletConfig] = useState({
    wallet_address: "",
    wallet_private_key: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Charger la configuration quand le bot change
  useEffect(() => {
    if (selectedBot && !saving) {
      setConfig({
        volatility_percent: getSafeValue(selectedBot.volatility_percent, 5),
        buy_amount: getSafeValue(selectedBot.buy_amount, 0.05),
        sell_amount: getSafeValue(selectedBot.sell_amount, 0.05),
        min_swap_amount: getSafeValue(selectedBot.min_swap_amount, 0.01),
        reference_price: getSafeValue(selectedBot.reference_price, null),
        slippage_tolerance: getSafeValue(selectedBot.slippage_tolerance, 1),
        gas_limit: getSafeValue(selectedBot.gas_limit, 300000),
        gas_price: getSafeValue(selectedBot.gas_price, 30),
        random_trades_count: getSafeValue(selectedBot.random_trades_count, 0),
        trading_duration_hours: getSafeValue(
          selectedBot.trading_duration_hours,
          24,
        ),
      });

      setWalletConfig({
        wallet_address: getSafeValue(selectedBot.wallet_address, ""),
        wallet_private_key: "",
      });
    }
  }, [selectedBot]);

  // Récupérer le prix KNO
  useEffect(() => {
    const fetchKnoPrice = async () => {
      try {
        const price = await getKnoPrice();
        setKnoPrice(price);
      } catch (error) {
        console.error("Erreur récupération prix KNO:", error);
      }
    };

    fetchKnoPrice();
    const interval = setInterval(fetchKnoPrice, 30000);
    return () => clearInterval(interval);
  }, [getKnoPrice]);

  // Validation
  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (config.buy_amount < config.min_swap_amount) {
      newErrors.buy_amount = `Doit être ≥ ${config.min_swap_amount}`;
    }

    if (config.sell_amount < config.min_swap_amount) {
      newErrors.sell_amount = `Doit être ≥ ${config.min_swap_amount}`;
    }

    if (config.volatility_percent < 0.1 || config.volatility_percent > 100) {
      newErrors.volatility_percent = "Doit être entre 0.1% et 100%";
    }

    if (
      walletConfig.wallet_address &&
      !/^0x[a-fA-F0-9]{40}$/.test(walletConfig.wallet_address)
    ) {
      newErrors.wallet_address = "Adresse Ethereum invalide";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) {
      alert("Veuillez corriger les erreurs avant de sauvegarder");
      return;
    }

    setSaving(true);

    try {
      // Préparer walletConfig avec toutes les adresses et rpc_endpoint
      const walletConfig: WalletConfig = {
        wallet_address: selectedBot?.wallet_address || "",
        wallet_private_key: selectedBot?.wallet_private_key || "",
        rpc_endpoint: selectedBot?.rpc_endpoint || "https://polygon-rpc.com",
        wpol_address:
          selectedBot?.wpol_address ||
          "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
        kno_address:
          selectedBot?.kno_address ||
          "0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631",
        router_address:
          selectedBot?.router_address ||
          "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
      };

      // Préparer les données de mise à jour principale
      const updateData: any = {
        volatility_percent: config.volatility_percent,
        buy_amount: config.buy_amount,
        sell_amount: config.sell_amount,
        min_swap_amount: config.min_swap_amount,
        reference_price: config.reference_price,
        slippage_tolerance: config.slippage_tolerance,
        gas_limit: config.gas_limit,
        gas_price: config.gas_price,
        random_trades_count: config.random_trades_count,
        trading_duration_hours: config.trading_duration_hours,
      };

      // Ajouter l'adresse wallet si modifiée
      if (
        selectedBot &&
        walletConfig.wallet_address !== selectedBot.wallet_address
      ) {
        updateData.wallet_address = walletConfig.wallet_address;
      }

      // Sauvegarder la configuration principale
      await updateBotConfig(selectedBotId, updateData);

      // Sauvegarder la configuration wallet séparément
      if (walletConfig.wallet_private_key) {
        await fetch(`http://mmk.knocoin.com/bots/${selectedBotId}/wallet`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(walletConfig),
        });
      }

      console.log("💾 Configuration du bot mise à jour avec succès");
    } catch (error) {
      console.error("Erreur lors de la sauvegarde :", error);
    } finally {
      setSaving(false);
    }
  };

  const handleSetCurrentPrice = async () => {
    if (knoPrice && selectedBotId) {
      try {
        await updateBotReferencePrice(selectedBotId, knoPrice);
        // Mettre à jour localement
        setConfig((prev) => ({ ...prev, reference_price: knoPrice }));
      } catch (error) {
        console.error("Erreur mise à jour prix de référence:", error);
      }
    }
  };

  const calculateThresholds = () => {
    const ref = config.reference_price || knoPrice || 0;
    const volatility = config.volatility_percent / 100;

    return {
      buy: ref * (1 - volatility),
      sell: ref * (1 + volatility),
      current: knoPrice || 0,
    };
  };

  const thresholds = calculateThresholds();
  const shouldBuy = knoPrice && thresholds.buy && knoPrice <= thresholds.buy;
  const shouldSell = knoPrice && thresholds.sell && knoPrice >= thresholds.sell;

  if (contextLoading) {
    return (
      <div className="p-6 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">Chargement...</p>
      </div>
    );
  }

  if (!selectedBot) {
    return (
      <div className="p-6 text-center">
        <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-700">
          Aucun bot sélectionné
        </h2>
        <p className="text-gray-500">
          Sélectionnez un bot pour configurer ses paramètres
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Settings className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Configuration KNO Bot
            </h1>
            <p className="text-gray-600">
              Bot #{selectedBotId} - {selectedBot.name}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {knoPrice && (
            <div className="bg-blue-50 px-4 py-2 rounded-lg">
              <div className="text-sm text-gray-600">Prix KNO actuel</div>
              <div className="text-xl font-bold text-blue-700">
                {knoPrice.toFixed(6)} €
              </div>
            </div>
          )}
          {saved && (
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Sauvegardé</span>
            </div>
          )}
        </div>
      </div>

      {/* Trading Status */}
      <div
        className={`rounded-xl p-6 ${
          shouldBuy
            ? "bg-green-50 border border-green-200"
            : shouldSell
              ? "bg-red-50 border border-red-200"
              : "bg-blue-50 border border-blue-200"
        }`}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Zap
              className={`w-6 h-6 ${
                shouldBuy
                  ? "text-green-600"
                  : shouldSell
                    ? "text-red-600"
                    : "text-blue-600"
              }`}
            />
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Statut de Trading
              </h2>
              <p className="text-gray-600">
                Basé sur le prix actuel et les seuils
              </p>
            </div>
          </div>

          <button
            onClick={handleSetCurrentPrice}
            className="flex items-center space-x-2 bg-white text-blue-600 px-4 py-2 rounded-lg hover:bg-blue-50 border border-blue-200"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Utiliser prix actuel</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            className={`p-4 rounded-lg ${
              shouldBuy ? "bg-green-100 border-2 border-green-300" : "bg-white"
            }`}
          >
            <div className="flex items-center space-x-2">
              <TrendingDown
                className={`w-5 h-5 ${
                  shouldBuy ? "text-green-700" : "text-gray-500"
                }`}
              />
              <span className="font-medium">Seuil Achat</span>
              {shouldBuy && (
                <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                  ACTIF
                </span>
              )}
            </div>
            <div
              className={`text-2xl font-bold mt-2 ${
                shouldBuy ? "text-green-700" : "text-gray-700"
              }`}
            >
              {thresholds.buy.toFixed(6)} €
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {config.reference_price
                ? `${config.volatility_percent}% en dessous`
                : "Prix de référence requis"}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-blue-600" />
              <span className="font-medium">Prix Actuel</span>
            </div>
            <div className="text-2xl font-bold text-blue-700 mt-2">
              {thresholds.current.toFixed(6)} €
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {knoPrice ? "Live depuis GeckoTerminal" : "Chargement..."}
            </div>
          </div>

          <div
            className={`p-4 rounded-lg ${
              shouldSell ? "bg-red-100 border-2 border-red-300" : "bg-white"
            }`}
          >
            <div className="flex items-center space-x-2">
              <TrendingUp
                className={`w-5 h-5 ${
                  shouldSell ? "text-red-700" : "text-gray-500"
                }`}
              />
              <span className="font-medium">Seuil Vente</span>
              {shouldSell && (
                <span className="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                  ACTIF
                </span>
              )}
            </div>
            <div
              className={`text-2xl font-bold mt-2 ${
                shouldSell ? "text-red-700" : "text-gray-700"
              }`}
            >
              {thresholds.sell.toFixed(6)} €
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {config.reference_price
                ? `${config.volatility_percent}% au dessus`
                : "Prix de référence requis"}
            </div>
          </div>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trading Parameters */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <Activity className="w-5 h-5 text-green-600" />
            <span>Paramètres de Trading</span>
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Volatilité (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="100"
                value={config.volatility_percent}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    volatility_percent: parseFloat(e.target.value),
                  }))
                }
                className={`w-full px-3 py-2 border rounded-lg ${
                  errors.volatility_percent
                    ? "border-red-300"
                    : "border-gray-300"
                }`}
              />
              {errors.volatility_percent && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.volatility_percent}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prix de Référence (€)
              </label>
              <input
                type="number"
                step="0.000001"
                min="0"
                value={config.reference_price || ""}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    reference_price: parseFloat(e.target.value) || null,
                  }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="0.001234"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Achat WPOL
                </label>
                <input
                  type="number"
                  step="0.001"
                  min={config.min_swap_amount}
                  value={config.buy_amount}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      buy_amount: parseFloat(e.target.value),
                    }))
                  }
                  className={`w-full px-3 py-2 border rounded-lg ${
                    errors.buy_amount ? "border-red-300" : "border-gray-300"
                  }`}
                />
                {errors.buy_amount && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.buy_amount}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Vente KNO
                </label>
                <input
                  type="number"
                  step="0.001"
                  min={config.min_swap_amount}
                  value={config.sell_amount}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      sell_amount: parseFloat(e.target.value),
                    }))
                  }
                  className={`w-full px-3 py-2 border rounded-lg ${
                    errors.sell_amount ? "border-red-300" : "border-gray-300"
                  }`}
                />
                {errors.sell_amount && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.sell_amount}
                  </p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Swap Minimum
              </label>
              <input
                type="number"
                step="0.0001"
                min="0.0001"
                value={config.min_swap_amount}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    min_swap_amount: parseFloat(e.target.value),
                  }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>
        </div>

        {/* Wallet & Transaction Settings */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <Wallet className="w-5 h-5 text-purple-600" />
            <span>Wallet & Transactions</span>
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Adresse Wallet
              </label>
              <input
                type="text"
                value={walletConfig.wallet_address}
                onChange={(e) =>
                  setWalletConfig((prev) => ({
                    ...prev,
                    wallet_address: e.target.value,
                  }))
                }
                className={`w-full px-3 py-2 border rounded-lg font-mono text-sm ${
                  errors.wallet_address ? "border-red-300" : "border-gray-300"
                }`}
                placeholder="0x1234..."
              />
              {errors.wallet_address && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.wallet_address}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center space-x-2">
                <Shield className="w-4 h-4 text-purple-600" />
                <span>Clé Privée</span>
              </label>
              <div className="relative">
                <input
                  type={showPrivateKey ? "text" : "password"}
                  value={walletConfig.wallet_private_key}
                  onChange={(e) =>
                    setWalletConfig((prev) => ({
                      ...prev,
                      wallet_private_key: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg font-mono text-sm"
                  placeholder="0xabcd..."
                />
                <button
                  type="button"
                  onClick={() => setShowPrivateKey(!showPrivateKey)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPrivateKey ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Ne la remplissez que si vous souhaitez la changer
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slippage (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10"
                  value={config.slippage_tolerance}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      slippage_tolerance: parseFloat(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gas Price (Gwei)
                </label>
                <input
                  type="number"
                  min="1"
                  max="200"
                  value={config.gas_price}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      gas_price: parseInt(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Gas Limit
              </label>
              <input
                type="number"
                min="100000"
                max="1000000"
                value={config.gas_limit}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    gas_limit: parseInt(e.target.value),
                  }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Additional Settings */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Paramètres Additionnels
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Trades Aléatoires
            </label>
            <input
              type="number"
              min="0"
              max="1000"
              value={config.random_trades_count}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  random_trades_count: parseInt(e.target.value),
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Durée Trading (heures)
            </label>
            <input
              type="number"
              min="1"
              max="720"
              value={config.trading_duration_hours}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  trading_duration_hours: parseInt(e.target.value),
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium ${
            saving
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700"
          } text-white transition-colors`}
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Sauvegarde...</span>
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              <span>Sauvegarder la Configuration</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default BotConfig;
