import { motion } from 'framer-motion';
import { LoginStep } from '../types';

const steps: { key: LoginStep; label: string }[] = [
  { key: 'credentials', label: 'Credentials' },
  { key: 'otp', label: 'OTP Code' },
  { key: 'two_fa', label: '2FA' },
  { key: 'success', label: 'Done' },
];

export default function StepIndicator({ currentStep }: { currentStep: LoginStep }) {
  const currentIndex = steps.findIndex((s) => s.key === currentStep);

  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {steps.map((step, i) => {
        const isActive = i === currentIndex;
        const isCompleted = i < currentIndex;

        return (
          <div key={step.key} className="flex items-center gap-2">
            <div className="flex flex-col items-center gap-1">
              <motion.div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-500 ${
                  isCompleted
                    ? 'bg-emerald-500 text-white'
                    : isActive
                      ? 'bg-sky-500 text-white ring-4 ring-sky-500/30'
                      : 'bg-white/10 text-slate-500'
                }`}
                animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                {isCompleted ? '✓' : i + 1}
              </motion.div>
              <span
                className={`text-[10px] font-medium ${
                  isActive ? 'text-sky-400' : isCompleted ? 'text-emerald-400' : 'text-slate-600'
                }`}
              >
                {step.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={`w-8 h-0.5 mb-4 rounded-full transition-all duration-500 ${
                  isCompleted ? 'bg-emerald-500' : 'bg-white/10'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
