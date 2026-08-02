// ==UserScript==
// @name         deltacards Bridge
// @version      0.1.0
// @description  Connects the Undercards web client to a local deltacards engine instance for offline play and testing.
// @author       rashidsh
// @homepageURL  https://github.com/rashidsh/deltacards
// @downloadURL  https://raw.githubusercontent.com/rashidsh/deltacards/main/deltacards/app/websocket/userscripts/deltacards-bridge.user.js
// @updateURL    https://raw.githubusercontent.com/rashidsh/deltacards/main/deltacards/app/websocket/userscripts/deltacards-bridge.user.js
// @match        https://undercards.net/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=undercards.net
// @run-at       document-start
// @grant        none
// @noframes
// ==/UserScript==

(() => {
  'use strict';

  const OriginalWebSocket = window.WebSocket;

  function getLocalGameID() {
    const url = new URL(location.href);

    if (url.pathname !== '/Spectate') return null;

    return 1;  // TODO
  }

  window.WebSocket = new Proxy(OriginalWebSocket, {
    construct(target, args) {
      const wsUrl = new URL(args[0]);
      if (wsUrl.pathname === '/game') {
        const localGameID = getLocalGameID();

        if (localGameID !== null) {
            args[0] = `ws://localhost:8080/game/${localGameID}?player_id=1`;
        }
      }

      return Reflect.construct(target, args);
    }
  });

  /* UnderScript Plugin */

  function sleep(ms = 0) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function waitForUnderScript() {
    const deadline = Date.now() + 10 * 1000;

    while (Date.now() < deadline) {
      try {
        if (underscript && (typeof underscript.plugin === 'function')) {
          return;
        }

        await sleep(100);
      } catch {
        await sleep(100);
      }
    }

    throw new Error("UnderScript API was not available.");
  }

  async function initPlugin() {
    await waitForUnderScript();

    const plugin = underscript.plugin("deltacards Bridge");
    const eventManager = plugin.events;
    const settings = plugin.settings();

    class StartButtonSetting extends underscript.utils.SettingType {
      constructor(name = 'startButton') {
        super(name);
      }

      value(value) {
        return value;
      }

      encode(value) {
        return value;
      }

      default() {
        return undefined;
      }

      element(value, update) {
        return $('<button>', {
          type: 'button',
          class: "btn btn-primary",
          text: "Start",
        }).on('click', () => update('start'));
      }

      labelFirst() {
        return null;
      }
    }

    settings.addType(new StartButtonSetting());

    const startSpectate = settings.add({
      key: 'startSpectate',
      name: "",
      type: `${plugin.name}:startButton`,
      category: "Local game",
      export: false,

      onChange: ((action, oldValue) => {
        if (action !== 'start') return;
        startSpectate.set(undefined);

        location.assign('/Spectate');
      }),
    });

    console.log("deltacards Bridge Plugin: Loaded");
  }

  initPlugin();
})();
