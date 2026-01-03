import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import { 
  Activity, Users, TrendingUp, AlertTriangle, CheckCircle, 
  Zap, Database, GitBranch, RefreshCw, Send
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Color palette
const COLORS = {
  green: '#22c55e',
  red: '#ef4444',
  blue: '#3b82f6',
  purple: '#a855f7',
  yellow: '#eab308',
  gray: '#64748b'
};

function App() {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [abStats, setAbStats] = useState(null);
  const [models, setModels] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    customer_id: 'CUST-' + Math.random().toString(36).substr(2, 9).toUpperCase(),
    tenure_months: 12,
    monthly_charges: 79.99,
    total_charges: 959.88,
    contract_type: 'Month-to-month',
    payment_method: 'Electronic check',
    internet_service: 'Fiber optic',
    has_phone: true,
    has_partner: false,
    has_dependents: false,
    is_senior: false,
    has_online_security: false,
    has_tech_support: false,
    has_streaming: true,
    paperless_billing: true
  });

  // Fetch health and stats on load
  useEffect(() => {
    fetchHealth();
    fetchABStats();
    fetchModels();
    
    const interval = setInterval(() => {
      fetchABStats();
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/health`);
      setHealthStatus(res.data);
    } catch (err) {
      setHealthStatus({ status: 'unhealthy', error: err.message });
    }
  };

  const fetchABStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/ab-stats`);
      setAbStats(res.data);
    } catch (err) {
      console.error('Failed to fetch A/B stats:', err);
    }
  };

  const fetchModels = async () => {
    try {
      const res = await axios.get(`${API_BASE}/models`);
      setModels(res.data);
    } catch (err) {
      console.error('Failed to fetch models:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await axios.post(`${API_BASE}/predict`, formData);
      setPrediction(res.data);
    } catch (err) {
      console.error('Prediction failed:', err);
      setPrediction({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseFloat(value) : value
    }));
  };

  const randomizeCustomer = () => {
    setFormData({
      customer_id: 'CUST-' + Math.random().toString(36).substr(2, 9).toUpperCase(),
      tenure_months: Math.floor(Math.random() * 72) + 1,
      monthly_charges: Math.round((Math.random() * 100 + 20) * 100) / 100,
      total_charges: Math.round((Math.random() * 5000 + 100) * 100) / 100,
      contract_type: ['Month-to-month', 'One year', 'Two year'][Math.floor(Math.random() * 3)],
      payment_method: ['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)'][Math.floor(Math.random() * 4)],
      internet_service: ['DSL', 'Fiber optic', 'No'][Math.floor(Math.random() * 3)],
      has_phone: Math.random() > 0.2,
      has_partner: Math.random() > 0.5,
      has_dependents: Math.random() > 0.7,
      is_senior: Math.random() > 0.8,
      has_online_security: Math.random() > 0.5,
      has_tech_support: Math.random() > 0.5,
      has_streaming: Math.random() > 0.4,
      paperless_billing: Math.random() > 0.4
    });
  };

  const getRiskClass = (risk) => {
    switch (risk) {
      case 'HIGH': return 'risk-high';
      case 'MEDIUM': return 'risk-medium';
      default: return 'risk-low';
    }
  };

  return (
    <div className="min-h-screen p-6 lg:p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold font-display bg-gradient-to-r from-green-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
              Churn Prediction Dashboard
            </h1>
            <p className="text-gray-400 mt-2">MLOps Workshop | Real-time Customer Churn Analysis</p>
          </div>
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${healthStatus?.status === 'healthy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
              {healthStatus?.status === 'healthy' ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
              <span className="text-sm font-medium">{healthStatus?.status || 'checking...'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="stat-card neon-green">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-500/20 rounded-xl">
              <Activity size={24} className="text-green-400" />
            </div>
            <div>
              <div className="stat-value text-green-400">{abStats?.total_requests || 0}</div>
              <div className="stat-label">Total Predictions</div>
            </div>
          </div>
        </div>
        
        <div className="stat-card neon-blue">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/20 rounded-xl">
              <GitBranch size={24} className="text-blue-400" />
            </div>
            <div>
              <div className="stat-value text-blue-400">{abStats?.model_a_requests || 0}</div>
              <div className="stat-label">Model A (Champion)</div>
            </div>
          </div>
        </div>
        
        <div className="stat-card neon-purple">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-500/20 rounded-xl">
              <Zap size={24} className="text-purple-400" />
            </div>
            <div>
              <div className="stat-value text-purple-400">{abStats?.model_b_requests || 0}</div>
              <div className="stat-label">Model B (Challenger)</div>
            </div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-yellow-500/20 rounded-xl">
              <TrendingUp size={24} className="text-yellow-400" />
            </div>
            <div>
              <div className="stat-value text-yellow-400">
                {abStats?.model_a_avg_latency_ms?.toFixed(1) || 0}ms
              </div>
              <div className="stat-label">Avg Latency</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Prediction Form */}
        <div className="lg:col-span-1">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold font-display flex items-center gap-2">
                <Users className="text-green-400" size={24} />
                Customer Data
              </h2>
              <button onClick={randomizeCustomer} className="p-2 hover:bg-dark-700 rounded-lg transition-colors" title="Randomize">
                <RefreshCw size={18} className="text-gray-400" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Customer ID</label>
                <input
                  type="text"
                  name="customer_id"
                  value={formData.customer_id}
                  onChange={handleInputChange}
                  className="input-field"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tenure (months)</label>
                  <input
                    type="number"
                    name="tenure_months"
                    value={formData.tenure_months}
                    onChange={handleInputChange}
                    className="input-field"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Monthly Charges ($)</label>
                  <input
                    type="number"
                    name="monthly_charges"
                    value={formData.monthly_charges}
                    onChange={handleInputChange}
                    className="input-field"
                    step="0.01"
                    min="0"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Total Charges ($)</label>
                <input
                  type="number"
                  name="total_charges"
                  value={formData.total_charges}
                  onChange={handleInputChange}
                  className="input-field"
                  step="0.01"
                  min="0"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Contract Type</label>
                <select
                  name="contract_type"
                  value={formData.contract_type}
                  onChange={handleInputChange}
                  className="input-field"
                >
                  <option value="Month-to-month">Month-to-month</option>
                  <option value="One year">One year</option>
                  <option value="Two year">Two year</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Payment Method</label>
                <select
                  name="payment_method"
                  value={formData.payment_method}
                  onChange={handleInputChange}
                  className="input-field"
                >
                  <option value="Electronic check">Electronic check</option>
                  <option value="Mailed check">Mailed check</option>
                  <option value="Bank transfer (automatic)">Bank transfer (automatic)</option>
                  <option value="Credit card (automatic)">Credit card (automatic)</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Internet Service</label>
                <select
                  name="internet_service"
                  value={formData.internet_service}
                  onChange={handleInputChange}
                  className="input-field"
                >
                  <option value="DSL">DSL</option>
                  <option value="Fiber optic">Fiber optic</option>
                  <option value="No">No Internet</option>
                </select>
              </div>
              
              {/* Checkboxes */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  { name: 'has_phone', label: 'Phone Service' },
                  { name: 'has_partner', label: 'Has Partner' },
                  { name: 'has_dependents', label: 'Has Dependents' },
                  { name: 'is_senior', label: 'Senior Citizen' },
                  { name: 'has_online_security', label: 'Online Security' },
                  { name: 'has_tech_support', label: 'Tech Support' },
                  { name: 'has_streaming', label: 'Streaming' },
                  { name: 'paperless_billing', label: 'Paperless Billing' }
                ].map(({ name, label }) => (
                  <label key={name} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name={name}
                      checked={formData[name]}
                      onChange={handleInputChange}
                      className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-green-500 focus:ring-green-500"
                    />
                    <span className="text-sm text-gray-300">{label}</span>
                  </label>
                ))}
              </div>
              
              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                {loading ? (
                  <>
                    <RefreshCw size={18} className="animate-spin" />
                    Predicting...
                  </>
                ) : (
                  <>
                    <Send size={18} />
                    Predict Churn
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
        
        {/* Prediction Result */}
        <div className="lg:col-span-2 space-y-6">
          {/* Result Card */}
          {prediction && !prediction.error && (
            <div className={`glass-card p-8 ${prediction.churn_prediction ? 'neon-red' : 'neon-green'}`}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold font-display">Prediction Result</h2>
                <span className={`px-4 py-2 rounded-full text-sm font-medium ${getRiskClass(prediction.risk_level)}`}>
                  {prediction.risk_level} RISK
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 bg-dark-800/50 rounded-xl">
                  <div className={`text-5xl font-bold font-display mb-2 ${prediction.churn_prediction ? 'text-red-400' : 'text-green-400'}`}>
                    {(prediction.churn_probability * 100).toFixed(1)}%
                  </div>
                  <div className="text-gray-400">Churn Probability</div>
                </div>
                
                <div className="text-center p-6 bg-dark-800/50 rounded-xl">
                  <div className={`text-3xl font-bold font-display mb-2 ${prediction.churn_prediction ? 'text-red-400' : 'text-green-400'}`}>
                    {prediction.churn_prediction ? 'WILL CHURN' : 'WILL STAY'}
                  </div>
                  <div className="text-gray-400">Prediction</div>
                </div>
                
                <div className="text-center p-6 bg-dark-800/50 rounded-xl">
                  <div className="text-xl font-medium mb-2 text-blue-400">
                    {prediction.model_name?.replace('telco-churn-', '')}
                  </div>
                  <div className="text-gray-400">Model Used (Group {prediction.ab_group})</div>
                  <div className="text-xs text-gray-500 mt-1">{prediction.prediction_time_ms?.toFixed(2)}ms</div>
                </div>
              </div>
            </div>
          )}
          
          {/* A/B Testing Stats */}
          {abStats && (
            <div className="glass-card p-6">
              <h2 className="text-xl font-semibold font-display mb-6 flex items-center gap-2">
                <GitBranch className="text-purple-400" size={24} />
                A/B Testing Statistics
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Traffic Split Chart */}
                <div className="bg-dark-800/50 rounded-xl p-4">
                  <h3 className="text-sm text-gray-400 mb-4 uppercase tracking-wider">Traffic Split</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Model A', value: abStats.model_a_requests || 1, fill: COLORS.blue },
                          { name: 'Model B', value: abStats.model_b_requests || 0, fill: COLORS.purple }
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                      </Pie>
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                        labelStyle={{ color: '#f1f5f9' }}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Latency Comparison */}
                <div className="bg-dark-800/50 rounded-xl p-4">
                  <h3 className="text-sm text-gray-400 mb-4 uppercase tracking-wider">Latency Comparison (ms)</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={[
                      { name: 'Model A', latency: abStats.model_a_avg_latency_ms || 0 },
                      { name: 'Model B', latency: abStats.model_b_avg_latency_ms || 0 }
                    ]}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#64748b" />
                      <YAxis stroke="#64748b" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                        labelStyle={{ color: '#f1f5f9' }}
                      />
                      <Bar dataKey="latency" fill={COLORS.green} radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              
              <div className="mt-4 flex items-center gap-4 text-sm text-gray-400">
                <span>Model A: <span className="text-blue-400">{abStats.model_a_name?.replace('telco-churn-', '')}</span></span>
                <span>|</span>
                <span>Model B: <span className="text-purple-400">{abStats.model_b_name?.replace('telco-churn-', '')}</span></span>
              </div>
            </div>
          )}
          
          {/* Models Info */}
          <div className="glass-card p-6">
            <h2 className="text-xl font-semibold font-display mb-6 flex items-center gap-2">
              <Database className="text-green-400" size={24} />
              Deployed Models
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {models.length > 0 ? models.map((model, idx) => (
                <div key={idx} className="bg-dark-800/50 rounded-xl p-4 border border-dark-700">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-200">{model.model_name?.replace('telco-churn-', '')}</span>
                    <span className={`px-2 py-1 rounded text-xs ${model.stage === 'Production' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                      {model.stage}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">Version: {model.model_version}</div>
                </div>
              )) : (
                <div className="col-span-3 text-center text-gray-400 py-8">
                  No models loaded. Make sure the ML pipeline has been run.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="mt-12 text-center text-gray-500 text-sm">
        <p>MLOps Workshop | Telco Customer Churn Prediction</p>
        <p className="mt-1">Built with FastAPI, MLflow, MinIO, Kubernetes</p>
      </footer>
    </div>
  );
}

export default App;

