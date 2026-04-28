/**
 * core.js — Application Core Infrastructure
 *
 * SOLID Principles applied:
 *   S — Single Responsibility: each class has one focused job
 *   O — Open/Closed: classes are open for extension, closed for modification
 *   L — Liskov Substitution: subclasses fully satisfy base contracts
 *   I — Interface Segregation: fine-grained interfaces via JSDoc @interface
 *   D — Dependency Inversion: high-level modules depend on abstractions
 *
 * OOP Patterns: Singleton, Observer, Strategy, Factory, Repository
 */

'use strict';

/* ============================================================
   EVENT BUS — Observer pattern for decoupled communication
   ============================================================ */

/**
 * EventBus — Publish/Subscribe system.
 * Single Responsibility: manages only event subscriptions/emissions.
 */
class EventBus {
  #listeners = new Map();

  /**
   * Subscribe to an event.
   * @param {string} event
   * @param {Function} handler
   * @returns {Function} unsubscribe function
   */
  on(event, handler) {
    if (!this.#listeners.has(event)) {
      this.#listeners.set(event, new Set());
    }
    this.#listeners.get(event).add(handler);

    // Return an unsubscribe function (clean API)
    return () => this.off(event, handler);
  }

  /**
   * Subscribe once — auto-removes after first call.
   * @param {string} event
   * @param {Function} handler
   */
  once(event, handler) {
    const wrapper = (...args) => {
      handler(...args);
      this.off(event, wrapper);
    };
    this.on(event, wrapper);
  }

  /**
   * Unsubscribe from an event.
   * @param {string} event
   * @param {Function} handler
   */
  off(event, handler) {
    this.#listeners.get(event)?.delete(handler);
  }

  /**
   * Emit an event with optional payload.
   * @param {string} event
   * @param {*} [payload]
   */
  emit(event, payload) {
    this.#listeners.get(event)?.forEach(handler => {
      try {
        handler(payload);
      } catch (err) {
        console.error(`[EventBus] Error in handler for "${event}":`, err);
      }
    });
  }

  /** Remove all listeners for an event. */
  clear(event) {
    if (event) {
      this.#listeners.delete(event);
    } else {
      this.#listeners.clear();
    }
  }
}

/** Global singleton event bus */
const Bus = new EventBus();

/* ============================================================
   APP EVENTS — Named constants prevent string typos (ISP)
   ============================================================ */

const AppEvents = Object.freeze({
  // Auth
  AUTH_LOGIN:       'auth:login',
  AUTH_LOGOUT:      'auth:logout',
  AUTH_CHANGED:     'auth:changed',

  // Expenses
  EXPENSE_ADDED:    'expense:added',
  EXPENSE_UPDATED:  'expense:updated',
  EXPENSE_DELETED:  'expense:deleted',
  EXPENSES_LOADED:  'expenses:loaded',

  // Budget
  BUDGET_UPDATED:   'budget:updated',

  // Settings
  SETTINGS_CHANGED: 'settings:changed',
  THEME_CHANGED:    'theme:changed',

  // UI
  TOAST_SHOW:       'toast:show',
  MODAL_OPEN:       'modal:open',
  MODAL_CLOSE:      'modal:close',
  SIDEBAR_TOGGLE:   'sidebar:toggle',
});

/* ============================================================
   STORAGE ABSTRACTION — Dependency Inversion Principle
   High-level modules depend on IStorage, not localStorage directly.
   ============================================================ */

/**
 * @interface IStorage
 * Segregated interface — only what consumers need.
 */

/**
 * LocalStorageAdapter — concrete implementation of IStorage.
 * Open/Closed: swap with SessionStorageAdapter or RemoteStorageAdapter
 *   without touching any consumer code.
 */
class LocalStorageAdapter {
  #prefix;

  /** @param {string} prefix namespace to prevent key collisions */
  constructor(prefix = 'xpense_') {
    this.#prefix = prefix;
  }

  #key(k) { return `${this.#prefix}${k}`; }

