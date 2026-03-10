/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';

export default function App() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="text-5xl font-bold tracking-tight mb-2">BOEVIK BOT</h1>
          <p className="text-zinc-400">Clan War & Economy Telegram Bot</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
              Статус Системы
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">Бот:</span>
                <span className="text-emerald-400">Активен</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">База данных:</span>
                <span className="text-emerald-400">Подключено</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">Версия:</span>
                <span>1.0.0</span>
              </div>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl">
            <h2 className="text-xl font-semibold mb-4">Быстрые ссылки</h2>
            <div className="space-y-2">
              <a 
                href="https://t.me/boevik_clan_bot" 
                target="_blank" 
                rel="noopener noreferrer"
                className="block w-full text-center bg-zinc-100 text-zinc-950 py-2 rounded-xl font-medium hover:bg-zinc-200 transition-colors"
              >
                Открыть в Telegram
              </a>
              <p className="text-xs text-zinc-500 text-center mt-2">
                Используйте /start для начала игры
              </p>
            </div>
          </div>
        </div>

        <section className="mt-12">
          <h2 className="text-2xl font-bold mb-6">Основные команды</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { cmd: '/start', desc: 'Начать игру' },
              { cmd: '/создать клан', desc: 'Создать новый клан' },
              { cmd: '/работа', desc: 'Заработать золото' },
              { cmd: '/завод', desc: 'Управление заводами' },
              { cmd: '/война', desc: 'Объявить войну' },
              { cmd: '/разработка', desc: 'Ракетная программа' },
            ].map((item) => (
              <div key={item.cmd} className="bg-zinc-900/50 border border-zinc-800/50 p-4 rounded-xl">
                <code className="text-emerald-400 font-mono text-sm">{item.cmd}</code>
                <p className="text-xs text-zinc-500 mt-1">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
