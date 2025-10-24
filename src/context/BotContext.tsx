import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService, BotConfig as ApiBotConfig, Transaction as ApiTransaction } from '../services/api';

interface BotConfig {
  id: string;
  name: string;
  tokenPair: string;
  isActive: boolean;
  status: 'active' | 'paused' | 'error';
  buyPriceThreshold: number;
  buyPercentageDrop: number;
  sellPriceThreshold: number;
  sellPercentageGain: number;
  randomTradesCount: number;
  tradingDurationHours: number;
  balance: number;
  totalProfit: number;
  lastBuyPrice?: number;
  lastSellPrice?: number;
}

interface Transaction {
  id: string;
  type: 'buy' | 'sell';
  amount: number;
  price: number;
  timestamp: string;
  profit?: number;
  botId?: string; // Ajoutez botId pour associer les transactions
}

interface BotContextType {
  bots: BotConfig[];
  activeBots: string[]; // NOUVEAU: Liste des IDs des bots actifs
  selectedBotId: string;
  selectedBot: BotConfig;
  transactions: Transaction[];
  updateBotConfig: (botId: string, config: Partial<BotConfig>) => void;
  toggleBot: (botId: string) => void;
  startBot: (botId: string) => void; // NOUVEAU
  stopBot: (botId: string) => void; // NOUVEAU
  selectBot: (botId: string) => void;
  addBot: (bot: Omit<BotConfig, 'id'>) => void;
  deleteBot: (botId: string) => void;
  loading: boolean;
  refreshData: () => void;
}

const BotContext = createContext<BotContextType | undefined>(undefined);

