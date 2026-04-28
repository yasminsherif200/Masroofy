/**
 * ui.js — UI Component Classes
 *
 * Component architecture with clean lifecycle and event handling.
 * SOLID:
 *   S — each component manages one piece of UI.
 *   O — extend BaseComponent; don't modify it.
 *   L — all components satisfy BaseComponent contract.
 *   I — UI events segregated; components only subscribe to what they need.
 *   D — components receive DOM elements, not selectors (DI via constructor).
 */

import { Bus, AppEvents } from './core.js';
import { AppContainer }   from './core.js';

/* ============================================================
   BASE COMPONENT
   ============================================================ */

/**
 * BaseComponent — lifecycle contract for all UI components.
 * @abstract
 */
class BaseComponent {
  #el;
  #listeners = [];
  #mounted   = false;

  /** @param {HTMLElement|string} elOrSelector */
  constructor(elOrSelector) {
    this.#el = typeof elOrSelector === 'string'
      ? document.querySelector(elOrSelector)
      : elOrSelector;
  }

  get el()       { return this.#el; }
  get isMounted(){ return this.#mounted; }

  /**
   * Mount — attach to DOM and bind events.
   * Subclasses override render() and bindEvents().
   */
  mount() {
    if (!this.#el) return this;
    this.render();
    this.bindEvents();
    this.#mounted = true;
    return this;
  }

  /** Override to inject HTML into this.el */
  render() {}

  /** Override to attach event listeners (use this._on for auto-cleanup) */
  bindEvents() {}

  /**
   * Register a DOM event listener — auto-removed on destroy().
   * @param {EventTarget} target
   * @param {string} event
   * @param {Function} handler
   * @param {AddEventListenerOptions} [opts]
   */
  _on(target, event, handler, opts) {
    target.addEventListener(event, handler, opts);
    this.#listeners.push({ target, event, handler, opts });
  }

  /**
   * Register a Bus listener — auto-removed on destroy().
   * @param {string} event
   * @param {Function} handler
   */
  _bus(event, handler) {
    const unsub = Bus.on(event, handler);
    this.#listeners.push({ unsub });
  }

  /**
   * Update a child element's text safely.
   * @param {string} selector
   * @param {string} text
   */
  _setText(selector, text) {
    const el = this.#el?.querySelector(selector);
    if (el) el.textContent = text;
  }

  /**
   * Show/hide a child element.
   * @param {string} selector
   * @param {boolean} visible
   */
  _toggle(selector, visible) {
    const el = this.#el?.querySelector(selector);
    if (el) el.hidden = !visible;
  }

  /** Tear down: remove all event listeners, empty el. */
  destroy() {
    this.#listeners.forEach(({ target, event, handler, opts, unsub }) => {
      if (unsub) {
        unsub();
      } else {
        target?.removeEventListener(event, handler, opts);
      }
    });
    this.#listeners = [];
    this.#mounted   = false;
  }
}

/* ============================================================
   SIDEBAR COMPONENT
   ============================================================ */

class SidebarComponent extends BaseComponent {
  #collapsed = false;
  #authService;
  #activePage;

  /**
   * @param {HTMLElement} el
   * @param {AuthService} authService
   * @param {string} activePage — e.g. 'dashboard'
   */
  constructor(el, authService, activePage) {
    super(el);
    this.#authService = authService;
    this.#activePage  = activePage;
    // Restore collapse preference
    this.#collapsed = localStorage.getItem('sidebar_collapsed') === 'true';
  }