  /**
   * @param {string} key
   * @param {*} value — auto-serialized to JSON
   */
  set(key, value) {
    try {
      localStorage.setItem(this.#key(key), JSON.stringify(value));
    } catch (e) {
      console.error('[Storage] Write failed:', e);
    }
  }

  /**
   * @param {string} key
   * @param {*} [fallback]
   * @returns {*}
   */
  get(key, fallback = null) {
    try {
      const raw = localStorage.getItem(this.#key(key));
      return raw === null ? fallback : JSON.parse(raw);
    } catch {
      return fallback;
    }
  }

  /** @param {string} key */
  remove(key) {
    localStorage.removeItem(this.#key(key));
  }

  /** Remove all keys in this namespace. */
  clear() {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k?.startsWith(this.#prefix)) keysToRemove.push(k);
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
  }
}

/* ============================================================
   BASE MODEL — Template for domain models
   ============================================================ */

/**
 * BaseModel — superclass for all domain entities.
 * Liskov Substitution: subclasses must not weaken contracts.
 */
class BaseModel {
  #id;
  #createdAt;
  #updatedAt;

  constructor(data = {}) {
    this.#id        = data.id        ?? crypto.randomUUID();
    this.#createdAt = data.createdAt ?? new Date().toISOString();
    this.#updatedAt = data.updatedAt ?? new Date().toISOString();
  }

  get id()        { return this.#id; }
  get createdAt() { return this.#createdAt; }
  get updatedAt() { return this.#updatedAt; }

  touch() {
    this.#updatedAt = new Date().toISOString();
  }

  /**
   * Serialize to a plain object (for storage/transfer).
   * Subclasses MUST call super.toJSON() and spread it.
   * @returns {Object}
   */
  toJSON() {
    return {
      id:        this.#id,
      createdAt: this.#createdAt,
      updatedAt: this.#updatedAt,
    };
  }

  /**
   * Validate the model. Subclasses override this.
   * @returns {{ valid: boolean, errors: string[] }}
   */
  validate() {
    return { valid: true, errors: [] };
  }
}

/* ============================================================
   BASE REPOSITORY — Generic CRUD over a storage adapter
   ============================================================ */

/**
 * BaseRepository<T extends BaseModel>
 * Open/Closed: extend for custom query logic; don't modify CRUD methods.
 * Dependency Inversion: depends on IStorage abstraction.
 */
class BaseRepository {
  #store;
  #key;
  #items = new Map();

  /**
   * @param {LocalStorageAdapter} store
   * @param {string} collectionKey
   */
  constructor(store, collectionKey) {
    this.#store = store;
    this.#key   = collectionKey;
    this.#load();
  }

  #load() {
    const raw = this.#store.get(this.#key, []);
    raw.forEach(item => this.#items.set(item.id, item));
  }

  #persist() {
    this.#store.set(this.#key, [...this.#items.values()]);
  }

  /** @returns {Object[]} all items as plain objects */
  findAll() {
    return [...this.#items.values()];
  }

  /**
   * @param {string} id
   * @returns {Object|null}
   */
  findById(id) {
    return this.#items.get(id) ?? null;
  }

  /**
   * @param {Function} predicate
   * @returns {Object[]}
   */
  findWhere(predicate) {
    return [...this.#items.values()].filter(predicate);
  }

  /**
   * Save (insert or update) an item.
   * @param {BaseModel} model
   * @returns {Object} saved plain object
   */
  save(model) {
    const validation = model.validate();
    if (!validation.valid) {
      throw new ValidationError(validation.errors.join('; '));
    }
    const data = model.toJSON();
    this.#items.set(data.id, data);
    this.#persist();
    return data;
  }

  /**
   * @param {string} id
   * @returns {boolean}
   */
  delete(id) {
    const existed = this.#items.delete(id);
    if (existed) this.#persist();
    return existed;
  }

  /** Remove all items. */
  clear() {
    this.#items.clear();
    this.#persist();
  }

  /** @returns {number} */
  count() { return this.#items.size; }
}

/* ============================================================
   CUSTOM ERRORS — Single Responsibility (typed error handling)
   ============================================================ */

class AppError extends Error {
  constructor(message, code) {
    super(message);
    this.name  = 'AppError';
    this.code  = code;
  }
}

class ValidationError extends AppError {
  constructor(message) {
    super(message, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

class AuthError extends AppError {
  constructor(message) {
    super(message, 'AUTH_ERROR');
    this.name = 'AuthError';
  }
}

class NotFoundError extends AppError {
  constructor(resource, id) {
    super(`${resource} with id "${id}" not found`, 'NOT_FOUND');
    this.name = 'NotFoundError';
  }
}

/* ============================================================
   FORMATTER — Single Responsibility: all display formatting
   ============================================================ */

class Formatter {
  #currency;
  #locale;

  constructor(currency = 'USD', locale = 'en-US') {
    this.#currency = currency;
    this.#locale   = locale;
  }

  /** @returns {string} e.g. "$1,234.56" */
  money(amount) {
    return new Intl.NumberFormat(this.#locale, {
      style: 'currency',
      currency: this.#currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  }

  /** @returns {string} e.g. "Apr 27, 2026" */
  date(dateStr) {
    return new Intl.DateTimeFormat(this.#locale, {
      year: 'numeric', month: 'short', day: 'numeric'
    }).format(new Date(dateStr));
  }

  /** @returns {string} e.g. "2 days ago" */
  relativeDate(dateStr) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const rtf  = new Intl.RelativeTimeFormat(this.#locale, { numeric: 'auto' });
    const mins  = Math.round(diff / 60000);
    const hours = Math.round(diff / 3600000);
    const days  = Math.round(diff / 86400000);
    if (Math.abs(mins)  < 60) return rtf.format(-mins,  'minute');
    if (Math.abs(hours) < 24) return rtf.format(-hours, 'hour');
    return rtf.format(-days, 'day');
  }

  /** @returns {string} e.g. "75%" */
  percent(value, total) {
    if (!total) return '0%';
    return `${Math.round((value / total) * 100)}%`;
  }

  /** Update currency (e.g. on settings change). */
  setCurrency(currency) { this.#currency = currency; }
}

/* ============================================================
   SERVICE LOCATOR / DI CONTAINER — Dependency Inversion
   ============================================================ */

/**
 * Container — lightweight dependency injection.
 * Register factories once; resolve anywhere without tight coupling.
 */
class Container {
  #registry  = new Map();
  #instances = new Map();

  /**
   * Register a factory (lazy singleton by default).
   * @param {string} name
   * @param {Function} factory — receives (container) => instance
   * @param {{ singleton?: boolean }} [opts]
   */
  register(name, factory, { singleton = true } = {}) {
    this.#registry.set(name, { factory, singleton });
  }

  /**
   * Check if a dependency is registered.
   * @param {string} name
   * @returns {boolean}
   */
  has(name) {
    return this.#registry.has(name);
  }

  /**
   * Resolve a registered dependency.
   * @param {string} name
   * @returns {*}
   */
  resolve(name) {
    if (!this.#registry.has(name)) {
      throw new AppError(`[Container] Unregistered dependency: "${name}"`, 'DI_ERROR');
    }
    const { factory, singleton } = this.#registry.get(name);
    if (singleton) {
      if (!this.#instances.has(name)) {
        this.#instances.set(name, factory(this));
      }
      return this.#instances.get(name);
    }
    return factory(this);
  }

  /** Convenience alias */
  get(name) { return this.resolve(name); }
}

/** Global application container */
const AppContainer = new Container();

// Register core services
AppContainer.register('storage',   () => new LocalStorageAdapter('xpense_'));
AppContainer.register('bus',       () => Bus);
AppContainer.register('formatter', (c) => {
  const settings = c.resolve('storage').get('settings', {});
  return new Formatter(settings.currency || 'USD', settings.locale || 'en-US');
});

// Export everything needed by other modules
export {
  EventBus,
  Bus,
  AppEvents,
  LocalStorageAdapter,
  BaseModel,
  BaseRepository,
  AppError,
  ValidationError,
  AuthError,
  NotFoundError,
  Formatter,
  Container,
  AppContainer,
};
