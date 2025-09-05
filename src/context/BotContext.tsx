import React, { createContext, useContext, useState } from 'react';

interface BotConfig {
  id: string;
  name: string;
  tokenPair: string;
  isActive: boolean;
  status: 'active' | 'paused' | 'error';
  buyPriceThreshold: number; // Prix < 0.007€
  buyPercentageDrop: number; // baisse de 10%+ depuis dernier achat
  sellPriceThreshold: number; // Prix > 0.009€
  sellPercentageGain: number; // hausse de 10%+ depuis dernière vente
  randomTradesCount: number; // nombre de trades aléatoires
  tradingDurationHours: number; // durée de trading en heures
  balance: number;
  totalProfit: number;
  lastBuyPrice?: number;
  lastSellPrice?: number;
  // Configuration Wallet
  walletAddress?: string;
  walletPrivateKey?: string;
  rpcEndpoint?: string;
  wpolAddress?: string;
  knoAddress?: string;
  routerAddress?: string;
  quoterAddress?: string;
  slippageTolerance?: number;
  gasLimit?: number;
  gasPrice?: number;
}

interface Transaction {
  id: string;
  type: 'buy' | 'sell';
  amount: number;
  price: number; // Prix en euros
  timestamp: string;
  profit?: number;
}

interface BotContextType {
  bots: BotConfig[];
  selectedBotId: string;
  selectedBot: BotConfig;
  transactions: Transaction[];
  updateBotConfig: (botId: string, config: Partial<BotConfig>) => void;
  toggleBot: (botId: string) => void;
  selectBot: (botId: string) => void;
  addBot: (bot: Omit<BotConfig, 'id'>) => void;
  deleteBot: (botId: string) => void;
}

const BotContext = createContext<BotContextType | undefined>(undefined);

export function BotProvider({ children }: { children: React.ReactNode }) {
  const [bots, setBots] = useState<BotConfig[]>([
    {
      id: 'bot-1',
      name: 'Bot Principal WPOL/KNO',
      tokenPair: 'WPOL/KNO',
      isActive: true,
      status: 'active',
      buyPriceThreshold: 0.007,
      buyPercentageDrop: 10,
      sellPriceThreshold: 0.009,
      sellPercentageGain: 10,
      randomTradesCount: 20,
      tradingDurationHours: 24,
      balance: 15420.50,
      totalProfit: 2340.75,
      lastBuyPrice: 0.0065,
      lastSellPrice: 0.0092
    },
    {
      id: 'bot-2',
      name: 'Bot ETH/USDC',
      tokenPair: 'ETH/USDC',
      isActive: false,
      status: 'paused',
      buyPriceThreshold: 2800,
      buyPercentageDrop: 5,
      sellPriceThreshold: 3200,
      sellPercentageGain: 8,
      randomTradesCount: 15,
      tradingDurationHours: 12,
      balance: 8500.00,
      totalProfit: 1250.30,
      lastBuyPrice: 2850,
      lastSellPrice: 3150
    },
    {
      id: 'bot-3',
      name: 'Bot BTC/USDT',
      tokenPair: 'BTC/USDT',
      isActive: false,
      status: 'paused',
      buyPriceThreshold: 65000,
      buyPercentageDrop: 3,
      sellPriceThreshold: 70000,
      sellPercentageGain: 5,
      randomTradesCount: 10,
      tradingDurationHours: 6,
      balance: 25000.00,
      totalProfit: 4500.00,
      lastBuyPrice: 66500,
      lastSellPrice: 69200
    }
  ]);
  
  const [selectedBotId, setSelectedBotId] = useState('bot-1');
  const selectedBot = bots.find(bot => bot.id === selectedBotId) || bots[0];

  const [transactions] = useState<Transaction[]>([
    {
      id: '1',
      type: 'buy',
      amount: 15000,
      price: 0.0065,
      timestamp: '2025-01-21 14:32:15'
    },
    {
      id: '2',
      type: 'sell',
      amount: 10000,
      price: 0.0092,
      timestamp: '2025-01-21 16:45:22',
      profit: 27.00
    },
    {
      id: '3',
      type: 'buy',
      amount: 8000,
      price: 0.0063,
      timestamp: '2025-01-21 18:20:10'
    },
    {
      id: '4',
      type: 'sell',
      amount: 5000,
      price: 0.0095,
      timestamp: '2025-01-21 20:15:35',
      profit: 16.00
    }
  ]);

  const updateBotConfig = (botId: string, config: Partial<BotConfig>) => {
    setBots(prev => prev.map(bot => 
      bot.id === botId ? { ...bot, ...config } : bot
    ));
  };

  const toggleBot = (botId: string) => {
    setBots(prev => prev.map(bot => 
      bot.id === botId ? {
        ...bot,
        isActive: !bot.isActive,
        status: !bot.isActive ? 'active' : 'paused'
      } : bot
    ));
  };

  const selectBot = (botId: string) => {
    setSelectedBotId(botId);
  };

  const addBot = (botData: Omit<BotConfig, 'id'>) => {
    const newBot: BotConfig = {
      ...botData,
      id: `bot-${Date.now()}`,
    };
    setBots(prev => [...prev, newBot]);
  };

  const deleteBot = (botId: string) => {
    setBots(prev => prev.filter(bot => bot.id !== botId));
    if (selectedBotId === botId) {
      setSelectedBotId(bots[0]?.id || '');
    }
  };

  return (
    <BotContext.Provider value={{ 
      bots, 
      selectedBotId, 
      selectedBot, 
      transactions, 
      updateBotConfig, 
      toggleBot, 
      selectBot, 
      addBot, 
      deleteBot 
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