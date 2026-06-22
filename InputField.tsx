import { type ReactNode } from 'react';

interface InputFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  icon?: ReactNode;
  disabled?: boolean;
  maxLength?: number;
}

export default function InputField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  icon,
  disabled = false,
  maxLength,
}: InputFieldProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-slate-300 pl-1">{label}</label>
      <div className="relative group">
        {icon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-sky-400 transition-colors">
            {icon}
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          maxLength={maxLength}
          className={`w-full ${icon ? 'pl-12' : 'pl-4'} pr-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-sky-500/50 focus:ring-2 focus:ring-sky-500/20 transition-all duration-300 disabled:opacity-50 text-sm`}
        />
      </div>
    </div>
  );
}
