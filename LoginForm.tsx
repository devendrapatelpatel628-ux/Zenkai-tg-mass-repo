import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Phone,
  Key,
  Hash,
  Shield,
  Loader2,
  ArrowLeft,
  CheckCircle2,
  Sparkles,
  AlertTriangle,
  Wifi,
  WifiOff,
  Smartphone,
  Globe,
  Cpu,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import { LoginState, LoginStep } from '../types';
import { api, FingerprintInfo, ProxyInfo } from '../api';
import InputField from './InputField';
import OtpInput from './OtpInput';
import GlowButton from './GlowButton';
import StepIndicator from './StepIndicator';
import TelegramLogo from './TelegramLogo';

interface LoginFormProps {
  onSuccess: () => void;
  onBack: () => void;
}

const slideVariants = {
  enter: (direction: number) => ({ x: direction > 0 ? 300 : -300, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (direction: number) => ({ x: direction > 0 ? -300 : 300, opacity: 0 }),
};

export default function LoginForm({ onSuccess, onBack }: LoginFormProps) {
  const [state, setState] = useState<LoginState>({
    step: 'credentials',
    phone: '',
    apiId: '',
    apiHash: '',
    otp: '',
    twoFaPassword: '',
    isLoading: false,
    error: '',
  });
  const [direction, setDirection] = useState(1);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [useProxy, setUseProxy] = useState(true);
  const [fingerprint, setFingerprint] = useState<FingerprintInfo | null>(null);
  const [proxyUsed, setProxyUsed] = useState<ProxyInfo | null>(null);

  const update = (partial: Partial<LoginState>) => setState((prev) => ({ ...prev, ...partial }));

  const goToStep = (step: LoginStep, dir: number = 1) => {
    setDirection(dir);
    update({ step, error: '' });
  };

  const checkBackend = async () => {
    const online = await api.healthCheck();
    setBackendOnline(online);
    return online;
  };

  const handleCredentialsSubmit = async () => {
    if (!state.phone || !state.apiId || !state.apiHash) {
      update({ error: 'Please fill in all fields' });
      return;
    }

    const phoneClean = state.phone.replace(/\s/g, '');
    if (!/^\+?\d{7,15}$/.test(phoneClean)) {
      update({ error: 'Invalid phone number format. Use format: +1234567890' });
      return;
    }

    update({ isLoading: true, error: '' });

    // Check if backend is online
    const online = await checkBackend();
    if (!online) {
      update({
        isLoading: false,
        error: 'Backend server is offline. Please start the Python backend first.',
      });
      return;
    }

    // Send code request with proxy option
    const result = await api.sendCode(state.phone, state.apiId, state.apiHash, useProxy);

    update({ isLoading: false });

    if (!result.success) {
      update({ error: result.error || 'Failed to send code' });
      return;
    }

    // Store fingerprint and proxy info
    if (result.data?.fingerprint) {
      setFingerprint(result.data.fingerprint);
    }
    if (result.data?.proxy) {
      setProxyUsed(result.data.proxy);
    }

    // Check if already authorized
    if (result.data?.already_authorized) {
      goToStep('success');
      return;
    }

    goToStep('otp');
  };

  const handleOtpSubmit = async () => {
    if (state.otp.length < 5) {
      update({ error: 'Please enter the full OTP code' });
      return;
    }

    update({ isLoading: true, error: '' });

    const result = await api.verifyCode(state.phone, state.otp);

    update({ isLoading: false });

    if (!result.success) {
      update({ error: result.error || 'Invalid code' });
      return;
    }

    if (result.data?.needs_2fa) {
      goToStep('two_fa');
      return;
    }

    goToStep('success');
  };

  const handleTwoFaSubmit = async () => {
    if (!state.twoFaPassword) {
      update({ error: 'Please enter your 2FA password' });
      return;
    }

    update({ isLoading: true, error: '' });

    const result = await api.verify2FA(state.phone, state.twoFaPassword);

    update({ isLoading: false });

    if (!result.success) {
      update({ error: result.error || 'Invalid password' });
      return;
    }

    goToStep('success');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/5 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative w-full max-w-md"
      >
        {/* Glass card */}
        <div className="relative bg-slate-900/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 shadow-2xl shadow-black/40">
          {/* Top glow */}
          <div className="absolute -top-px left-10 right-10 h-px bg-gradient-to-r from-transparent via-sky-500/50 to-transparent" />

          {/* Backend status indicator */}
          {backendOnline !== null && (
            <div
              className={`absolute top-4 right-4 flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${
                backendOnline
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : 'bg-red-500/10 text-red-400'
              }`}
            >
              {backendOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
              {backendOnline ? 'Connected' : 'Offline'}
            </div>
          )}

          {/* Header */}
          <div className="text-center mb-6">
            <div className="flex justify-center mb-4">
              <div className="relative">
                <TelegramLogo className="w-16 h-16" />
                <div className="absolute -inset-2 bg-sky-500/20 rounded-full blur-xl" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">
              {state.step === 'success' ? 'Account Added! 🎉' : 'Login Account'}
            </h1>
            <p className="text-sm text-slate-400">
              {state.step === 'credentials' && 'Enter your Telegram API credentials'}
              {state.step === 'otp' && 'Enter the code sent to your Telegram'}
              {state.step === 'two_fa' && 'Enter your two-factor authentication password'}
              {state.step === 'success' && 'Your account has been successfully added'}
            </p>
          </div>

          {state.step !== 'success' && <StepIndicator currentStep={state.step} />}

          {/* Fingerprint & Proxy Info (shown during OTP/2FA steps) */}
          {(state.step === 'otp' || state.step === 'two_fa') && (fingerprint || proxyUsed) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl space-y-2"
            >
              {fingerprint && (
                <div className="flex items-center gap-2 text-xs text-purple-300">
                  <Smartphone size={12} />
                  <span>{fingerprint.device}</span>
                  <span className="text-purple-500">•</span>
                  <Cpu size={12} />
                  <span>{fingerprint.app}</span>
                </div>
              )}
              {proxyUsed && (
                <div className="flex items-center gap-2 text-xs text-sky-300">
                  <Globe size={12} />
                  <span>
                    {proxyUsed.host}:{proxyUsed.port}
                  </span>
                  <span className="px-1.5 py-0.5 bg-sky-500/20 rounded text-[10px]">
                    {proxyUsed.type.toUpperCase()}
                  </span>
                  {proxyUsed.country && <span>({proxyUsed.country})</span>}
                </div>
              )}
            </motion.div>
          )}

          {/* Error message */}
          <AnimatePresence>
            {state.error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm flex items-start gap-2"
              >
                <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
                <span>{state.error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Form steps */}
          <AnimatePresence mode="wait" custom={direction}>
            {state.step === 'credentials' && (
              <motion.div
                key="credentials"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                <InputField
                  label="Phone Number"
                  value={state.phone}
                  onChange={(v) => update({ phone: v, error: '' })}
                  placeholder="+1234567890"
                  type="tel"
                  icon={<Phone size={18} />}
                />
                <InputField
                  label="API ID"
                  value={state.apiId}
                  onChange={(v) => update({ apiId: v, error: '' })}
                  placeholder="Enter your API ID (numbers only)"
                  icon={<Hash size={18} />}
                />
                <InputField
                  label="API Hash"
                  value={state.apiHash}
                  onChange={(v) => update({ apiHash: v, error: '' })}
                  placeholder="Enter your API Hash"
                  icon={<Key size={18} />}
                />

                {/* Proxy Toggle */}
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                  <div className="flex items-center gap-2">
                    <Globe size={16} className="text-purple-400" />
                    <span className="text-sm text-slate-300">Use Proxy</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setUseProxy(!useProxy)}
                    className="cursor-pointer"
                  >
                    {useProxy ? (
                      <ToggleRight size={28} className="text-emerald-400" />
                    ) : (
                      <ToggleLeft size={28} className="text-slate-500" />
                    )}
                  </button>
                </div>

                <div className="pt-2 space-y-3">
                  <GlowButton
                    onClick={handleCredentialsSubmit}
                    disabled={state.isLoading}
                    className="w-full"
                  >
                    {state.isLoading ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        Connecting...
                      </>
                    ) : (
                      <>
                        Send OTP Code
                        <Sparkles size={16} />
                      </>
                    )}
                  </GlowButton>
                  <GlowButton onClick={onBack} variant="ghost" className="w-full">
                    <ArrowLeft size={16} />
                    Back to Dashboard
                  </GlowButton>
                </div>
              </motion.div>
            )}

            {state.step === 'otp' && (
              <motion.div
                key="otp"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                <div className="text-center">
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-sky-500/10 border border-sky-500/20 rounded-full text-sky-400 text-sm mb-4">
                    <Phone size={14} />
                    Code sent to {state.phone}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    Check your Telegram app for the login code
                  </p>
                </div>

                <OtpInput value={state.otp} onChange={(v) => update({ otp: v, error: '' })} />

                <div className="pt-2 space-y-3">
                  <GlowButton
                    onClick={handleOtpSubmit}
                    disabled={state.isLoading}
                    className="w-full"
                  >
                    {state.isLoading ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        Verifying...
                      </>
                    ) : (
                      'Verify Code'
                    )}
                  </GlowButton>
                  <GlowButton
                    onClick={() => goToStep('credentials', -1)}
                    variant="ghost"
                    className="w-full"
                  >
                    <ArrowLeft size={16} />
                    Go Back
                  </GlowButton>
                </div>
              </motion.div>
            )}

            {state.step === 'two_fa' && (
              <motion.div
                key="two_fa"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                <div className="text-center">
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-400 text-sm mb-4">
                    <Shield size={14} />
                    Two-Factor Authentication Required
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    Enter the cloud password you set up in Telegram
                  </p>
                </div>

                <InputField
                  label="2FA Password"
                  value={state.twoFaPassword}
                  onChange={(v) => update({ twoFaPassword: v, error: '' })}
                  placeholder="Enter your cloud password"
                  type="password"
                  icon={<Shield size={18} />}
                />

                <div className="pt-2 space-y-3">
                  <GlowButton
                    onClick={handleTwoFaSubmit}
                    disabled={state.isLoading}
                    className="w-full"
                  >
                    {state.isLoading ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        Authenticating...
                      </>
                    ) : (
                      'Submit Password'
                    )}
                  </GlowButton>
                  <GlowButton
                    onClick={() => goToStep('otp', -1)}
                    variant="ghost"
                    className="w-full"
                  >
                    <ArrowLeft size={16} />
                    Go Back
                  </GlowButton>
                </div>
              </motion.div>
            )}

            {state.step === 'success' && (
              <motion.div
                key="success"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
                className="space-y-6 text-center"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
                  className="flex justify-center"
                >
                  <div className="relative">
                    <CheckCircle2 size={80} className="text-emerald-400" />
                    <div className="absolute -inset-4 bg-emerald-500/20 rounded-full blur-2xl" />
                  </div>
                </motion.div>

                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">Successfully Logged In!</h3>
                  <p className="text-sm text-slate-400">
                    Your Telegram account ({state.phone}) has been added to the manager.
                  </p>
                </div>

                {/* Show fingerprint on success */}
                {fingerprint && (
                  <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-xl text-left">
                    <p className="text-xs text-purple-400 font-semibold mb-2">Device Fingerprint:</p>
                    <div className="space-y-1 text-xs text-slate-300">
                      <p>📱 {fingerprint.device}</p>
                      <p>📲 {fingerprint.app} {fingerprint.app_version}</p>
                      <p>🔧 {fingerprint.system}</p>
                    </div>
                  </div>
                )}

                <GlowButton onClick={onSuccess} className="w-full">
                  Go to Dashboard
                </GlowButton>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Footer hint */}
          {state.step === 'credentials' && (
            <div className="mt-6 space-y-2">
              <p className="text-xs text-slate-500 text-center">
                Get your API credentials from{' '}
                <a
                  href="https://my.telegram.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sky-400 hover:underline"
                >
                  my.telegram.org
                </a>
              </p>
              <div className="flex items-center justify-center gap-2 text-xs text-purple-400/80">
                <Smartphone size={12} />
                <span>Auto fingerprinting enabled</span>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
