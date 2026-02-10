export function initTelegram() {
    if (!window.Telegram || !window.Telegram.WebApp) {
      console.error("Telegram WebApp not available");
      return null;
    }
  
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
  
    return tg;
  }
  