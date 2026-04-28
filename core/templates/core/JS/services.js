/**
 * services.js — Business Logic Services
 *
 * Services orchestrate models + repositories.
 * They are the single source of truth for business rules.
 *
 * SOLID:
 *   S — Each service owns exactly one domain concern.
 *   O — Strategy pattern for sorting/filtering (open for extension).
 *   L — All services satisfy IService interface (init, destroy).
 *   I — Fine-grained service interfaces prevent fat dependencies.
 *   D — Services receive their dependencies via constructor injection.
 */

import {
  Bus, AppEvents, AppContainer,
  BaseRepository, ValidationError, AuthError, NotFoundError,
} from './core.js';
import { Expense, Budget, User, Settings, ExpenseType } from './models.js';

/* ============================================================
   BASE SERVICE
   ============================================================ */

/**
 * BaseService — lifecycle contract all services must satisfy.
 * Liskov: concrete services must init/destroy correctly.
 */
class BaseService {
  #initialized = false;

  /** Called once at app bootstrap. Override to set up listeners. */
  init() { this.#initialized = true; }

  /** Called on logout/cleanup. Override to remove listeners. */
  destroy() { this.#initialized = false; }

  get isInitialized() { return this.#initialized; }
}

/* ============================================================
   SORTING / FILTERING STRATEGIES — Open/Closed
   New strategies can be added without modifying ExpenseService.
   ============================================================ */

/** @interface ISortStrategy */

class SortByDateDesc  { compare(a, b) { return new Date(b.date) - new Date(a.date); } }
class SortByDateAsc   { compare(a, b) { return new Date(a.date) - new Date(b.date); } }
class SortByAmountDesc{ compare(a, b) { return b.amount - a.amount; } }
class SortByAmountAsc { compare(a, b) { return a.amount - b.amount; } }

const SortStrategies = Object.freeze({
  date_desc:   new SortByDateDesc(),
  date_asc:    new SortByDateAsc(),
  amount_desc: new SortByAmountDesc(),
  amount_asc:  new SortByAmountAsc(),
});

/** @interface IFilterStrategy */

class FilterByCategory {
  constructor(category) { this.category = category; }
  test(expense) { return expense.category === this.category; }
}

class FilterByDateRange {
  constructor(from, to) {
    this.from = new Date(from);
    this.to   = new Date(to);
    this.to.setHours(23, 59, 59, 999);
  }
  test(expense) {
    const d = new Date(expense.date);
    return d >= this.from && d <= this.to;
  }
}

class FilterByMonth {
  constructor(year, month) {
    this.prefix = `${year}-${String(month).padStart(2, '0')}`;
  }
  test(expense) { return expense.date.startsWith(this.prefix); }
}

class FilterByType {
  constructor(type) { this.type = type; }
  test(expense) { return expense.type === this.type; }
}

class FilterBySearch {
  constructor(query) { this.q = query.toLowerCase(); }
  test(expense) {
    return expense.description.toLowerCase().includes(this.q)
      || (expense.note || '').toLowerCase().includes(this.q);
  }
}

/* ============================================================
   AUTH SERVICE
   ============================================================ */

/**
 * AuthService — manages user sessions in this demo app.
 * In production: replace with real API calls.
 */
class AuthService extends BaseService {
  #store;
  #currentUser = null;

  /** @param {LocalStorageAdapter} store */
  constructor(store) {
    super();
    this.#store = store;
  }

  init() {
    super.init();
    const userData = this.#store.get('current_user');
    if (userData) {
      this.#currentUser = User.from(userData);
    }
  }

  get currentUser() { return this.#currentUser; }
  get isLoggedIn()  { return this.#currentUser !== null; }

  /**
   * Register a new user.
   * @param {{ name: string, email: string, password: string }} data
   * @returns {User}
   */
  register(data) {
    const users = this.#store.get('users', []);
    if (users.find(u => u.email === data.email.toLowerCase())) {
      throw new ValidationError('An account with this email already exists.');
    }
    const user = new User({ name: data.name, email: data.email });
    const validation = user.validate();
    if (!validation.valid) throw new ValidationError(validation.errors.join(' '));

    // NOTE: In production, hash the password server-side.
    // Here we store a flag only (this is a demo SPA).
    users.push({ ...user.toJSON(), _pwHash: btoa(data.password) });
    this.#store.set('users', users);
    this.#setSession(user);
    return user;
  }

  /**
   * Log in an existing user.
   * @param {string} email
   * @param {string} password
   * @returns {User}
   */
  login(email, password) {
    const users   = this.#store.get('users', []);
    const record  = users.find(u => u.email === email.toLowerCase());
    if (!record || record._pwHash !== btoa(password)) {
      throw new AuthError('Invalid email or password.');
    }
    const user = User.from(record);
    this.#setSession(user);
    return user;
  }

  /** Log out the current user. */
  logout() {
    this.#currentUser = null;
    this.#store.remove('current_user');
    Bus.emit(AppEvents.AUTH_LOGOUT);
    window.location.href = 'login.html';
  }

  /**
   * Update current user profile.
   * @param {Object} patch
   */
  updateProfile(patch) {
    if (!this.#currentUser) throw new AuthError('Not authenticated.');
    if (patch.name)     this.#currentUser.name     = patch.name;
    if (patch.currency) this.#currentUser.currency = patch.currency;
    this.#setSession(this.#currentUser);
    Bus.emit(AppEvents.AUTH_CHANGED, this.#currentUser);
  }

  #setSession(user) {
    this.#currentUser = user;
    this.#store.set('current_user', user.toJSON());
    Bus.emit(AppEvents.AUTH_CHANGED, user);
  }

  /** Guards: redirect to login if not authenticated. */
  requireAuth() {
    if (!this.isLoggedIn) {
      window.location.href = 'login.html';
      throw new AuthError('Authentication required.');
    }
  }
}

/* ============================================================
   EXPENSE SERVICE
   ============================================================ */

/**
 * ExpenseService — all CRUD + query operations for expenses.
 */
class ExpenseService extends BaseService {
  #repo;
  #bus;

  /**
   * @param {BaseRepository} repo
   * @param {EventBus} bus
   */
  constructor(repo, bus) {
    super();
    this.#repo = repo;
    this.#bus  = bus;
  }

  /**
   * Add a new expense.
   * @param {Object} data
   * @returns {Object} saved expense
   */
  add(data) {
    const expense = new Expense(data);
    const saved   = this.#repo.save(expense);
    this.#bus.emit(AppEvents.EXPENSE_ADDED, saved);
    return saved;
  }

  /**
   * Update an existing expense.
   * @param {string} id
   * @param {Object} patch
   * @returns {Object}
   */
  update(id, patch) {
    const raw = this.#repo.findById(id);
    if (!raw) throw new NotFoundError('Expense', id);

    const expense = new Expense({ ...raw, ...patch });
    const saved   = this.#repo.save(expense);
    this.#bus.emit(AppEvents.EXPENSE_UPDATED, saved);
    return saved;
  }

  /**
   * Delete an expense by id.
   * @param {string} id
   */
  delete(id) {
    const existed = this.#repo.delete(id);
    if (!existed) throw new NotFoundError('Expense', id);
    this.#bus.emit(AppEvents.EXPENSE_DELETED, { id });
  }

  /**
   * Get all expenses, optionally sorted.
   * @param {ISortStrategy} [sort]
   * @returns {Object[]}
   */
  getAll(sort = SortStrategies.date_desc) {
    const all = this.#repo.findAll();
    return sort ? [...all].sort((a, b) => sort.compare(a, b)) : all;
  }

  /** @param {string} id @returns {Object|null} */
  getById(id) { return this.#repo.findById(id); }

  /**
   * Query with multiple filter strategies + one sort strategy.
   * Open/Closed: new filters added without touching this method.
   *
   * @param {Object} opts
   * @param {string}   [opts.category]
   * @param {string}   [opts.type]
   * @param {string}   [opts.from]
   * @param {string}   [opts.to]
   * @param {number}   [opts.year]
   * @param {number}   [opts.month]
   * @param {string}   [opts.search]
   * @param {ISortStrategy} [opts.sort]
   * @param {number}   [opts.limit]
   * @returns {Object[]}
   */
  query({ category, type, from, to, year, month, search, sort, limit } = {}) {
    const filters = [];
    if (category)           filters.push(new FilterByCategory(category));
    if (type)               filters.push(new FilterByType(type));
    if (from && to)         filters.push(new FilterByDateRange(from, to));
    if (year  && month)     filters.push(new FilterByMonth(year, month));
    if (search)             filters.push(new FilterBySearch(search));

    let result = this.#repo.findAll();

    // Apply all filters (chain)
    if (filters.length) {
      result = result.filter(e => filters.every(f => f.test(e)));
    }

    // Sort
    const strategy = sort ?? SortStrategies.date_desc;
    result = result.sort((a, b) => strategy.compare(a, b));

    // Limit
    if (limit) result = result.slice(0, limit);

    return result;
  }

  /**
   * Get expenses for the current calendar month.
   * @returns {Object[]}
   */
  thisMonth() {
    const now = new Date();
    return this.query({ year: now.getFullYear(), month: now.getMonth() + 1 });
  }

  /**
   * Aggregate totals for a list of expenses.
   * @param {Object[]} expenses
   * @returns {{ total: number, income: number, expenses: number, net: number }}
   */
  totals(expenses) {
    return expenses.reduce((acc, e) => {
      if (e.type === ExpenseType.INCOME) {
        acc.income += e.amount;
      } else {
        acc.expenses += e.amount;
      }
      acc.total += e.amount;
      acc.net    = acc.income - acc.expenses;
      return acc;
    }, { total: 0, income: 0, expenses: 0, net: 0 });
  }

  /**
   * Group expenses by category and compute totals.
   * @param {Object[]} expenses
   * @returns {Map<string, { total: number, count: number }>}
   */
  byCategory(expenses) {
    const map = new Map();
    expenses
      .filter(e => e.type === ExpenseType.EXPENSE)
      .forEach(e => {
        const prev = map.get(e.category) ?? { total: 0, count: 0 };
        map.set(e.category, { total: prev.total + e.amount, count: prev.count + 1 });
      });
    return map;
  }

  /**
   * Group by day for a bar chart.
   * @param {Object[]} expenses
   * @returns {{ labels: string[], amounts: number[] }}
   */
  byDay(expenses) {
    const map = new Map();
    expenses.forEach(e => {
      const prev = map.get(e.date) ?? 0;
      map.set(e.date, prev + (e.type === ExpenseType.EXPENSE ? e.amount : 0));
    });
    const sorted = [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
    return {
      labels:  sorted.map(([d]) => d),
      amounts: sorted.map(([, v]) => v),
    };
  }
}

/* ============================================================
   BUDGET SERVICE
   ============================================================ */

/**
 * BudgetService — manage and evaluate spending limits.
 */
class BudgetService extends BaseService {
  #repo;
  #expenseService;
  #bus;

  constructor(repo, expenseService, bus) {
    super();
    this.#repo           = repo;
    this.#expenseService = expenseService;
    this.#bus            = bus;
  }

  /**
   * Set or update a budget limit.
   * @param {string} category
   * @param {number} limit
   * @param {string} [month] "YYYY-MM"
   * @returns {Object}
   */
  set(category, limit, month) {
    const existing = this.#findByCategory(category, month);
    const data     = existing
      ? { ...existing, limit }
      : { category, limit, month };

    const budget = new Budget(data);
    const saved  = this.#repo.save(budget);
    this.#bus.emit(AppEvents.BUDGET_UPDATED, saved);
    return saved;
  }

  /**
   * Get all budgets with their current spending status.
   * @param {string} [month]
   * @returns {Array<{ budget: Object, spent: number, progress: Object }>}
   */
  getStatus(month) {
    const m = month ?? new Date().toISOString().substring(0, 7);
    const [year, mo] = m.split('-').map(Number);
    const expenses = this.#expenseService.query({
      year, month: mo, type: ExpenseType.EXPENSE
    });
    const byCategory = this.#expenseService.byCategory(expenses);

    return this.#repo.findWhere(b => b.month === m).map(raw => {
      const budget  = Budget.from(raw);
      const spent   = byCategory.get(raw.category)?.total ?? 0;
      const progress = budget.progress(spent);
      return { budget: raw, spent, ...progress };
    });
  }

  /**
   * @param {string} category
   * @param {string} [month]
   * @returns {Object|null}
   */
  #findByCategory(category, month) {
    const m = month ?? new Date().toISOString().substring(0, 7);
    return this.#repo.findWhere(b => b.category === category && b.month === m)[0] ?? null;
  }

  getAll()      { return this.#repo.findAll(); }
  delete(id)    { return this.#repo.delete(id); }
}

/* ============================================================
   SETTINGS SERVICE
   ============================================================ */

/**
 * SettingsService — persist and apply user preferences.
 */
class SettingsService extends BaseService {
  #store;
  #bus;
  #settings;

  constructor(store, bus) {
    super();
    this.#store = store;
    this.#bus   = bus;
  }

  init() {
    super.init();
    const raw = this.#store.get('settings', {});
    this.#settings = Settings.from(raw);
    this.#applyTheme(this.#settings.theme);
  }

  get current() { return this.#settings; }

  /**
   * Update settings.
   * @param {Object} patch
   */
  update(patch) {
    this.#settings.update(patch);
    this.#store.set('settings', this.#settings.toJSON());
    if (patch.theme) this.#applyTheme(patch.theme);
    this.#bus.emit(AppEvents.SETTINGS_CHANGED, this.#settings);
    if (patch.theme) this.#bus.emit(AppEvents.THEME_CHANGED, patch.theme);
  }

  #applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }

  reset() {
    this.#store.remove('settings');
    this.#settings = Settings.from({});
    this.#applyTheme(this.#settings.theme);
    this.#bus.emit(AppEvents.SETTINGS_CHANGED, this.#settings);
  }
}

/* ============================================================
   REPORT SERVICE
   ============================================================ */

/**
 * ReportService — analytics and aggregated report data.
 * Single Responsibility: only produces report-ready data structures.
 */
class ReportService extends BaseService {
  #expenseService;
  #budgetService;

  constructor(expenseService, budgetService) {
    super();
    this.#expenseService = expenseService;
    this.#budgetService  = budgetService;
  }

  /**
   * Monthly summary report.
   * @param {number} year
   * @param {number} month
   * @returns {Object}
   */
  monthly(year, month) {
    const expenses    = this.#expenseService.query({ year, month });
    const totals      = this.#expenseService.totals(expenses);
    const byCategory  = this.#expenseService.byCategory(expenses);
    const byDay       = this.#expenseService.byDay(expenses);

    return { year, month, expenses, totals, byCategory, byDay };
  }

  /**
   * 12-month trend (spending per month).
   * @returns {{ labels: string[], income: number[], expenses: number[] }}
   */
  yearlyTrend() {
    const now    = new Date();
    const labels = [];
    const income = [];
    const expArr = [];

    for (let i = 11; i >= 0; i--) {
      const d  = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const yr = d.getFullYear();
      const mo = d.getMonth() + 1;
      labels.push(`${d.toLocaleString('default', { month: 'short' })} '${String(yr).slice(2)}`);
      const data = this.monthly(yr, mo);
      income.push(data.totals.income);
      expArr.push(data.totals.expenses);
    }

    return { labels, income, expenses: expArr };
  }

  /**
   * Savings rate for a month.
   * @param {number} year
   * @param {number} month
   * @returns {number} 0–100
   */
  savingsRate(year, month) {
    const { totals } = this.monthly(year, month);
    if (!totals.income) return 0;
    return Math.max(0, Math.round(((totals.income - totals.expenses) / totals.income) * 100));
  }

  /**
   * Top spending categories this month.
   * @param {number} [topN]
   * @returns {Array<{ category: string, total: number, percent: number }>}
   */
  topCategories(topN = 5) {
    const now = new Date();
    const { byCategory, totals } = this.monthly(now.getFullYear(), now.getMonth() + 1);
    return [...byCategory.entries()]
      .sort((a, b) => b[1].total - a[1].total)
      .slice(0, topN)
      .map(([cat, { total }]) => ({
        category: cat,
        total,
        percent: totals.expenses ? Math.round((total / totals.expenses) * 100) : 0,
      }));
  }
}

/* ============================================================
   EXPORT & WIRE UP — Register services in container
   ============================================================ */

AppContainer.register('expenseRepo', (c) =>
  new BaseRepository(c.get('storage'), 'expenses')
);
AppContainer.register('budgetRepo', (c) =>
  new BaseRepository(c.get('storage'), 'budgets')
);

AppContainer.register('authService', (c) => {
  const svc = new AuthService(c.get('storage'));
  svc.init();
  return svc;
});

AppContainer.register('expenseService', (c) => {
  const svc = new ExpenseService(c.get('expenseRepo'), c.get('bus'));
  svc.init();
  return svc;
});

AppContainer.register('budgetService', (c) => {
  const svc = new BudgetService(c.get('budgetRepo'), c.get('expenseService'), c.get('bus'));
  svc.init();
  return svc;
});

AppContainer.register('settingsService', (c) => {
  const svc = new SettingsService(c.get('storage'), c.get('bus'));
  svc.init();
  return svc;
});

AppContainer.register('reportService', (c) =>
  new ReportService(c.get('expenseService'), c.get('budgetService'))
);

export {
  BaseService,
  SortStrategies,
  FilterByCategory, FilterByDateRange, FilterByMonth, FilterByType, FilterBySearch,
  AuthService,
  ExpenseService,
  BudgetService,
  SettingsService,
  ReportService,
};

// Eagerly instantiate settings service to apply theme on load
if (typeof document !== 'undefined') {
  setTimeout(() => {
    try {
      AppContainer.get('settingsService');
    } catch (e) {
      console.error('Failed to init SettingsService:', e);
    }
  }, 0);
}
