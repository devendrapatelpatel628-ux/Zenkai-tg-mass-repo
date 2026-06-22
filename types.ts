export type LoginStep = 'credentials' | 'otp' | 'two_fa' | 'success';

export interface TelegramAccount {
  id: string;
  phone: string;
  firstName: string;
  lastName: string;
  username: string;
  apiId: string;
  apiHash: string;
  status: 'online' | 'offline' | 'recently';
  avatar?: string;
  loginDate: string;
}

export interface LoginState {
  step: LoginStep;
  phone: string;
  apiId: string;
  apiHash: string;
  otp: string;
  twoFaPassword: string;
  isLoading: boolean;
  error: string;
}
