import React, { createContext, useContext, useState, useEffect } from "react";
import {
  apiService,
  BotConfig as ApiBotConfig,
  Transaction as ApiTransaction,
} from "../services/api";

// Interface complète pour le bot KNO
export interface BotConfig {
  id: string;
  name: string;
  token_pair: string;
  isActive: boolean;
  status: "active" | "paused" | "error" | "offline";

  // Paramètres KNO spécifiques
  volatility_percent: number;
  buy_amount: number;
  sell_amount: number;
  min_swap_amount: number;
  reference_price: number | null;

  // Paramètres de trading optionnels
  random_trades_count: number;
  trading_duration_hours: number;
  swap_amount: number;

  // Configuration wallet
  wallet_address: string | null;
  wallet_private_key: string;
  rpc_endpoint: string;

  // Adresses des contrats
  wpol_address: string;
  kno_address: string;
  router_address: string;
  quoter_address: string;

  // Paramètres de transaction
  slippage_tolerance: number;
  gas_limit: number;
  gas_price: number;

  // Statistiques
  balance: number;
  total_profit: number;
  last_buy_price: number | null;
  last_sell_price: number | null;

  // Champs hérités (pour compatibilité)
  buy_price_threshold?: number;
  buy_percentage_drop?: number;
  sell_price_threshold?: number;
  sell_percentage_gain?: number;

  // Timestamps
  created_at?: string;
  updated_at?: string;
  last_heartbeat?: string;
}

interface Transaction {
  id: string;
  type: "buy" | "sell";
  amount: number;
  price: number;
  timestamp: string;
  profit?: number;
  botId?: string;
  tx_hash?: string;
}

interface BotContextType {
  bots: BotConfig[];
  activeBots: string[];
  selectedBotId: string;
  selectedBot: BotConfig;
  transactions: Transaction[];
  updateBotConfig: (botId: string, config: Partial<BotConfig>) => void;
  toggleBot: (botId: string) => void;
  startBot: (botId: string) => void;
  stopBot: (botId: string) => void;
  selectBot: (botId: string) => void;
  addBot: (bot: Omit<BotConfig, "id">) => void;
  deleteBot: (botId: string) => void;
  loading: boolean;
  refreshData: () => void;
  updateBotReferencePrice: (botId: string, price: number) => Promise<void>;
  getKnoPrice: () => Promise<number | null>;
}

const BotContext = createContext<BotContextType | undefined>(undefined);

