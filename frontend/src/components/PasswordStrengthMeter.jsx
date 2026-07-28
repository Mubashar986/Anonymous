import React from 'react';
import { Check, X } from 'lucide-react';

export default function PasswordStrengthMeter({ password = '' }) {
  const checks = [
    { label: 'At least 8 characters', valid: password.length >= 8 },
    { label: 'One uppercase letter', valid: /[A-Z]/.test(password) },
    { label: 'One lowercase letter', valid: /[a-z]/.test(password) },
    { label: 'One digit', valid: /\d/.test(password) },
    { label: 'One special character', valid: /[!@#$%^&*(),.?":{}|<>]/.test(password) },
  ];
  const passed = checks.filter((c) => c.valid).length;
  const pct = (passed / checks.length) * 100;
  const barColor = passed <= 2 ? 'bg-crimson' : passed <= 4 ? 'bg-gold' : 'bg-sage';

  return (
    <div className="mt-2.5 space-y-1.5">
      <div className="flex justify-between items-center text-[11px] text-cream-dim font-medium">
        <span>Password strength</span>
        <span>{passed} of 5</span>
      </div>
      <div className="h-1 w-full bg-canvas-elevated rounded-full overflow-hidden">
        <div className={`h-full transition-all duration-300 ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="grid grid-cols-1 gap-1 pt-0.5">
        {checks.map((check, i) => (
          <div key={i} className="flex items-center gap-1.5 text-[11px]">
            {check.valid ? <Check className="w-3 h-3 text-sage shrink-0" /> : <X className="w-3 h-3 text-cream-faint shrink-0" />}
            <span className={check.valid ? 'text-cream-muted font-medium' : 'text-cream-faint'}>{check.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
