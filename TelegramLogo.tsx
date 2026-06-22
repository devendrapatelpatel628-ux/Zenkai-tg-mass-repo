export default function TelegramLogo({ className = 'w-10 h-10' }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} fill="none">
      <defs>
        <linearGradient id="tg-grad" x1="24" y1="0" x2="24" y2="48" gradientUnits="userSpaceOnUse">
          <stop stopColor="#37AEE2" />
          <stop offset="1" stopColor="#1E96C8" />
        </linearGradient>
      </defs>
      <circle cx="24" cy="24" r="24" fill="url(#tg-grad)" />
      <path
        d="M10.6 23.4c6.2-2.7 10.3-4.5 12.4-5.3 5.9-2.5 7.1-2.9 7.9-2.9.2 0 .5 0 .7.3.2.2.2.4.2.6 0 .2 0 .4-.1.8-.5 5.5-2.7 18.8-3.8 24.9-.5 2.6-1.4 3.4-2.3 3.5-2 .2-3.5-1.3-5.4-2.6-3-1.9-4.7-3.1-7.6-5-3.3-2.1-.2-3.3 1.6-5.2.5-.5 8.8-8 9-8.7 0-.1 0-.3-.1-.4-.2-.1-.4-.1-.5 0-.2.1-3.8 2.4-10.7 7.1-1 .7-2 1-2.8 1-.9 0-2.7-.5-4.1-1-1.6-.5-2.9-.8-2.8-1.7.1-.5.7-.9 2-1.4z"
        fill="white"
      />
    </svg>
  );
}
