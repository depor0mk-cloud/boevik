export interface User {
  clan_id: string | null;
  role: 'leader' | 'member' | null;
  username: string;
  exp: number;
  level: number;
  contribution: number;
  last_work_1?: number;
  last_work_2?: number;
}

export interface Clan {
  name: string;
  tag: string;
  leader_id: string;
  members: string[];
  level: number;
  exp: number;
  gold: number;
  weapons: number;
  hp: number;
  army: {
    count: number;
    strength: number;
    experience: number;
  };
  rockets: {
    ballistics: number;
    nuclear: number;
  };
  factories: Record<string, Factory>;
  war?: {
    target_id: string;
    start_time: number;
    status: 'active' | 'truce';
  };
}

export interface Factory {
  type: 'finance' | 'weapon';
  level: number;
  last_production: number;
}

export interface Settings {
  bot_disabled: boolean;
  test_mode: boolean;
  sleep_mode: string | null;
  prices: {
    factory_finance: number;
    factory_weapon: number;
    production_create: number;
    production_upgrade: number;
  };
}