  render() {
    const user = this.#authService.currentUser;
    this.el.innerHTML = `
      <div class="sidebar__header">
        <div class="sidebar__logo">X</div>
        <span class="sidebar__brand">Xpense</span>
      </div>

      <nav class="sidebar__nav" role="navigation" aria-label="Main navigation">
        <div class="nav-section">
          <div class="nav-section__label">Main</div>
          ${this.#navItem('dashboard',   '📊', 'Dashboard')}
          ${this.#navItem('add_expense', '➕', 'Add Expense')}
          ${this.#navItem('history',     '📋', 'History')}
          ${this.#navItem('reports',     '📈', 'Reports')}
        </div>
        <div class="nav-section">
          <div class="nav-section__label">Settings</div>
          ${this.#navItem('settings', '⚙️', 'Settings')}
        </div>
        <div class="nav-section">
          <div class="nav-section__label">Pages (Demo)</div>
          ${this.#navItem('login', '🔑', 'Login')}
          ${this.#navItem('signup', '📝', 'Sign Up')}
          ${this.#navItem('setup', '🎯', 'Setup')}
        </div>
      </nav>

      <div class="sidebar__footer">
        <div class="user-card" id="sidebarUserCard" role="button" tabindex="0" aria-label="User menu">
          <div class="user-card__avatar">${user?.avatarInitials ?? '?'}</div>
          <div class="user-card__info">
            <div class="user-card__name">${user?.name ?? 'User'}</div>
            <div class="user-card__email">${user?.email ?? ''}</div>
          </div>
        </div>
      </div>

      <button class="sidebar__toggle" id="sidebarToggle" aria-label="Toggle sidebar">
        ‹
      </button>
    `;

    if (this.#collapsed) this.el.classList.add('collapsed');
    this.#syncMainContent();
  }

  #navItem(page, icon, label) {
    const isActive = this.#activePage === page;
    return `
      <a href="${page}.html"
         class="nav-item${isActive ? ' active' : ''}"
         aria-current="${isActive ? 'page' : 'false'}">
        <span class="nav-item__icon" aria-hidden="true">${icon}</span>
        <span class="nav-item__label">${label}</span>
      </a>`;
  }

  bindEvents() {
    const toggleBtn = this.el.querySelector('#sidebarToggle');
    if (toggleBtn) {
      this._on(toggleBtn, 'click', () => this.toggle());
    }

    const userCard = this.el.querySelector('#sidebarUserCard');
    if (userCard) {
      this._on(userCard, 'click', () => {
        Bus.emit(AppEvents.MODAL_OPEN, { type: 'userMenu' });
      });
    }

    this._bus(AppEvents.AUTH_CHANGED, (user) => {
      const avatar = this.el.querySelector('.user-card__avatar');
      const name   = this.el.querySelector('.user-card__name');
      const email  = this.el.querySelector('.user-card__email');
      if (avatar) avatar.textContent = user?.avatarInitials ?? '?';
      if (name)   name.textContent   = user?.name ?? '';
      if (email)  email.textContent  = user?.email ?? '';
    });
  }

