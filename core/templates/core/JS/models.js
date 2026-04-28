/**
 * models.js — Domain Models
 *
 * Each model: Single Responsibility (represents one entity),
 *   validates its own invariants (tell-don't-ask),
 *   and serializes itself cleanly.
 *
 * Liskov Substitution: all extend BaseModel without weakening contracts.
 */

import { BaseModel, ValidationError } from './core.js';

/* ============================================================
   CATEGORY MODEL
   ============================================================ */

/** @readonly Predefined expense categories */
const CATEGORIES = Object.freeze([
  { id: 'food',          label: 'Food & Dining',   emoji: '🍔',  color: '#FF6F61' },
  { id: 'transport',     label: 'Transport',        emoji: '🚌',  color: '#007BFF' },
  { id: 'shopping',      label: 'Shopping',         emoji: '🛍️',  color: '#FFD700' },
  { id: 'entertainment', label: 'Entertainment',    emoji: '🍿',  color: '#9B59B6' },
  { id: 'bills',         label: 'Bills',            emoji: '💡',  color: '#E67E22' },
  { id: 'health',        label: 'Health',           emoji: '💊',  color: '#2ECC71' },
  { id: 'utilities',     label: 'Utilities',        emoji: '💡',  color: '#E67E22' },
  { id: 'rent',          label: 'Rent & Housing',   emoji: '🏠',  color: '#1ABC9C' },
  { id: 'education',     label: 'Education',        emoji: '📚',  color: '#3498DB' },
  { id: 'travel',        label: 'Travel',           emoji: '✈️',  color: '#E74C3C' },
  { id: 'savings',       label: 'Savings',          emoji: '💰',  color: '#27AE60' },
  { id: 'income',        label: 'Income',           emoji: '💵',  color: '#2ECC71' },
  { id: 'other',         label: 'Other',            emoji: '✨',  color: '#95A5A6' },
]);

/**
 * CategoryRegistry — lookup helper (Open/Closed: add categories without
 * modifying any consumer code).
 */
class CategoryRegistry {
  #map;

  constructor(categories) {
    this.#map = new Map(categories.map(c => [c.id, c]));
  }