export function BotProvider({ children }: { children: React.ReactNode }) {
  const [bots, setBots] = useState<BotConfig[]>([]);
  const [activeBots, setActiveBots] = useState<string[]>([]); // NOUVEAU
  const [selectedBotId, setSelectedBotId] = useState<string>('');
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  // Charger les données au démarrage
  useEffect(() => {
    loadAllData();
  }, []);

  // Mettre à jour activeBots quand les bots changent
  useEffect(() => {
    const activeIds = bots.filter(bot => bot.isActive).map(bot => bot.id);
    setActiveBots(activeIds);
  }, [bots]);

  const loadAllData = async () => {
    try {
      setLoading(true);
      await Promise.all([loadBots(), loadTransactions()]);
    } catch (error) {
      console.error('Erreur chargement données:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadBots = async () => {
    try {
      const apiBots = await apiService.getBots();
      
      const formattedBots: BotConfig[] = apiBots.map(apiBot => ({
        id: apiBot.id.toString(),
        name: apiBot.name,
        tokenPair: apiBot.token_pair,
        isActive: apiBot.is_active,
        status: apiBot.status,
        buyPriceThreshold: apiBot.buy_price_threshold,
        buyPercentageDrop: apiBot.buy_percentage_drop,
        sellPriceThreshold: apiBot.sell_price_threshold,
        sellPercentageGain: apiBot.sell_percentage_gain,
        randomTradesCount: apiBot.random_trades_count,
        tradingDurationHours: apiBot.trading_duration_hours,
        balance: apiBot.balance,
        totalProfit: apiBot.total_profit,
        lastBuyPrice: apiBot.last_buy_price,
        lastSellPrice: apiBot.last_sell_price
      }));

      setBots(formattedBots);
      if (formattedBots.length > 0 && !selectedBotId) {
        setSelectedBotId(formattedBots[0].id);
      }
    } catch (error) {
      console.error('Erreur chargement bots:', error);
    }
  };

  const loadTransactions = async () => {
    try {
      const apiTransactions = await apiService.getTransactions();
      
      const formattedTransactions: Transaction[] = apiTransactions.map(apiTx => ({
        id: apiTx.id.toString(),
        type: apiTx.type as 'buy' | 'sell',
        amount: apiTx.amount,
        price: apiTx.price,
        timestamp: apiTx.timestamp,
        profit: apiTx.profit,
        botId: apiTx.bot_id?.toString() // Assurez-vous que votre API retourne bot_id
      }));

      setTransactions(formattedTransactions);
    } catch (error) {
      console.error('Erreur chargement transactions:', error);
    }
  };

  const selectedBot = bots.find(bot => bot.id === selectedBotId) || bots[0] || getDefaultBot();

  function getDefaultBot(): BotConfig {
    return {
      id: 'default',
      name: 'Aucun bot',
      tokenPair: 'N/A',
      isActive: false,
      status: 'paused',
      buyPriceThreshold: 0,
      buyPercentageDrop: 0,
      sellPriceThreshold: 0,
      sellPercentageGain: 0,
      randomTradesCount: 0,
      tradingDurationHours: 0,
      balance: 0,
      totalProfit: 0
    };
  }

  const refreshData = () => {
    loadAllData();
  };

  const addBot = async (botData: Omit<BotConfig, 'id'>) => {
    try {
      const apiBotData = {
        name: botData.name,
        token_pair: botData.tokenPair,
        buy_price_threshold: botData.buyPriceThreshold,
        buy_percentage_drop: botData.buyPercentageDrop,
        sell_price_threshold: botData.sellPriceThreshold,
        sell_percentage_gain: botData.sellPercentageGain,
        random_trades_count: botData.randomTradesCount,
        trading_duration_hours: botData.tradingDurationHours
      };

      await apiService.createBot(apiBotData);
      await loadBots();
      
    } catch (error) {
      console.error('Erreur création bot:', error);
      throw error;
    }
  };

  // NOUVELLE FONCTION: Démarrer un bot spécifique
  const startBot = async (botId: string) => {
    try {
      await apiService.startBot(botId);
      await loadBots(); // Recharger les statuts
    } catch (error) {
      console.error('Erreur démarrage bot:', error);
      throw error;
    }
  };

  // NOUVELLE FONCTION: Arrêter un bot spécifique
  const stopBot = async (botId: string) => {
    try {
      await apiService.stopBot(botId);
      await loadBots(); // Recharger les statuts
    } catch (error) {
      console.error('Erreur arrêt bot:', error);
      throw error;
    }
  };

  // MODIFIÉ: Toggle bot utilisant les nouvelles fonctions
  const toggleBot = async (botId: string) => {
    try {
      const bot = bots.find(b => b.id === botId);
      if (!bot) return;

      if (bot.isActive) {
        await stopBot(botId);
      } else {
        await startBot(botId);
      }
    } catch (error) {
      console.error('Erreur toggle bot:', error);
    }
  };

  const updateBotConfig = async (botId: string, config: Partial<BotConfig>) => {
    try {
      const apiConfig: any = {};
      Object.keys(config).forEach(key => {
        const apiKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
        apiConfig[apiKey] = (config as any)[key];
      });

      await apiService.updateBot(botId, apiConfig);
      await loadBots();
      
    } catch (error) {
      console.error('Erreur mise à jour bot:', error);
    }
  };

  const deleteBot = async (botId: string) => {
    try {
      await apiService.deleteBot(botId);
      await loadBots();
    } catch (error) {
      console.error('Erreur suppression bot:', error);
    }
  };

  return (
    <BotContext.Provider value={{ 
      bots, 
      activeBots, // NOUVEAU
      selectedBotId, 
      selectedBot,
      transactions, 
      updateBotConfig, 
      toggleBot,
      startBot, // NOUVEAU
      stopBot, // NOUVEAU
      selectBot: setSelectedBotId, 
      addBot, 
      deleteBot,
      loading,
      refreshData
    }}>
      {children}
    </BotContext.Provider>
  );
}

export function useBotContext() {
  const context = useContext(BotContext);
  if (context === undefined) {
    throw new Error('useBotContext must be used within a BotProvider');
  }
  return context;
}