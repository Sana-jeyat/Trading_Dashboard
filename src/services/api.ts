// const API_BASE_URL = 'http://localhost:8000';

// // Types pour l'API
// export interface BotConfig {
//   id: string;
//   name: string;
//   tokenPair: string;
//   isActive: boolean;
//   status: 'active' | 'paused' | 'error';
//   buyPriceThreshold: number;
//   buyPercentageDrop: number;
//   sellPriceThreshold: number;
//   sellPercentageGain: number;
//   randomTradesCount: number;
//   tradingDurationHours: number;
//   balance: number;
//   totalProfit: number;
//   lastBuyPrice?: number;
//   lastSellPrice?: number;
//   githubRepo?: string;
//   scriptPath?: string;
// }

// export interface Transaction {
//   id: string;
//   type: 'buy' | 'sell';
//   amount: number;
//   price: number;
//   timestamp: string;
//   profit?: number;
//   txHash?: string;
// }

// class ApiService {
//   private token: string | null = null;

//   setToken(token: string) {
//     this.token = token;
//     localStorage.setItem('auth_token', token);
//   }

//   getToken(): string | null {
//     if (!this.token) {
//       this.token = localStorage.getItem('auth_token');
//     }
//     return this.token;
//   }

//   private async request(endpoint: string, options: RequestInit = {}) {
//     const token = this.getToken();
//     const headers: HeadersInit = {
//       'Content-Type': 'application/json',
//       ...options.headers,
//     };

//     if (token) {
//       headers.Authorization = `Bearer ${token}`;
//     }

//     const response = await fetch(`${API_BASE_URL}${endpoint}`, {
//       ...options,
//       headers,
//     });

//     if (!response.ok) {
//       throw new Error(`API Error: ${response.statusText}`);
//     }

//     return response.json();
//   }

//   // Authentification
//   async login(email: string, password: string) {
//     const response = await this.request('/auth/login', {
//       method: 'POST',
//       body: JSON.stringify({ email, password }),
//     });
//     this.setToken(response.access_token);
//     return response;
//   }

//   async register(email: string, password: string) {
//     return this.request('/auth/register', {
//       method: 'POST',
//       body: JSON.stringify({ email, password }),
//     });
//   }

//   // Gestion des bots
//   async getBots(): Promise<BotConfig[]> {
//     return this.request('/bots');
//   }

//   async createBot(bot: Omit<BotConfig, 'id'>): Promise<BotConfig> {
//     return this.request('/bots', {
//       method: 'POST',
//       body: JSON.stringify(bot),
//     });
//   }

//   async updateBot(botId: string, updates: Partial<BotConfig>): Promise<BotConfig> {
//     return this.request(`/bots/${botId}`, {
//       method: 'PUT',
//       body: JSON.stringify(updates),
//     });
//   }

//   async deleteBot(botId: string) {
//     return this.request(`/bots/${botId}`, {
//       method: 'DELETE',
//     });
//   }

//   async startBot(botId: string) {
//     return this.request(`/bots/${botId}/start`, {
//       method: 'POST',
//     });
//   }

//   async stopBot(botId: string) {
//     return this.request(`/bots/${botId}/stop`, {
//       method: 'POST',
//     });
//   }

//   // Transactions
//   async getTransactions(botId?: string): Promise<Transaction[]> {
//     const endpoint = botId ? `/bots/${botId}/transactions` : '/transactions';
//     return this.request(endpoint);
//   }

//   // Statistiques
//   async getStats() {
//     return this.request('/stats');
//   }

//   // Intégration GitHub
//   async deployBotFromGithub(botId: string, githubRepo: string, scriptPath: string) {
//     return this.request(`/bots/${botId}/deploy-github`, {
//       method: 'POST',
//       body: JSON.stringify({ githubRepo, scriptPath }),
//     });
//   }
// }

// export const apiService = new ApiService();

// api.tsx - Version corrigée
const API_BASE_URL = 'http://mmk.knocoin.com';

// Types pour l'API - CORRIGÉS pour matcher le backend
export interface BotConfig {
  last_heartbeat: any;
  updated_at: any;
  created_at: any;
  sell_percentage_gain: any;
  sell_price_threshold: any;
  buy_price_threshold: any;
  reference_price: any;
  sell_amount: number;
  is_active: any;
  buy_amount: number;
  last_sell_price: any;
  last_buy_price: any;
  buy_percentage_drop: any;
  id: string;
  name: string;
  token_pair: string;
  isActive: boolean;
  status: "active" | "paused" | "error";

  volatility_percent: number;
  random_trades_count: number;
  trading_duration_hours: number;
  swap_amount: number;

  wallet_address: string;
  wallet_private_key: string;
  rpc_endpoint: string;
  wpol_address: string;
  kno_address: string;
  router_address: string;
  quoter_address: string;

  slippage_tolerance: number;
  gas_limit: number;
  gas_price: number;

  balance: number;
  total_profit: number;
}

export interface Transaction {
  bot_id: any;
  botId: string;
  id: number;
  type: 'buy' | 'sell';
  amount: number;
  price: number;
  timestamp: string;
  profit?: number;
  tx_hash?: string;
}

class ApiService {
  updateBotReferencePrice(botId: string, price: number) {
    throw new Error("Method not implemented.");
  }
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    //const token = this.getToken();
    const token = null; // ← Désactive l'envoi du token

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // if (token) {
    //   headers.Authorization = `Bearer ${token}`;
    // }

    console.log(`🔄 API Call: ${endpoint}`, { method: options.method, body: options.body });

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ API Error ${response.status}:`, errorText);
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    console.log(`✅ API Success:`, data);
    return data;
  }

  // Authentification
  async login(email: string, password: string) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(response.access_token);
    return response;
  }

  async register(email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  // Gestion des bots - CORRIGÉ
  async getBots(): Promise<BotConfig[]> {
    return this.request('/bots');
  }

  async createBot(botData: {
    name: string;
    token_pair: string;
    buy_price_threshold: number;
    buy_percentage_drop: number;
    sell_price_threshold: number;
    sell_percentage_gain: number;
    random_trades_count?: number;
    trading_duration_hours?: number;
    wallet_address?: string;
    wallet_private_key?: string;  // Pour la création seulement
    rpc_endpoint?: string;
    wpol_address?: string;
    kno_address?: string;
    router_address?: string;
    quoter_address?: string;
    slippage_tolerance?: number;
    gas_limit?: number;
    gas_price?: number;
  }): Promise<BotConfig> {
    return this.request('/bots', {
      method: 'POST',
      body: JSON.stringify(botData),
    });
  }

  async updateBot(botId: string, updates: any): Promise<BotConfig> {
    return this.request(`/bots/${botId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteBot(botId: string) {
    return this.request(`/bots/${botId}`, {
      method: 'DELETE',
    });
  }

  async startBot(botId: string) {
    return this.request(`/bots/${botId}/start`, {
      method: 'POST',
    });
  }

  async stopBot(botId: string) {
    return this.request(`/bots/${botId}/stop`, {
      method: 'POST',
    });
  }

  // Transactions
  async getTransactions(botId?: string): Promise<Transaction[]> {
    const endpoint = botId ? `/bots/${botId}/transactions` : '/transactions';
    return this.request(endpoint);
  }

  // Statistiques
  async getStats() {
    return this.request('/stats');
  }
}

export const apiService = new ApiService();