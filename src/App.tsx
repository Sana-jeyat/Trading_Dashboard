import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import BotConfig from './components/BotConfig';
import TransactionHistory from './components/TransactionHistory';
import BotManager from './components/BotManager';
import { BotProvider } from './context/BotContext';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'config':
        return <BotConfig />;
      case 'history':
        return <TransactionHistory />;
      case 'bots':
        return <BotManager />;
      default:
        return <Dashboard />;
    }
  };
  

  return (
    <BotProvider>
      <div className="flex h-screen bg-gray-50">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="flex-1 overflow-auto">
          {renderContent()}
        </main>
      </div>
    </BotProvider>
  );
}

export default App;