  toggle() {
    this.#collapsed = !this.#collapsed;
    this.el.classList.toggle('collapsed', this.#collapsed);
    localStorage.setItem('sidebar_collapsed', this.#collapsed);
    this.#syncMainContent();
    Bus.emit(AppEvents.SIDEBAR_TOGGLE, this.#collapsed);
  }

  #syncMainContent() {
    const main = document.querySelector('.main-content');
    if (main) main.classList.toggle('sidebar-collapsed', this.#collapsed);
  }

  /** Open on mobile. */
  openMobile() {
    this.el.classList.add('mobile-open');
    document.querySelector('.sidebar-overlay')?.classList.remove('d-none');
  }

  closeMobile() {
    this.el.classList.remove('mobile-open');
    document.querySelector('.sidebar-overlay')?.classList.add('d-none');
  }
}

/* ============================================================
   TOPBAR COMPONENT
   ============================================================ */

class TopbarComponent extends BaseComponent {
  #title;
  #subtitle;

  /**
   * @param {HTMLElement} el
   * @param {{ title: string, subtitle?: string }} opts
   */
  constructor(el, { title, subtitle = '' } = {}) {
    super(el);
    this.#title    = title;
    this.#subtitle = subtitle;
  }

  render() {
    const auth = AppContainer.get('authService');
    const fmt  = AppContainer.get('formatter');
    const now  = fmt.date(new Date().toISOString());

    this.el.innerHTML = `
      <div class="topbar__breadcrumb">
        <h1 class="topbar__title">${this.#title}</h1>
        ${this.#subtitle ? `<p class="topbar__subtitle">${this.#subtitle || now}</p>` : ''}
      </div>
      <div class="topbar__actions">
        <button class="topbar__icon-btn" id="themeToggle" aria-label="Toggle theme" data-tooltip="Toggle dark mode">
          🌙
        </button>
        <button class="topbar__icon-btn" id="notifBtn" aria-label="Notifications" data-tooltip="Notifications">
          🔔
        </button>
        <button class="topbar__icon-btn" id="logoutBtn" aria-label="Logout" data-tooltip="Logout">
          🚪
        </button>
      </div>
    `;
  }

  bindEvents() {
    const themeBtn = this.el.querySelector('#themeToggle');
    const logoutBtn= this.el.querySelector('#logoutBtn');

    if (themeBtn) {
      this._on(themeBtn, 'click', () => {
        const settings = AppContainer.get('settingsService');
        const isDark   = document.documentElement.getAttribute('data-theme') === 'dark';
        settings.update({ theme: isDark ? 'light' : 'dark' });
        themeBtn.textContent = isDark ? '🌙' : '☀️';
      });
    }

    if (logoutBtn) {
      this._on(logoutBtn, 'click', () => {
        AppContainer.get('authService').logout();
      });
    }
  }
}

/* ============================================================
   TOAST MANAGER
   ============================================================ */

/**
 * ToastManager — displays non-blocking notifications.
 * Single Responsibility: toast display only.
 * Singleton via AppContainer registration.
 */
class ToastManager {
  #container;

  constructor() {
    this.#container = this.#createContainer();
  }

  #createContainer() {
    let el = document.getElementById('toastContainer');
    if (!el) {
      el = document.createElement('div');
      el.id = 'toastContainer';
      el.className = 'toast-container';
      el.setAttribute('role', 'region');
      el.setAttribute('aria-live', 'polite');
      el.setAttribute('aria-label', 'Notifications');
      document.body.appendChild(el);
    }
    return el;
  }

  /**
   * Show a toast.
   * @param {Object} opts
   * @param {string}  opts.message
   * @param {string}  [opts.title]
   * @param {'success'|'error'|'warning'|'info'} [opts.type]
   * @param {number}  [opts.duration] ms — 0 for persistent
   */
  show({ message, title = '', type = 'info', duration = 4000 } = {}) {
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    const toast = document.createElement('div');
    toast.className  = `toast toast--${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML  = `
      <div class="toast__icon" aria-hidden="true">${icons[type]}</div>
      <div class="toast__message">
        ${title ? `<div class="toast__title">${title}</div>` : ''}
        <div class="toast__body">${message}</div>
      </div>
      <button class="toast__close" aria-label="Dismiss">✕</button>
    `;

    this.#container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      requestAnimationFrame(() => toast.classList.add('show'));
    });

    const dismiss = () => this.#dismiss(toast);
    toast.querySelector('.toast__close').addEventListener('click', dismiss);
    if (duration > 0) setTimeout(dismiss, duration);
    return dismiss; // allow manual dismissal
  }

  #dismiss(toast) {
    toast.classList.remove('show');
    toast.classList.add('hide');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }

  success(message, title)  { return this.show({ message, title, type: 'success' }); }
  error(message, title)    { return this.show({ message, title, type: 'error', duration: 6000 }); }
  warning(message, title)  { return this.show({ message, title, type: 'warning' }); }
  info(message, title)     { return this.show({ message, title, type: 'info' }); }
}

/* ============================================================
   MODAL MANAGER
   ============================================================ */

/**
 * ModalManager — manages a single modal with configurable content.
 * Open/Closed: register new modal types via registerType().
 */
class ModalManager {
  #backdrop;
  #modal;
  #types = new Map();

  constructor() {
    this.#createMarkup();
    this.#bindBaseEvents();

    // Listen on the Bus
    Bus.on(AppEvents.MODAL_OPEN,  (opts) => this.open(opts));
    Bus.on(AppEvents.MODAL_CLOSE, ()     => this.close());
  }

  #createMarkup() {
    this.#backdrop = document.createElement('div');
    this.#backdrop.className = 'modal-backdrop';
    this.#backdrop.setAttribute('role', 'dialog');
    this.#backdrop.setAttribute('aria-modal', 'true');
    this.#backdrop.innerHTML = `
      <div class="modal" role="document">
        <div class="modal__header">
          <h2 class="modal__title" id="modalTitle"></h2>
          <button class="modal__close" aria-label="Close dialog">✕</button>
        </div>
        <div class="modal__body" id="modalBody"></div>
        <div class="modal__footer" id="modalFooter"></div>
      </div>
    `;
    document.body.appendChild(this.#backdrop);
    this.#modal = this.#backdrop.querySelector('.modal');
  }

  #bindBaseEvents() {
    this.#backdrop.querySelector('.modal__close')
      .addEventListener('click', () => this.close());
    this.#backdrop.addEventListener('click', (e) => {
      if (e.target === this.#backdrop) this.close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) this.close();
    });
  }

  get isOpen() { return this.#backdrop.classList.contains('visible'); }

  /**
   * Register a modal type renderer.
   * Open/Closed: add types without modifying open().
   * @param {string} type
   * @param {Function} renderer — (opts) => { title, body, footer? }
   */
  registerType(type, renderer) {
    this.#types.set(type, renderer);
  }

  /**
   * Open the modal.
   * @param {{ type?: string, title?: string, body?: string, footer?: string }} opts
   */
  open(opts = {}) {
    let content;
    if (opts.type && this.#types.has(opts.type)) {
      content = this.#types.get(opts.type)(opts);
    } else {
      content = opts;
    }

    this.#backdrop.querySelector('#modalTitle').textContent  = content.title  ?? '';
    this.#backdrop.querySelector('#modalBody').innerHTML     = content.body   ?? '';
    this.#backdrop.querySelector('#modalFooter').innerHTML   = content.footer ?? '';

    this.#backdrop.hidden = false;
    requestAnimationFrame(() => this.#backdrop.classList.add('visible'));
    document.body.style.overflow = 'hidden';

    // Focus trap
    setTimeout(() => {
      const firstFocusable = this.#modal.querySelector('button, [href], input, select, textarea');
      firstFocusable?.focus();
    }, 100);
  }

  close() {
    this.#backdrop.classList.remove('visible');
    document.body.style.overflow = '';
    this.#backdrop.addEventListener('transitionend', () => {
      this.#backdrop.hidden = true;
    }, { once: true });
  }
}

/* ============================================================
   FORM VALIDATOR — Single Responsibility
   ============================================================ */

/**
 * FormValidator — validates form fields against a schema.
 * Open/Closed: add new rule types to the RULES map; don't modify validate().
 */
class FormValidator {
  #schema;

  static #RULES = {
    required:    (v)    => v !== '' && v !== null && v !== undefined,
    minLength:   (v, n) => String(v).length >= n,
    maxLength:   (v, n) => String(v).length <= n,
    min:         (v, n) => Number(v) >= n,
    max:         (v, n) => Number(v) <= n,
    email:       (v)    => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v),
    numeric:     (v)    => !isNaN(Number(v)) && String(v).trim() !== '',
    pattern:     (v, p) => new RegExp(p).test(v),
    custom:      (v, fn)=> fn(v),
  };

  /**
   * @param {Object} schema — { fieldName: [{ rule, value, message }] }
   */
  constructor(schema) {
    this.#schema = schema;
  }

  /**
   * Validate a values object.
   * @param {Object} values
   * @returns {{ valid: boolean, errors: Object<string, string> }}
   */
  validate(values) {
    const errors = {};

    for (const [field, rules] of Object.entries(this.#schema)) {
      const val = values[field] ?? '';
      for (const { rule, value, message } of rules) {
        const fn = FormValidator.#RULES[rule];
        if (!fn) continue;
        const passes = fn(val, value);
        if (!passes) {
          errors[field] = message;
          break; // first failing rule per field
        }
      }
    }

    return { valid: Object.keys(errors).length === 0, errors };
  }

  /**
   * Bind live validation to a form element.
   * @param {HTMLFormElement} form
   */
  bindLive(form) {
    form.querySelectorAll('[name]').forEach(input => {
      input.addEventListener('blur', () => {
        const values = this.#getFormValues(form);
        const { errors } = this.validate(values);
        this.#applyError(input, errors[input.name] ?? null);
      });
      input.addEventListener('input', () => {
        // Clear error on typing
        this.#applyError(input, null);
      });
    });
  }

  /**
   * Apply (or clear) an error message on a field.
   * @param {HTMLElement} input
   * @param {string|null} message
   */
  #applyError(input, message) {
    input.classList.toggle('error', !!message);
    let errEl = input.parentElement.querySelector('.form-error');
    if (message) {
      if (!errEl) {
        errEl = document.createElement('p');
        errEl.className = 'form-error';
        input.parentElement.appendChild(errEl);
      }
      errEl.textContent = message;
    } else {
      errEl?.remove();
    }
  }

  #getFormValues(form) {
    const fd = new FormData(form);
    return Object.fromEntries(fd.entries());
  }

  /**
   * Apply all errors to a form (after submit attempt).
   * @param {HTMLFormElement} form
   * @param {Object} errors
   */
  applyErrors(form, errors) {
    for (const [field, message] of Object.entries(errors)) {
      const input = form.querySelector(`[name="${field}"]`);
      if (input) this.#applyError(input, message);
    }
    // Focus first invalid
    const first = form.querySelector('.error');
    first?.focus();
  }

  clearErrors(form) {
    form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    form.querySelectorAll('.form-error').forEach(el => el.remove());
  }
}

/* ============================================================
   CHART HELPERS — wraps Chart.js with brand tokens
   ============================================================ */

/**
 * ChartFactory — creates branded Chart.js instances.
 * Single Responsibility: chart creation and theming.
 * Open/Closed: add new chart types via static methods.
 */
class ChartFactory {
  static #COLORS = {
    coral:  '#FF6F61',
    blue:   '#007BFF',
    yellow: '#FFD700',
    green:  '#2ECC71',
    purple: '#9B59B6',
    orange: '#E67E22',
    teal:   '#1ABC9C',
    red:    '#E74C3C',
  };

  static #PALETTE = Object.values(ChartFactory.#COLORS);

  static get palette() { return ChartFactory.#PALETTE; }

  static #defaults() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      gridColor:  isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
      textColor:  isDark ? '#9A9088' : '#6B6560',
      background: isDark ? '#1A1714' : '#FFFFFF',
    };
  }

  /**
   * Create a donut / doughnut chart.
   * @param {HTMLCanvasElement} canvas
   * @param {{ labels: string[], data: number[], colors?: string[] }} config
   * @returns {Chart}
   */
  static donut(canvas, { labels, data, colors }) {
    const { background } = ChartFactory.#defaults();
    return new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors ?? ChartFactory.#PALETTE,
          borderColor: background,
          borderWidth: 3,
          hoverOffset: 8,
        }],
      },
      options: {
        cutout: '72%',
        plugins: {
          legend: { display: false },
          tooltip: ChartFactory.#tooltipOptions(),
        },
        animation: { animateRotate: true, duration: 700 },
      },
    });
  }

  /**
   * Create a line chart.
   * @param {HTMLCanvasElement} canvas
   * @param {{ labels: string[], datasets: Array }} config
   * @returns {Chart}
   */
  static line(canvas, { labels, datasets }) {
    const d = ChartFactory.#defaults();
    return new Chart(canvas, {
      type: 'line',
      data: { labels, datasets: datasets.map((ds, i) => ({
        borderColor:     ChartFactory.#PALETTE[i],
        backgroundColor: ChartFactory.#PALETTE[i] + '18',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        ...ds,
      }))},
      options: {
        responsive: true,
        plugins: {
          legend: { display: datasets.length > 1, labels: { color: d.textColor, font: { size: 12 } } },
          tooltip: ChartFactory.#tooltipOptions(),
        },
        scales: {
          x: { grid: { color: d.gridColor }, ticks: { color: d.textColor, font: { size: 11 } } },
          y: { grid: { color: d.gridColor }, ticks: { color: d.textColor, font: { size: 11 }, callback: v => '$' + v.toLocaleString() } },
        },
      },
    });
  }

  /**
   * Create a bar chart.
   * @param {HTMLCanvasElement} canvas
   * @param {{ labels: string[], datasets: Array }} config
   * @returns {Chart}
   */
  static bar(canvas, { labels, datasets }) {
    const d = ChartFactory.#defaults();
    return new Chart(canvas, {
      type: 'bar',
      data: { labels, datasets: datasets.map((ds, i) => ({
        backgroundColor: ChartFactory.#PALETTE[i],
        borderRadius: 6,
        borderSkipped: false,
        ...ds,
      }))},
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: ChartFactory.#tooltipOptions(),
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: d.textColor, font: { size: 11 } } },
          y: { grid: { color: d.gridColor }, ticks: { color: d.textColor, font: { size: 11 }, callback: v => '$' + v.toLocaleString() } },
        },
      },
    });
  }

  static #tooltipOptions() {
    return {
      backgroundColor: '#0F0D0B',
      titleColor:      '#F0EDE8',
      bodyColor:       '#9A9088',
      padding:         12,
      cornerRadius:    10,
      displayColors:   true,
    };
  }
}

/* ============================================================
   WIRE UP SERVICES IN CONTAINER
   ============================================================ */

AppContainer.register('toast',  () => new ToastManager());
AppContainer.register('modal',  () => new ModalManager());

// Subscribe to bus-driven toasts
Bus.on(AppEvents.TOAST_SHOW, (opts) => AppContainer.get('toast').show(opts));

/* ============================================================
   EXPORTS
   ============================================================ */

export {
  BaseComponent,
  SidebarComponent,
  TopbarComponent,
  ToastManager,
  ModalManager,
  FormValidator,
  ChartFactory,
};
