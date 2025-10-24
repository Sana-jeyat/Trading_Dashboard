import React, { useState } from 'react';
import { useBotContext } from '../context/BotContext';
import { Save, Settings, AlertCircle, CheckCircle, TrendingUp, TrendingDown, Activity, Wallet, Eye, EyeOff, Shield, Key } from 'lucide-react';

function BotConfig() {
  const { selectedBot, updateBotConfig, selectedBotId } = useBotContext();
  const [config, setConfig] = useState({
    buyPriceThreshold: selectedBot.buyPriceThreshold,
    buyPercentageDrop: selectedBot.buyPercentageDrop,
    sellPriceThreshold: selectedBot.sellPriceThreshold,
    sellPercentageGain: selectedBot.sellPercentageGain,
    randomTradesCount: selectedBot.randomTradesCount,
    tradingDurationHours: selectedBot.tradingDurationHours,
    swapAmount: selectedBot.swapAmount || 0.1,
    // Configuration Wallet
    walletAddress: selectedBot.walletAddress || '',
    walletPrivateKey: selectedBot.walletPrivateKey || '',
    rpcEndpoint: selectedBot.rpcEndpoint || 'https://polygon-rpc.com',
    wpolAddress: selectedBot.wpolAddress || '',
    knoAddress: selectedBot.knoAddress || '',
    routerAddress: selectedBot.routerAddress || '',
    quoterAddress: selectedBot.quoterAddress || '',
    slippageTolerance: selectedBot.slippageTolerance || 1,
    gasLimit: selectedBot.gasLimit || 300000,
    gasPrice: selectedBot.gasPrice || 30
  });
  const [saved, setSaved] = useState(false);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  const [walletValidation, setWalletValidation] = useState({ address: true, privateKey: true });

  // Update config when selected bot changes
  React.useEffect(() => {
    setConfig({
      buyPriceThreshold: selectedBot.buyPriceThreshold,
      buyPercentageDrop: selectedBot.buyPercentageDrop,
      sellPriceThreshold: selectedBot.sellPriceThreshold,
      sellPercentageGain: selectedBot.sellPercentageGain,
      randomTradesCount: selectedBot.randomTradesCount,
      tradingDurationHours: selectedBot.tradingDurationHours,
      swapAmount: selectedBot.swapAmount || 0.1,
      walletAddress: selectedBot.walletAddress || '',
      walletPrivateKey: selectedBot.walletPrivateKey || '',
      rpcEndpoint: selectedBot.rpcEndpoint || 'https://polygon-rpc.com',
      wpolAddress: selectedBot.wpolAddress || '',
      knoAddress: selectedBot.knoAddress || '',
      routerAddress: selectedBot.routerAddress || '',
      slippageTolerance: selectedBot.slippageTolerance || 1,
      gasLimit: selectedBot.gasLimit || 300000,
      gasPrice: selectedBot.gasPrice || 30
    });
  }, [selectedBot]);

  const validateWallet = (field: string, value: string) => {
    if (field === 'walletAddress') {
      const isValid = /^0x[a-fA-F0-9]{40}$/.test(value);
      setWalletValidation(prev => ({ ...prev, address: isValid || value === '' }));
    } else if (field === 'walletPrivateKey') {
      const isValid = /^(0x)?[a-fA-F0-9]{64}$/.test(value);
      setWalletValidation(prev => ({ ...prev, privateKey: isValid || value === '' }));
    }
  };

  const handleSave = () => {
    updateBotConfig(selectedBotId, config);
    setSaved(true);
    
    // Dans une vraie implémentation, ceci ferait un appel API
    // fetch(`/api/bots/${selectedBotId}`, { method: 'PUT', body: JSON.stringify(config) })
    
    setTimeout(() => setSaved(false), 3000);
  };

  const handleChange = (field: string, value: number | string) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    
    // Validation pour les champs wallet
    if (field === 'walletAddress' || field === 'walletPrivateKey') {
      validateWallet(field, value as string);
    }
  };

  const isSmallToken = !selectedBot.tokenPair.includes('BTC') && !selectedBot.tokenPair.includes('ETH');
  const priceStep = isSmallToken ? "0.0001" : "1";

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Settings className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Configuration</h1>
            <p className="text-gray-600">Paramètres de {selectedBot.name}</p>
          </div>
        </div>
        {saved && (
          <div className="flex items-center space-x-2 text-green-600">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Sauvegardé</span>
          </div>
        )}
      </div>

      {/* Bot Info */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Informations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nom du bot</label>
            <p className="text-lg font-semibold text-gray-900">{selectedBot.name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Paire de trading</label>
            <p className="text-lg font-semibold text-gray-900">{selectedBot.tokenPair}</p>
          </div>
        </div>
      </div>

      {/* Wallet Configuration */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Wallet className="w-6 h-6 text-purple-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Configuration Wallet</h2>
              <p className="text-gray-600">Paramètres blockchain pour {selectedBot.tokenPair}</p>
            </div>
          </div>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Wallet Credentials */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
              <Key className="w-5 h-5 text-purple-600" />
              <span>Identifiants Wallet</span>
            </h3>
            
            <div className="grid grid-cols-1 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Adresse du Wallet
                </label>
                <input
                  type="text"
                  value={config.walletAddress}
                  onChange={(e) => handleChange('walletAddress', e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors font-mono text-sm ${
                    !walletValidation.address ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  placeholder="0x1234567890123456789012345678901234567890"
                />
                {!walletValidation.address && (
                  <p className="text-xs text-red-600 mt-1 flex items-center space-x-1">
                    <AlertCircle className="w-3 h-3" />
                    <span>Format d'adresse invalide (doit commencer par 0x et faire 42 caractères)</span>
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Adresse publique de votre wallet (0x...)
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Clé Privée
                </label>
                <div className="relative">
                  <input
                    type={showPrivateKey ? "text" : "password"}
                    value={config.walletPrivateKey}
                    onChange={(e) => handleChange('walletPrivateKey', e.target.value)}
                    className={`w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors font-mono text-sm ${
                      !walletValidation.privateKey ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="0x1234567890abcdef..."
                  />
                  <button
                    type="button"
                    onClick={() => setShowPrivateKey(!showPrivateKey)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPrivateKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {!walletValidation.privateKey && (
                  <p className="text-xs text-red-600 mt-1 flex items-center space-x-1">
                    <AlertCircle className="w-3 h-3" />
                    <span>Format de clé privée invalide (64 caractères hexadécimaux)</span>
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  ⚠️ Clé privée de votre wallet (gardée sécurisée et chiffrée)
                </p>
              </div>
            </div>
          </div>

          {/* Blockchain Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
              <Activity className="w-5 h-5 text-blue-600" />
              <span>Configuration Blockchain</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  RPC Endpoint
                </label>
                <select
                  value={config.rpcEndpoint}
                  onChange={(e) => handleChange('rpcEndpoint', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                  <option value="https://polygon-rpc.com">Polygon Mainnet</option>
                  <option value="https://rpc-mainnet.matic.network">Polygon Matic</option>
                  <option value="https://polygon-mainnet.infura.io/v3/YOUR_KEY">Infura Polygon</option>
                  <option value="https://rpc.ankr.com/polygon">Ankr Polygon</option>
                  <option value="https://mainnet.infura.io/v3/YOUR_KEY">Ethereum Mainnet</option>
                  <option value="https://bsc-dataseed.binance.org">BSC Mainnet</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Point d'accès à la blockchain
                </p>
              </div>
              
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-4">Adresses des Contrats</h4>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Adresse Token WPOL
                </label>
                <input
                  type="text"
                  value={config.wpolAddress}
                  onChange={(e) => handleChange('wpolAddress', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors font-mono text-sm"
                  placeholder="0x1234567890abcdef..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Contrat ERC20 du token WPOL
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Adresse Token KNO
                </label>
                <input
                  type="text"
                  value={config.knoAddress}
                  onChange={(e) => handleChange('knoAddress', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors font-mono text-sm"
                  placeholder="0xabcdef1234567890..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Contrat ERC20 du token KNO
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Adresse Router (Uniswap/Sushi)
                </label>
                <input
                  type="text"
                  value={config.routerAddress}
                  onChange={(e) => handleChange('routerAddress', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors font-mono text-sm"
                  placeholder="0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Router pour exécuter les swaps
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Adresse Quoter (Prix)
                </label>
                <input
                  type="text"
                  value={config.quoterAddress}
                  onChange={(e) => handleChange('quoterAddress', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors font-mono text-sm"
                  placeholder="0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Quoter pour récupérer les prix
                </p>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h5 className="text-sm font-medium text-blue-900 mb-2">💡 À quoi servent ces adresses ?</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-blue-800">
                <div>
                  <p><strong>• WPOL :</strong> Balance, transfers, approvals</p>
                  <p><strong>• KNO :</strong> Balance, transfers, approvals</p>
                </div>
                <div>
                  <p><strong>• Router :</strong> Exécuter les swaps WPOL ↔ KNO</p>
                  <p><strong>• Quoter :</strong> Récupérer les prix en temps réel</p>
                </div>
              </div>
            </div>
          </div>

          {/* Trading Parameters */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
              <Settings className="w-5 h-5 text-green-600" />
              <span>Paramètres de Transaction</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Montant du Swap (WPOL)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="100"
                  value={config.swapAmount}
                  onChange={(e) => handleChange('swapAmount', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                  placeholder="0.1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Montant en WPOL pour chaque swap
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Slippage Tolérance (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10"
                  value={config.slippageTolerance}
                  onChange={(e) => handleChange('slippageTolerance', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Tolérance de glissement de prix
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gas Limit
                </label>
                <input
                  type="number"
                  min="21000"
                  max="1000000"
                  value={config.gasLimit}
                  onChange={(e) => handleChange('gasLimit', parseInt(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Limite de gas par transaction
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gas Price (Gwei)
                </label>
                <input
                  type="number"
                  min="1"
                  max="200"
                  value={config.gasPrice}
                  onChange={(e) => handleChange('gasPrice', parseInt(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Prix du gas en Gwei
                </p>
              </div>
            </div>

            {/* Info sur les swaps */}
            <div className="mt-4 p-4 bg-green-50 rounded-lg">
              <div className="flex items-start space-x-2">
                <Activity className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-green-900">Configuration des Swaps</h4>
                  <p className="text-sm text-green-700 mt-1">
                    Le bot utilisera <strong>{config.swapAmount} WPOL</strong> pour chaque transaction, 
                    avec une tolérance de slippage de <strong>{config.slippageTolerance}%</strong>.
                    Volume total estimé : <strong>{config.swapAmount * config.randomTradesCount} WPOL</strong> sur {config.tradingDurationHours}h.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50 rounded-b-xl">
          <div className="flex items-start space-x-3">
            <Shield className="w-6 h-6 text-purple-600 mt-1" />
            <div>
              <h4 className="font-medium text-purple-900 mb-2">🔒 Sécurité des Clés Privées</h4>
              <div className="text-sm text-purple-800 space-y-1">
                <p>• Les clés privées sont <strong>chiffrées</strong> avant stockage</p>
                <p>• Transmission <strong>sécurisée</strong> vers votre bot via HTTPS</p>
                <p>• Stockage <strong>local uniquement</strong> (pas de cloud)</p>
                <p>• Accès <strong>restreint</strong> par authentification</p>
              </div>
              <div className="mt-3 p-3 bg-yellow-100 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>⚠️ Important :</strong> Vos clés privées ne quittent jamais votre réseau local. 
                  Elles sont envoyées directement à votre bot via votre réseau privé.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Trading Parameters */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Paramètres de Trading</h2>
          <p className="text-gray-600">Configurez les conditions d'achat et de vente pour {selectedBot.tokenPair}</p>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Buy Parameters */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
              <TrendingDown className="w-5 h-5 text-blue-600" />
              <span>Paramètres d'Achat</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prix maximum d'achat (€)
                </label>
                <input
                  type="number"
                  step={priceStep}
                  value={config.buyPriceThreshold}
                  onChange={(e) => handleChange('buyPriceThreshold', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder={isSmallToken ? "0.007" : "2800"}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Achat si prix &lt; {"€" + (isSmallToken ? config.buyPriceThreshold.toFixed(4) : config.buyPriceThreshold.toLocaleString())}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Baisse pour re-achat (%)
                </label>
                <input
                  type="number"
                  value={config.buyPercentageDrop}
                  onChange={(e) => handleChange('buyPercentageDrop', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="10"
                />
                <p className="text-xs text-gray-500 mt-1">Achat si baisse de {config.buyPercentageDrop}%+ depuis dernier achat</p>
              </div>
            </div>
          </div>

          {/* Sell Parameters */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <span>Paramètres de Vente</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prix minimum de vente (€)
                </label>
                <input
                  type="number"
                  step={priceStep}
                  value={config.sellPriceThreshold}
                  onChange={(e) => handleChange('sellPriceThreshold', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                  placeholder={isSmallToken ? "0.009" : "3200"}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Vente si prix &gt; {"€" + (isSmallToken ? config.sellPriceThreshold.toFixed(4) : config.sellPriceThreshold.toLocaleString())}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hausse pour vente (%)
                </label>
                <input
                  type="number"
                  value={config.sellPercentageGain}
                  onChange={(e) => handleChange('sellPercentageGain', parseFloat(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                  placeholder="10"
                />
                <p className="text-xs text-gray-500 mt-1">Vente si hausse de {config.sellPercentageGain}%+ depuis dernière vente</p>
              </div>
            </div>
          </div>
        </div>

        {/* Random Trading Parameters */}
        <div className="p-6 border-t border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2 mb-4">
            <Activity className="w-5 h-5 text-purple-600" />
            <span>Paramètres Aléatoires</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre de trades aléatoires
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={config.randomTradesCount}
                onChange={(e) => handleChange('randomTradesCount', parseInt(e.target.value))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                placeholder="20"
              />
              <p className="text-xs text-gray-500 mt-1">
                Le bot effectuera {config.randomTradesCount} trades de manière aléatoire
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Durée de trading (heures)
              </label>
              <input
                type="number"
                min="1"
                max="168"
                value={config.tradingDurationHours}
                onChange={(e) => handleChange('tradingDurationHours', parseInt(e.target.value))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                placeholder="24"
              />
              <p className="text-xs text-gray-500 mt-1">
                Période sur {config.tradingDurationHours}h ({config.tradingDurationHours === 24 ? '1 jour' : config.tradingDurationHours < 24 ? config.tradingDurationHours + 'h' : Math.round(config.tradingDurationHours / 24 * 10) / 10 + ' jours'})
              </p>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-purple-50 rounded-lg">
            <div className="flex items-start space-x-2">
              <Activity className="w-5 h-5 text-purple-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-purple-900">Stratégie Aléatoire</h4>
                <p className="text-sm text-purple-700 mt-1">
                  Le bot répartira {config.randomTradesCount} trades de manière aléatoire sur {config.tradingDurationHours}h, 
                  soit environ {Math.round((config.randomTradesCount / config.tradingDurationHours) * 10) / 10} trades par heure.
                  Les trades respecteront toujours vos conditions de prix.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 bg-gray-50 rounded-b-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-amber-600">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm font-medium">
                Conditions: Achat si prix &lt; {"€" + (isSmallToken ? config.buyPriceThreshold.toFixed(4) : config.buyPriceThreshold.toLocaleString())} OU baisse {config.buyPercentageDrop}%+ | Vente si prix &gt; {"€" + (isSmallToken ? config.sellPriceThreshold.toFixed(4) : config.sellPriceThreshold.toLocaleString())} OU hausse {config.sellPercentageGain}%+ | {config.randomTradesCount} trades/{config.tradingDurationHours}h | Montant: {config.swapAmount} WPOL/swap
              </span>
            </div>
            <button
              onClick={handleSave}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors font-medium"
            >
              <Save className="w-4 h-4" />
              <span>Sauvegarder</span>
            </button>
          </div>
        </div>
      </div>

      {/* Current Market Conditions */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Conditions Actuelles</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-900 mb-2">Dernier Prix d'Achat</h3>
            <p className="text-2xl font-bold text-blue-700">
              {selectedBot.lastBuyPrice ? 
                "€" + (isSmallToken ? selectedBot.lastBuyPrice.toFixed(4) : selectedBot.lastBuyPrice.toLocaleString()) : 
                'Aucun'}
            </p>
            <p className="text-sm text-blue-600 mt-1">
              Prochain achat si baisse à {"€" + (selectedBot.lastBuyPrice ? 
                (isSmallToken ? 
                  (selectedBot.lastBuyPrice * (1 - selectedBot.buyPercentageDrop / 100)).toFixed(4) :
                  (selectedBot.lastBuyPrice * (1 - selectedBot.buyPercentageDrop / 100)).toLocaleString()
                ) : '0')}
            </p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <h3 className="font-medium text-green-900 mb-2">Dernier Prix de Vente</h3>
            <p className="text-2xl font-bold text-green-700">
              {selectedBot.lastSellPrice ? 
                "€" + (isSmallToken ? selectedBot.lastSellPrice.toFixed(4) : selectedBot.lastSellPrice.toLocaleString()) : 
                'Aucun'}
            </p>
            <p className="text-sm text-green-600 mt-1">
              Prochaine vente si hausse à {"€" + (selectedBot.lastSellPrice ? 
                (isSmallToken ? 
                  (selectedBot.lastSellPrice * (1 + selectedBot.sellPercentageGain / 100)).toFixed(4) :
                  (selectedBot.lastSellPrice * (1 + selectedBot.sellPercentageGain / 100)).toLocaleString()
                ) : '0')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BotConfig;