  /** @param {string} id @returns {Object|null} */
  find(id) { return this.#map.get(id) ?? null; }

  /** @returns {Object[]} */
  all() { return [...this.#map.values()]; }

  /** @param {string} id @returns {string} emoji or '📦' */
  emoji(id) { return this.find(id)?.emoji ?? '📦'; }

  /** @param {string} id @returns {string} hex color */
  color(id) { return this.find(id)?.color ?? '#95A5A6'; }

  /** @param {string} id @returns {string} label */
  label(id) { return this.find(id)?.label ?? 'Other'; }
}

const Categories = new CategoryRegistry(CATEGORIES);

/* ============================================================
   EXPENSE MODEL
   ============================================================ */

/** @enum {string} */
const ExpenseType = Object.freeze({
  EXPENSE: 'expense',
  INCOME:  'income',
});

/**
 * Expense — core domain model.
 * Encapsulates all business rules for a financial transaction.
 */
class Expense extends BaseModel {
  #amount;
  #description;
  #category;
  #type;
  #date;
  #note;
  #tags;
  #recurring;

  /**
   * @param {Object} data
   * @param {number} data.amount
   * @param {string} data.description
   * @param {string} data.category
   * @param {string} [data.type]
   * @param {string} [data.date]
   * @param {string} [data.note]
   * @param {string[]} [data.tags]
   * @param {boolean} [data.recurring]
   */
  constructor(data = {}) {
    super(data);
    this.#amount      = Number(data.amount ?? 0);
    this.#description = String(data.description ?? '').trim();
    this.#category    = String(data.category ?? 'other');
    this.#type        = data.type === ExpenseType.INCOME ? ExpenseType.INCOME : ExpenseType.EXPENSE;
    this.#date        = data.date ?? new Date().toISOString().split('T')[0];
    this.#note        = String(data.note ?? '').trim();
    this.#tags        = Array.isArray(data.tags) ? [...data.tags] : [];
    this.#recurring   = Boolean(data.recurring ?? false);
  }

  /* ── Getters ── */
  get amount()      { return this.#amount; }
  get description() { return this.#description; }
  get category()    { return this.#category; }
  get type()        { return this.#type; }
  get date()        { return this.#date; }
  get note()        { return this.#note; }
  get tags()        { return [...this.#tags]; }
  get recurring()   { return this.#recurring; }
  get isIncome()    { return this.#type === ExpenseType.INCOME; }
  get isExpense()   { return this.#type === ExpenseType.EXPENSE; }

  /* ── Business logic (tell-don't-ask) ── */

  /** Returns the signed amount (negative for expenses). */
  get signedAmount() {
    return this.isIncome ? this.#amount : -this.#amount;
  }

  /** Category metadata from registry. */
  get categoryMeta() { return Categories.find(this.#category); }

  /* ── Setters (mutation → touch updatedAt) ── */

  set amount(v) {
    if (typeof v !== 'number' || v < 0) throw new ValidationError('Amount must be a non-negative number');
    this.#amount = v;
    this.touch();
  }

  set description(v) {
    this.#description = String(v).trim();
    this.touch();
  }

  set category(v) {
    this.#category = String(v);
    this.touch();
  }

  set note(v) {
    this.#note = String(v).trim();
    this.touch();
  }

  set date(v) {
    this.#date = v;
    this.touch();
  }

  /* ── Validation ── */
  validate() {
    const errors = [];
    if (this.#amount <= 0)            errors.push('Amount must be greater than zero.');
    if (this.#description && this.#description.length > 100) errors.push('Description must be 100 characters or less.');
    if (!this.#date)                  errors.push('Date is required.');
    if (!Categories.find(this.#category)) errors.push(`Unknown category: ${this.#category}.`);
    return { valid: errors.length === 0, errors };
  }

  /* ── Serialization ── */
  toJSON() {
    return {
      ...super.toJSON(),
      amount:      this.#amount,
      description: this.#description,
      category:    this.#category,
      type:        this.#type,
      date:        this.#date,
      note:        this.#note,
      tags:        [...this.#tags],
      recurring:   this.#recurring,
    };
  }

  /* ── Factory (Open/Closed: static factory without modifying constructor) ── */

  /** @param {Object} data @returns {Expense} */
  static from(data) { return new Expense(data); }

  /** Quick income factory. */
  static income(data) {
    return new Expense({ ...data, type: ExpenseType.INCOME });
  }
}

/* ============================================================
   BUDGET MODEL
   ============================================================ */

/**
 * Budget — monthly spending limit per category.
 */
class Budget extends BaseModel {
  #category;
  #limit;
  #month; // "YYYY-MM"

  constructor(data = {}) {
    super(data);
    this.#category = String(data.category ?? 'other');
    this.#limit    = Number(data.limit ?? 0);
    this.#month    = data.month ?? new Date().toISOString().substring(0, 7);
  }

  get category() { return this.#category; }
  get limit()    { return this.#limit; }
  get month()    { return this.#month; }

  set limit(v) {
    if (v < 0) throw new ValidationError('Budget limit cannot be negative');
    this.#limit = v;
    this.touch();
  }

  /**
   * Compute progress ratio given actual spending.
   * @param {number} spent
   * @returns {{ ratio: number, overBudget: boolean, remaining: number }}
   */
  progress(spent) {
    if (!this.#limit) return { ratio: 0, overBudget: false, remaining: 0 };
    const ratio      = Math.min(spent / this.#limit, 1);
    const overBudget = spent > this.#limit;
    const remaining  = Math.max(this.#limit - spent, 0);
    return { ratio, overBudget, remaining };
  }

  validate() {
    const errors = [];
    if (this.#limit < 0)                  errors.push('Limit must be non-negative.');
    if (!Categories.find(this.#category)) errors.push(`Unknown category: ${this.#category}.`);
    if (!/^\d{4}-\d{2}$/.test(this.#month)) errors.push('Month must be in YYYY-MM format.');
    return { valid: errors.length === 0, errors };
  }

  toJSON() {
    return { ...super.toJSON(), category: this.#category, limit: this.#limit, month: this.#month };
  }

  static from(data) { return new Budget(data); }
}

/* ============================================================
   USER MODEL
   ============================================================ */

/**
 * User — authentication and profile data.
 * Note: passwords are NEVER stored in plaintext here; only flag.
 */
class User extends BaseModel {
  #name;
  #email;
  #avatarInitials;
  #currency;
  #locale;

  constructor(data = {}) {
    super(data);
    this.#name           = String(data.name ?? '').trim();
    this.#email          = String(data.email ?? '').trim().toLowerCase();
    this.#avatarInitials = data.avatarInitials ?? this.#computeInitials(this.#name);
    this.#currency       = data.currency ?? 'USD';
    this.#locale         = data.locale ?? 'en-US';
  }

  get name()           { return this.#name; }
  get email()          { return this.#email; }
  get avatarInitials() { return this.#avatarInitials; }
  get currency()       { return this.#currency; }
  get locale()         { return this.#locale; }

  set name(v) {
    this.#name           = String(v).trim();
    this.#avatarInitials = this.#computeInitials(this.#name);
    this.touch();
  }

  set currency(v) { this.#currency = v; this.touch(); }

  #computeInitials(name) {
    return name
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map(w => w[0].toUpperCase())
      .join('');
  }

  validate() {
    const errors = [];
    if (!this.#name)                        errors.push('Name is required.');
    if (!this.#email)                       errors.push('Email is required.');
    if (!/\S+@\S+\.\S+/.test(this.#email)) errors.push('Invalid email address.');
    return { valid: errors.length === 0, errors };
  }

  toJSON() {
    return {
      ...super.toJSON(),
      name:           this.#name,
      email:          this.#email,
      avatarInitials: this.#avatarInitials,
      currency:       this.#currency,
      locale:         this.#locale,
    };
  }

  static from(data) { return new User(data); }
}

/* ============================================================
   SETTINGS MODEL
   ============================================================ */

class Settings extends BaseModel {
  #currency;
  #locale;
  #theme;
  #monthlyIncome;
  #notifications;
  #dateFormat;

  static #DEFAULTS = {
    currency:       'USD',
    locale:         'en-US',
    theme:          'light',
    monthlyIncome:  0,
    notifications:  true,
    dateFormat:     'MMM DD, YYYY',
  };

  constructor(data = {}) {
    super(data);
    const d = Settings.#DEFAULTS;
    this.#currency       = data.currency       ?? d.currency;
    this.#locale         = data.locale         ?? d.locale;
    this.#theme          = data.theme          ?? d.theme;
    this.#monthlyIncome  = Number(data.monthlyIncome  ?? d.monthlyIncome);
    this.#notifications  = Boolean(data.notifications ?? d.notifications);
    this.#dateFormat     = data.dateFormat     ?? d.dateFormat;
  }

  get currency()       { return this.#currency; }
  get locale()         { return this.#locale; }
  get theme()          { return this.#theme; }
  get monthlyIncome()  { return this.#monthlyIncome; }
  get notifications()  { return this.#notifications; }
  get dateFormat()     { return this.#dateFormat; }

  update(patch) {
    if (patch.currency      !== undefined) this.#currency      = patch.currency;
    if (patch.locale        !== undefined) this.#locale        = patch.locale;
    if (patch.theme         !== undefined) this.#theme         = patch.theme;
    if (patch.monthlyIncome !== undefined) this.#monthlyIncome = Number(patch.monthlyIncome);
    if (patch.notifications !== undefined) this.#notifications = Boolean(patch.notifications);
    if (patch.dateFormat    !== undefined) this.#dateFormat    = patch.dateFormat;
    this.touch();
  }

  toJSON() {
    return {
      ...super.toJSON(),
      currency:      this.#currency,
      locale:        this.#locale,
      theme:         this.#theme,
      monthlyIncome: this.#monthlyIncome,
      notifications: this.#notifications,
      dateFormat:    this.#dateFormat,
    };
  }

  static from(data) { return new Settings(data); }
}

export {
  CATEGORIES,
  Categories,
  CategoryRegistry,
  ExpenseType,
  Expense,
  Budget,
  User,
  Settings,
};
