import { useState } from 'react';
import { motion } from 'framer-motion';
import { login } from '../services/api';
import logoImg from '../assets/logo.jpg';
import { Shield, Mail, Lock, Eye, EyeOff } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAutofill = () => {
    setEmail('admin@kovirx.com');
    setPassword('KovirX@2024!');
  };

  return (
    <div className="relative w-screen h-screen bg-bg flex items-center justify-center overflow-hidden font-sans">
      {/* Background Cyber Grid */}
      <div 
        className="absolute inset-0 z-0 pointer-events-none opacity-30" 
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 212, 255, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 212, 255, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
          backgroundPosition: 'center',
        }} 
      />

      {/* Animated Ambient Glows */}
      <motion.div 
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        className="absolute top-[10%] left-[20%] w-[500px] h-[500px] bg-purple/10 rounded-full blur-[80px] z-0 pointer-events-none"
      />
      <motion.div 
        animate={{
          scale: [1.2, 1, 1.2],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        className="absolute bottom-[10%] right-[20%] w-[600px] h-[600px] bg-cyan/5 rounded-full blur-[100px] z-0 pointer-events-none"
      />

      {/* Login Box Container */}
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-full max-w-[440px] px-8 py-10 rounded-2xl bg-panel/75 border border-panelBorder/80 shadow-2xl backdrop-blur-xl z-10 flex flex-col items-center"
      >
        {/* Logo Zone */}
        <div className="relative mb-6">
          <div className="absolute -inset-4 rounded-full bg-cyan/15 blur-lg pointer-events-none" />
          <img
            src={logoImg}
            alt="KovirX Logo"
            className="h-[76px] w-[76px] object-contain block filter drop-shadow-[0_0_15px_rgba(0,212,255,0.6)]"
          />
        </div>

        <h1 className="font-orbitron text-2xl font-black text-white tracking-[4px] mb-1 bg-gradient-to-r from-white to-cyan bg-clip-text text-transparent">
          KOVIRX
        </h1>
        <p className="font-orbitron text-[9px] tracking-[2px] text-textDim mb-8 text-center">
          SECURE OPERATIONS GATEWAY
        </p>

        {error && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full p-3 rounded-lg bg-red/10 border border-red text-red text-xs mb-6 font-medium"
          >
            <strong>ACCESS DENIED:</strong> {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="w-full space-y-5">
          <div>
            <label className="block font-orbitron text-[9px] text-textDim tracking-wider mb-2 font-semibold">
              ANALYST EMAIL
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-textDim">
                <Mail className="h-4 w-4" />
              </span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@kovirx.com"
                disabled={loading}
                className="w-full pl-10 pr-4 py-3 rounded-lg bg-bg/80 border border-panelBorder text-white text-sm outline-none transition-all duration-300 focus:border-cyan focus:ring-1 focus:ring-cyan/25"
              />
            </div>
          </div>

          <div>
            <label className="block font-orbitron text-[9px] text-textDim tracking-wider mb-2 font-semibold">
              SECURE KEY / PASSWORD
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-textDim">
                <Lock className="h-4 w-4" />
              </span>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                disabled={loading}
                className="w-full pl-10 pr-10 py-3 rounded-lg bg-bg/80 border border-panelBorder text-white text-sm outline-none transition-all duration-300 focus:border-cyan focus:ring-1 focus:ring-cyan/25"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-textDim hover:text-cyan transition-colors"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={loading}
            className={`w-full py-3.5 rounded-lg text-white font-orbitron text-[11px] font-bold tracking-[3px] shadow-lg transition-all duration-300 ${
              loading 
                ? 'bg-panelBorder/50 cursor-default text-textDim shadow-none' 
                : 'bg-gradient-to-r from-purple to-cyan hover:shadow-cyan/40 hover:brightness-110 shadow-purple/30'
            }`}
          >
            {loading ? 'VERIFYING CREDENTIALS...' : 'AUTHENTICATE'}
          </motion.button>
        </form>

        {/* Quick autofill helper */}
        <div className="mt-8 w-full p-4 rounded-xl border border-dashed border-purple/20 bg-purple/5 flex flex-col items-center gap-3">
          <span className="text-[10px] text-textDim flex items-center gap-1.5 font-orbitron tracking-wider">
            <Shield className="h-3 w-3 text-purple" />
            Seed Admin Credential Helper
          </span>
          <button
            type="button"
            onClick={handleAutofill}
            className="border border-cyan/60 rounded-md text-cyan text-[10px] py-1.5 px-3 hover:bg-cyan/10 transition-colors font-orbitron tracking-wider font-semibold"
          >
            AUTO-FILL ADMIN CREDENTIALS
          </button>
        </div>
      </motion.div>
    </div>
  );
}