export function BotProvider({ children }: { children: React.ReactNode }) {
  const [bots, setBots] = useState<BotConfig[]>([]);
  const [activeBots, setActiveBots] = useState<string[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<string>("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  // Charger les données au démarrage
  useEffect(() => {
    loadAllData();
  }, []);

  // Mettre à jour activeBots quand les bots changent
  useEffect(() => {
    const activeIds = bots.filter((bot) => bot.isActive).map((bot) => bot.id);
    setActiveBots(activeIds);
  }, [bots]);

  const loadAllData = async () => {
    try {
      setLoading(true);
      await Promise.all([loadBots(), loadTransactions()]);
    } catch (error) {
      console.error("Erreur chargement données:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadBots = async () => {
    try {
      const apiBots = await apiService.getBots();

      const formattedBots: BotConfig[] = apiBots.map((apiBot) => ({
        id: apiBot.id.toString(),
        name: apiBot.name,
        token_pair: apiBot.token_pair || "KNO/WPOL",
        isActive: apiBot.is_active,
        status: apiBot.status,

        // Paramètres KNO spécifiques
        volatility_percent: apiBot.volatility_percent ?? 5,
        buy_amount: apiBot.buy_amount ?? 0.05,
        sell_amount: apiBot.sell_amount ?? 0.05,
        min_swap_amount: apiBot.swap_amount ?? 0.01,
        reference_price: apiBot.reference_price,

        // Paramètres optionnels
        random_trades_count: apiBot.random_trades_count ?? 0,
        trading_duration_hours: apiBot.trading_duration_hours ?? 24,
        swap_amount: apiBot.swap_amount || 0.1,

        // Configuration Wallet
        wallet_address: apiBot.wallet_address || null,
        wallet_private_key: apiBot.wallet_private_key || "",
        rpc_endpoint: apiBot.rpc_endpoint || "https://polygon-rpc.com",

        // Adresses des contrats
        wpol_address:
          apiBot.wpol_address || "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
        kno_address:
          apiBot.kno_address || "0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631",
        router_address:
          apiBot.router_address || "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
        quoter_address: apiBot.quoter_address || "",

        // Paramètres de transaction
        slippage_tolerance: apiBot.slippage_tolerance || 1,
        gas_limit: apiBot.gas_limit || 300000,
        gas_price: apiBot.gas_price || 30,

        // Statistiques
        balance: apiBot.balance || 0,
        total_profit: apiBot.total_profit || 0,
        last_buy_price: apiBot.last_buy_price,
        last_sell_price: apiBot.last_sell_price,

        // Champs hérités
        buy_price_threshold: apiBot.buy_price_threshold,
        buy_percentage_drop: apiBot.buy_percentage_drop,
        sell_price_threshold: apiBot.sell_price_threshold,
        sell_percentage_gain: apiBot.sell_percentage_gain,

        // Timestamps
        created_at: apiBot.created_at,
        updated_at: apiBot.updated_at,
        last_heartbeat: apiBot.last_heartbeat,
      }));

      setBots(formattedBots);
      if (formattedBots.length > 0 && !selectedBotId) {
        setSelectedBotId(formattedBots[0].id);
      }
    } catch (error) {
      console.error("Erreur chargement bots:", error);
    }
  };

  const loadTransactions = async () => {
    try {
      const apiTransactions = await apiService.getTransactions();

      const formattedTransactions: Transaction[] = apiTransactions.map(
        (apiTx) => ({
          id: apiTx.id.toString(),
          type: apiTx.type as "buy" | "sell",
          amount: apiTx.amount,
          price: apiTx.price,
          timestamp: apiTx.timestamp,
          profit: apiTx.profit,
          botId: apiTx.bot_id?.toString(),
          tx_hash: apiTx.tx_hash,
        }),
      );

      setTransactions(formattedTransactions);
    } catch (error) {
      console.error("Erreur chargement transactions:", error);
    }
  };

  const selectedBot =
    bots.find((bot) => bot.id === selectedBotId) || bots[0] || getDefaultBot();

  function getDefaultBot(): BotConfig {
    return {
      id: "default",
      name: "Aucun bot",
      token_pair: "KNO/WPOL",
      isActive: false,
      status: "paused",

      // Paramètres KNO
      volatility_percent: 5,
      buy_amount: 0.05,
      sell_amount: 0.05,
      min_swap_amount: 0.01,
      reference_price: null,

      // Autres paramètres
      random_trades_count: 0,
      trading_duration_hours: 24,
      swap_amount: 0.1,

      // Configuration
      wallet_address: null,
      wallet_private_key: "",
      rpc_endpoint: "https://polygon-rpc.com",
      wpol_address: "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
      kno_address: "0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631",
      router_address: "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
      quoter_address: "",

      // Paramètres transaction
      slippage_tolerance: 1,
      gas_limit: 300000,
      gas_price: 30,

      // Statistiques
      balance: 0,
      total_profit: 0,
      last_buy_price: null,
      last_sell_price: null,
    };
  }

  const refreshData = () => {
    loadAllData();
  };

  const addBot = async (botData: Omit<BotConfig, "id">) => {
    try {
      const apiBotData = {
        name: botData.name,
        token_pair: botData.token_pair || "KNO/WPOL",

        // Paramètres KNO
        volatility_percent: botData.volatility_percent,
        buy_amount: botData.buy_amount,
        sell_amount: botData.sell_amount,
        min_swap_amount: botData.min_swap_amount,
        reference_price: botData.reference_price,

        // Paramètres de trading
        random_trades_count: botData.random_trades_count,
        trading_duration_hours: botData.trading_duration_hours,
        swap_amount: botData.swap_amount,

        // Configuration wallet
        wallet_address: botData.wallet_address,
        wallet_private_key: botData.wallet_private_key,
        rpc_endpoint: botData.rpc_endpoint,

        // Adresses
        wpol_address: botData.wpol_address,
        kno_address: botData.kno_address,
        router_address: botData.router_address,
        quoter_address: botData.quoter_address,

        // Paramètres transaction
        slippage_tolerance: botData.slippage_tolerance,
        gas_limit: botData.gas_limit,
        gas_price: botData.gas_price,

        // Champs obligatoires pour compatibilité
        buy_price_threshold: 0,
        buy_percentage_drop: botData.volatility_percent || 5,
        sell_price_threshold: 0,
        sell_percentage_gain: botData.volatility_percent || 5,
      };

      console.log("📤 Création bot KNO:", apiBotData);
      await apiService.createBot(apiBotData);
      await loadBots();
    } catch (error) {
      console.error("Erreur création bot:", error);
      throw error;
    }
  };

  const startBot = async (botId: string) => {
    try {
      await apiService.startBot(botId);
      await loadBots();
    } catch (error) {
      console.error("Erreur démarrage bot:", error);
      throw error;
    }
  };

  const stopBot = async (botId: string) => {
    try {
      await apiService.stopBot(botId);
      await loadBots();
    } catch (error) {
      console.error("Erreur arrêt bot:", error);
      throw error;
    }
  };

  const toggleBot = async (botId: string) => {
    const bot = bots.find((b) => b.id === botId);
    if (!bot) return;

    const newIsActive = !bot.isActive;
    const newStatus = newIsActive ? "active" : "paused";

    setBots((prev) =>
      prev.map((b) =>
        b.id === botId ? { ...b, isActive: newIsActive, status: newStatus } : b,
      ),
    );

    try {
      if (newIsActive) {
        await startBot(botId);
      } else {
        await stopBot(botId);
      }
    } catch (error) {
      console.error("Erreur toggleBot:", error);
      setBots((prev) =>
        prev.map((b) =>
          b.id === botId
            ? { ...b, isActive: bot.isActive, status: bot.status }
            : b,
        ),
      );
    }
  };

  const updateBotConfig = async (botId: string, config: Partial<BotConfig>) => {
    try {
      // Mapping des champs frontend → backend
      const fieldMappings: { [key: string]: string } = {
        // Paramètres KNO
        volatility_percent: "volatility_percent",
        buy_amount: "buy_amount",
        sell_amount: "sell_amount",
        min_swap_amount: "min_swap_amount",
        reference_price: "reference_price",

        // Paramètres trading
        random_trades_count: "random_trades_count",
        trading_duration_hours: "trading_duration_hours",
        swap_amount: "swap_amount",

        // Wallet
        wallet_address: "wallet_address",
        wallet_private_key: "wallet_private_key",
        rpc_endpoint: "rpc_endpoint",

        // Adresses
        wpol_address: "wpol_address",
        kno_address: "kno_address",
        router_address: "router_address",
        quoter_address: "quoter_address",

        // Transaction
        slippage_tolerance: "slippage_tolerance",
        gas_limit: "gas_limit",
        gas_price: "gas_price",

        // Statut
        isActive: "is_active",
        status: "status",

        // Statistiques
        balance: "balance",
        total_profit: "total_profit",
        last_buy_price: "last_buy_price",
        last_sell_price: "last_sell_price",

        // Champs de base
        name: "name",
        token_pair: "token_pair",
      };

      const apiConfig: any = {};
      Object.keys(config).forEach((key) => {
        const apiKey = fieldMappings[key] || key;
        apiConfig[apiKey] = (config as any)[key];
      });

      await apiService.updateBot(botId, apiConfig);

      // 🔹 Mise à jour locale immédiate
      setBots((prev) =>
        prev.map((bot) => (bot.id === botId ? { ...bot, ...config } : bot)),
      );
    } catch (error) {
      console.error("Erreur mise à jour bot:", error);
      throw error;
    }
  };

  // Nouvelle fonction pour mettre à jour le prix de référence
  const updateBotReferencePrice = async (botId: string, price: number) => {
    try {
      await apiService.updateBotReferencePrice(botId, price);
      await loadBots(); // Recharger pour avoir la valeur mise à jour
    } catch (error) {
      console.error("Erreur mise à jour prix de référence:", error);
      throw error;
    }
  };

  // Fonction pour récupérer le prix KNO
  const getKnoPrice = async (): Promise<number | null> => {
    try {
      const response = await fetch("/api/kno/price");
      const data = await response.json();
      return data.price_eur || null;
    } catch (error) {
      console.error("Erreur récupération prix KNO:", error);
      return null;
    }
  };

  const deleteBot = async (botId: string) => {
    try {
      await apiService.deleteBot(botId);
      await loadBots();
    } catch (error) {
      console.error("Erreur suppression bot:", error);
    }
  };

  return (
    <BotContext.Provider
      value={{
        bots,
        activeBots,
        selectedBotId,
        selectedBot,
        transactions,
        updateBotConfig,
        toggleBot,
        startBot,
        stopBot,
        selectBot: setSelectedBotId,
        addBot,
        deleteBot,
        loading,
        refreshData,
        updateBotReferencePrice,
        getKnoPrice,
      }}
    >
      {children}
    </BotContext.Provider>
  );
}

export function useBotContext() {
  const context = useContext(BotContext);
  if (context === undefined) {
    throw new Error("useBotContext must be used within a BotProvider");
  }
  return context;
}
