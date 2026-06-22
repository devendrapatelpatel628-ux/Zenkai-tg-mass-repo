import { motion } from 'framer-motion';

interface GlowButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'danger' | 'ghost';
  type?: 'button' | 'submit';
  className?: string;
}

export default function GlowButton({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
  type = 'button',
  className = '',
}: GlowButtonProps) {
  const base =
    'relative px-6 py-3 rounded-xl font-semibold text-sm tracking-wide transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary:
      'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 hover:scale-[1.02]',
    danger:
      'bg-gradient-to-r from-red-500 to-rose-600 text-white shadow-lg shadow-red-500/30 hover:shadow-red-500/50 hover:scale-[1.02]',
    ghost:
      'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 hover:border-white/20',
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className}`}
      whileTap={{ scale: 0.97 }}
    >
      {children}
    </motion.button>
  );
}
