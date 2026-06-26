import { useState } from 'react';
import { login } from '../services/api';
import logoImg from '../assets/logo.jpg';

const COLORS = {
  bg: "#060B18",
  panel: "rgba(12, 20, 38, 0.75)",
  panelBorder: "rgba(30, 41, 59, 0.8)",
  text: "#C5D0E6",
  textDim: "#5A7090",
  cyan: "#00D4FF",
  amber: "#FFB400",
  red: "#FF355E",
  purple: "#9B59FF",
};

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
    <div style={{
      position: 'relative',
      width: '100vw',
      height: '100vh',
      background: COLORS.bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden',
      fontFamily: "'Inter', sans-serif"
    }}>
      {/* Background Cyber Grid */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `
          linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px',
        backgroundPosition: 'center',
        zIndex: 1,
      }} />

      {/* Ambient Glows */}
      <div style={{
        position: 'absolute',
        top: '20%',
        left: '30%',
        width: '500px',
        height: '500px',
        background: `radial-gradient(circle, rgba(155, 89, 255, 0.1) 0%, transparent 70%)`,
        filter: 'blur(40px)',
        zIndex: 1,
      }} />
      <div style={{
        position: 'absolute',
        bottom: '15%',
        right: '25%',
        width: '600px',
        height: '600px',
        background: `radial-gradient(circle, rgba(0, 212, 255, 0.08) 0%, transparent 70%)`,
        filter: 'blur(50px)',
        zIndex: 1,
      }} />

      {/* Login Box */}
      <div style={{
        width: '100%',
        maxWidth: '440px',
        padding: '40px',
        borderRadius: '16px',
        background: COLORS.panel,
        border: `1px solid ${COLORS.panelBorder}`,
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.5), 0 0 1px 1px rgba(0, 212, 255, 0.1)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        zIndex: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        animation: 'slideIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) both',
      }}>
        {/* Logo Zone */}
        <div style={{ position: 'relative', marginBottom: '24px' }}>
          <div style={{
            position: 'absolute',
            inset: -12,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(0, 212, 255, 0.2) 0%, transparent 70%)',
            pointerEvents: 'none'
          }} />
          <img
            src={logoImg}
            alt="KovirX Logo"
            style={{
              height: '70px',
              width: '70px',
              objectFit: 'contain',
              display: 'block',
              filter: 'drop-shadow(0 0 12px #00D4FF88)'
            }}
          />
        </div>

        <h1 style={{
          fontFamily: "'Orbitron', sans-serif",
          fontSize: '22px',
          fontWeight: 900,
          color: '#FFFFFF',
          letterSpacing: '4px',
          marginBottom: '6px',
          textAlign: 'center',
          background: 'linear-gradient(90deg, #FFFFFF, #00D4FF)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          KOVIRX
        </h1>
        <p style={{
          fontFamily: "'Orbitron', sans-serif",
          fontSize: '9px',
          letterSpacing: '2px',
          color: COLORS.textDim,
          marginBottom: '32px',
          textAlign: 'center',
        }}>
          SECURE OPERATIONS GATEWAY
        </p>

        {error && (
          <div style={{
            width: '100%',
            padding: '10px 14px',
            borderRadius: '6px',
            backgroundColor: `${COLORS.red}15`,
            border: `1px solid ${COLORS.red}`,
            color: COLORS.red,
            fontSize: '12px',
            marginBottom: '20px',
            lineHeight: 1.4,
          }}>
            <strong>ACCESS DENIED:</strong> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              fontFamily: "'Orbitron', sans-serif",
              fontSize: '9px',
              color: COLORS.textDim,
              letterSpacing: '1px',
              marginBottom: '8px',
            }}>
              ANALYST EMAIL
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@kovirx.com"
              disabled={loading}
              style={{
                width: '100%',
                padding: '12px 16px',
                borderRadius: '8px',
                backgroundColor: 'rgba(6, 11, 24, 0.8)',
                border: `1px solid ${COLORS.panelBorder}`,
                color: '#FFFFFF',
                fontSize: '14px',
                outline: 'none',
                transition: 'all 0.3s ease',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = COLORS.cyan;
                e.target.style.boxShadow = `0 0 10px ${COLORS.cyan}25`;
              }}
              onBlur={(e) => {
                e.target.style.borderColor = COLORS.panelBorder;
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontFamily: "'Orbitron', sans-serif",
              fontSize: '9px',
              color: COLORS.textDim,
              letterSpacing: '1px',
              marginBottom: '8px',
            }}>
              SECURE KEY / PASSWORD
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              disabled={loading}
              style={{
                width: '100%',
                padding: '12px 16px',
                borderRadius: '8px',
                backgroundColor: 'rgba(6, 11, 24, 0.8)',
                border: `1px solid ${COLORS.panelBorder}`,
                color: '#FFFFFF',
                fontSize: '14px',
                outline: 'none',
                transition: 'all 0.3s ease',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = COLORS.cyan;
                e.target.style.boxShadow = `0 0 10px ${COLORS.cyan}25`;
              }}
              onBlur={(e) => {
                e.target.style.borderColor = COLORS.panelBorder;
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: '8px',
              background: loading ? 'rgba(30, 41, 59, 0.5)' : `linear-gradient(90deg, ${COLORS.purple}, ${COLORS.cyan})`,
              border: 'none',
              color: '#FFFFFF',
              fontFamily: "'Orbitron', sans-serif",
              fontSize: '11px',
              fontWeight: '700',
              letterSpacing: '3px',
              cursor: loading ? 'default' : 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: loading ? 'none' : `0 0 20px ${COLORS.purple}55`,
            }}
            onMouseOver={(e) => {
              if (!loading) {
                e.target.style.filter = 'brightness(1.1)';
                e.target.style.boxShadow = `0 0 25px ${COLORS.cyan}77`;
              }
            }}
            onMouseOut={(e) => {
              if (!loading) {
                e.target.style.filter = 'none';
                e.target.style.boxShadow = `0 0 20px ${COLORS.purple}55`;
              }
            }}
          >
            {loading ? 'VERIFYING CREDENTIALS...' : 'AUTHENTICATE'}
          </button>
        </form>

        {/* Quick autofill helper */}
        <div style={{
          marginTop: '32px',
          width: '100%',
          padding: '12px 14px',
          borderRadius: '8px',
          border: `1px dashed ${COLORS.purple}44`,
          background: 'rgba(155, 89, 255, 0.03)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px',
        }}>
          <span style={{ fontSize: '10px', color: COLORS.textDim, textAlign: 'center' }}>
            Seed Admin Credential Helper
          </span>
          <button
            onClick={handleAutofill}
            style={{
              background: 'none',
              border: `1px solid ${COLORS.cyan}77`,
              borderRadius: '4px',
              color: COLORS.cyan,
              fontSize: '9px',
              padding: '4px 10px',
              cursor: 'pointer',
              fontFamily: "'Orbitron', sans-serif",
              letterSpacing: '1px',
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => {
              e.target.style.background = `${COLORS.cyan}15`;
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'none';
            }}
          >
            AUTO-FILL ADMIN CREDENTIALS
          </button>
        </div>
      </div>
    </div>
  );
}
