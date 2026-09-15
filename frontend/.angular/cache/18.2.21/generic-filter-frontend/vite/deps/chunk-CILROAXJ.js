import {
  CommonModule
} from "./chunk-GUBNNMHS.js";
import {
  Component,
  Directive,
  Injectable,
  Input,
  NgModule,
  TemplateRef,
  setClassMetadata,
  ɵsetClassDebugInfo,
  ɵɵdefineComponent,
  ɵɵdefineDirective,
  ɵɵdefineInjectable,
  ɵɵdefineInjector,
  ɵɵdefineNgModule,
  ɵɵdirectiveInject,
  ɵɵprojection,
  ɵɵprojectionDef
} from "./chunk-MEHXH6ZQ.js";
import {
  Subject
} from "./chunk-4S3KYZTJ.js";

// node_modules/@primeuix/utils/dom/index.mjs
function hasClass(element, className) {
  if (element) {
    if (element.classList) return element.classList.contains(className);
    else return new RegExp("(^| )" + className + "( |$)", "gi").test(element.className);
  }
  return false;
}
function addClass(element, className) {
  if (element && className) {
    const fn = (_className) => {
      if (!hasClass(element, _className)) {
        if (element.classList) element.classList.add(_className);
        else element.className += " " + _className;
      }
    };
    [className].flat().filter(Boolean).forEach((_classNames) => _classNames.split(" ").forEach(fn));
  }
}
function removeClass(element, className) {
  if (element && className) {
    const fn = (_className) => {
      if (element.classList) element.classList.remove(_className);
      else element.className = element.className.replace(new RegExp("(^|\\b)" + _className.split(" ").join("|") + "(\\b|$)", "gi"), " ");
    };
    [className].flat().filter(Boolean).forEach((_classNames) => _classNames.split(" ").forEach(fn));
  }
}
function getViewport() {
  let win = window, d = document, e = d.documentElement, g = d.getElementsByTagName("body")[0], w = win.innerWidth || e.clientWidth || g.clientWidth, h = win.innerHeight || e.clientHeight || g.clientHeight;
  return {
    width: w,
    height: h
  };
}
function getWindowScrollLeft() {
  let doc = document.documentElement;
  return (window.pageXOffset || doc.scrollLeft) - (doc.clientLeft || 0);
}
function getWindowScrollTop() {
  let doc = document.documentElement;
  return (window.pageYOffset || doc.scrollTop) - (doc.clientTop || 0);
}
function getOuterWidth(element, margin) {
  if (element instanceof HTMLElement) {
    let width = element.offsetWidth;
    if (margin) {
      let style = getComputedStyle(element);
      width += parseFloat(style.marginLeft) + parseFloat(style.marginRight);
    }
    return width;
  }
  return 0;
}
function isElement(element) {
  return typeof HTMLElement === "object" ? element instanceof HTMLElement : element && typeof element === "object" && element !== null && element.nodeType === 1 && typeof element.nodeName === "string";
}
function toElement(element) {
  let target = element;
  if (element && typeof element === "object") {
    if (element.hasOwnProperty("current")) {
      target = element.current;
    } else if (element.hasOwnProperty("el")) {
      if (element.el.hasOwnProperty("nativeElement")) {
        target = element.el.nativeElement;
      } else {
        target = element.el;
      }
    }
  }
  return isElement(target) ? target : void 0;
}
function appendChild(element, child) {
  const target = toElement(element);
  if (target) target.appendChild(child);
  else throw new Error("Cannot append " + child + " to " + element);
}
function setAttributes(element, attributes = {}) {
  if (isElement(element)) {
    const computedStyles = (rule, value) => {
      var _a, _b;
      const styles = ((_a = element == null ? void 0 : element.$attrs) == null ? void 0 : _a[rule]) ? [(_b = element == null ? void 0 : element.$attrs) == null ? void 0 : _b[rule]] : [];
      return [value].flat().reduce((cv, v) => {
        if (v !== null && v !== void 0) {
          const type = typeof v;
          if (type === "string" || type === "number") {
            cv.push(v);
          } else if (type === "object") {
            const _cv = Array.isArray(v) ? computedStyles(rule, v) : Object.entries(v).map(([_k, _v]) => rule === "style" && (!!_v || _v === 0) ? `${_k.replace(/([a-z])([A-Z])/g, "$1-$2").toLowerCase()}:${_v}` : !!_v ? _k : void 0);
            cv = _cv.length ? cv.concat(_cv.filter((c) => !!c)) : cv;
          }
        }
        return cv;
      }, styles);
    };
    Object.entries(attributes).forEach(([key, value]) => {
      if (value !== void 0 && value !== null) {
        const matchedEvent = key.match(/^on(.+)/);
        if (matchedEvent) {
          element.addEventListener(matchedEvent[1].toLowerCase(), value);
        } else if (key === "p-bind" || key === "pBind") {
          setAttributes(element, value);
        } else {
          value = key === "class" ? [...new Set(computedStyles("class", value))].join(" ").trim() : key === "style" ? computedStyles("style", value).join(";").trim() : value;
          (element.$attrs = element.$attrs || {}) && (element.$attrs[key] = value);
          element.setAttribute(key, value);
        }
      }
    });
  }
}
function fadeIn(element, duration) {
  if (element) {
    element.style.opacity = "0";
    let last = +/* @__PURE__ */ new Date();
    let opacity = "0";
    let tick = function() {
      opacity = `${+element.style.opacity + ((/* @__PURE__ */ new Date()).getTime() - last) / duration}`;
      element.style.opacity = opacity;
      last = +/* @__PURE__ */ new Date();
      if (+opacity < 1) {
        !!window.requestAnimationFrame && requestAnimationFrame(tick) || setTimeout(tick, 16);
      }
    };
    tick();
  }
}
function find(element, selector) {
  return isElement(element) ? Array.from(element.querySelectorAll(selector)) : [];
}
function findSingle(element, selector) {
  return isElement(element) ? element.matches(selector) ? element : element.querySelector(selector) : null;
}
function focus(element, options) {
  element && document.activeElement !== element && element.focus(options);
}
function getHeight(element) {
  if (element) {
    let height = element.offsetHeight;
    let style = getComputedStyle(element);
    height -= parseFloat(style.paddingTop) + parseFloat(style.paddingBottom) + parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);
    return height;
  }
  return 0;
}
function getOffset(element) {
  if (element) {
    let rect = element.getBoundingClientRect();
    return {
      top: rect.top + (window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0),
      left: rect.left + (window.pageXOffset || document.documentElement.scrollLeft || document.body.scrollLeft || 0)
    };
  }
  return {
    top: "auto",
    left: "auto"
  };
}
function getOuterHeight(element, margin) {
  if (element) {
    let height = element.offsetHeight;
    if (margin) {
      let style = getComputedStyle(element);
      height += parseFloat(style.marginTop) + parseFloat(style.marginBottom);
    }
    return height;
  }
  return 0;
}
function getWidth(element) {
  if (element) {
    let width = element.offsetWidth;
    let style = getComputedStyle(element);
    width -= parseFloat(style.paddingLeft) + parseFloat(style.paddingRight) + parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth);
    return width;
  }
  return 0;
}
function isVisible(element) {
  return !!(element && element.offsetParent != null);
}
function isTouchDevice() {
  return "ontouchstart" in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0;
}
function remove(element) {
  var _a;
  if (element) {
    if (!("remove" in Element.prototype)) (_a = element.parentNode) == null ? void 0 : _a.removeChild(element);
    else element.remove();
  }
}
function removeChild(element, child) {
  const target = toElement(element);
  if (target) target.removeChild(child);
  else throw new Error("Cannot remove " + child + " from " + element);
}
function setAttribute(element, attribute = "", value) {
  if (isElement(element) && value !== null && value !== void 0) {
    element.setAttribute(attribute, value);
  }
}

// node_modules/@primeuix/utils/eventbus/index.mjs
function EventBus() {
  const allHandlers = /* @__PURE__ */ new Map();
  return {
    on(type, handler2) {
      let handlers = allHandlers.get(type);
      if (!handlers) handlers = [handler2];
      else handlers.push(handler2);
      allHandlers.set(type, handlers);
      return this;
    },
    off(type, handler2) {
      let handlers = allHandlers.get(type);
      if (handlers) {
        handlers.splice(handlers.indexOf(handler2) >>> 0, 1);
      }
      return this;
    },
    emit(type, evt) {
      let handlers = allHandlers.get(type);
      if (handlers) {
        handlers.slice().map((handler2) => {
          handler2(evt);
        });
      }
    },
    clear() {
      allHandlers.clear();
    }
  };
}

// node_modules/@primeuix/utils/object/index.mjs
function isEmpty(value) {
  return value === null || value === void 0 || value === "" || Array.isArray(value) && value.length === 0 || !(value instanceof Date) && typeof value === "object" && Object.keys(value).length === 0;
}
function _deepEquals(obj1, obj2, visited = /* @__PURE__ */ new WeakSet()) {
  if (obj1 === obj2) return true;
  if (!obj1 || !obj2 || typeof obj1 !== "object" || typeof obj2 !== "object") return false;
  if (visited.has(obj1) || visited.has(obj2)) return false;
  visited.add(obj1).add(obj2);
  let arrObj1 = Array.isArray(obj1), arrObj2 = Array.isArray(obj2), i, length, key;
  if (arrObj1 && arrObj2) {
    length = obj1.length;
    if (length != obj2.length) return false;
    for (i = length; i-- !== 0; ) if (!_deepEquals(obj1[i], obj2[i], visited)) return false;
    return true;
  }
  if (arrObj1 != arrObj2) return false;
  let dateObj1 = obj1 instanceof Date, dateObj2 = obj2 instanceof Date;
  if (dateObj1 != dateObj2) return false;
  if (dateObj1 && dateObj2) return obj1.getTime() == obj2.getTime();
  let regexpObj1 = obj1 instanceof RegExp, regexpObj2 = obj2 instanceof RegExp;
  if (regexpObj1 != regexpObj2) return false;
  if (regexpObj1 && regexpObj2) return obj1.toString() == obj2.toString();
  let keys = Object.keys(obj1);
  length = keys.length;
  if (length !== Object.keys(obj2).length) return false;
  for (i = length; i-- !== 0; ) if (!Object.prototype.hasOwnProperty.call(obj2, keys[i])) return false;
  for (i = length; i-- !== 0; ) {
    key = keys[i];
    if (!_deepEquals(obj1[key], obj2[key], visited)) return false;
  }
  return true;
}
function deepEquals(obj1, obj2) {
  return _deepEquals(obj1, obj2);
}
function isFunction(value) {
  return !!(value && value.constructor && value.call && value.apply);
}
function isNotEmpty(value) {
  return !isEmpty(value);
}
function resolveFieldData(data, field) {
  if (!data || !field) {
    return null;
  }
  try {
    const value = data[field];
    if (isNotEmpty(value)) return value;
  } catch (e) {
  }
  if (Object.keys(data).length) {
    if (isFunction(field)) {
      return field(data);
    } else if (field.indexOf(".") === -1) {
      return data[field];
    } else {
      let fields = field.split(".");
      let value = data;
      for (let i = 0, len = fields.length; i < len; ++i) {
        if (value == null) {
          return null;
        }
        value = value[fields[i]];
      }
      return value;
    }
  }
  return null;
}
function equals(obj1, obj2, field) {
  if (field) return resolveFieldData(obj1, field) === resolveFieldData(obj2, field);
  else return deepEquals(obj1, obj2);
}
function contains(value, list) {
  if (value != null && list && list.length) {
    for (let val of list) {
      if (equals(value, val)) return true;
    }
  }
  return false;
}
function isObject(value, empty = true) {
  return value instanceof Object && value.constructor === Object && (empty || Object.keys(value).length !== 0);
}
function resolve(obj, ...params) {
  return isFunction(obj) ? obj(...params) : obj;
}
function isString(value, empty = true) {
  return typeof value === "string" && (empty || value !== "");
}
function toFlatCase(str) {
  return isString(str) ? str.replace(/(-|_)/g, "").toLowerCase() : str;
}
function getKeyValue(obj, key = "", params = {}) {
  const fKeys = toFlatCase(key).split(".");
  const fKey = fKeys.shift();
  return fKey ? isObject(obj) ? getKeyValue(resolve(obj[Object.keys(obj).find((k) => toFlatCase(k) === fKey) || ""], params), fKeys.join("."), params) : void 0 : resolve(obj, params);
}
function isArray(value, empty = true) {
  return Array.isArray(value) && (empty || value.length !== 0);
}
function isNumber(value) {
  return isNotEmpty(value) && !isNaN(value);
}
function matchRegex(str, regex) {
  if (regex) {
    const match = regex.test(str);
    regex.lastIndex = 0;
    return match;
  }
  return false;
}
function minifyCSS(css) {
  return css ? css.replace(/\/\*(?:(?!\*\/)[\s\S])*\*\/|[\r\n\t]+/g, "").replace(/ {2,}/g, " ").replace(/ ([{:}]) /g, "$1").replace(/([;,]) /g, "$1").replace(/ !/g, "!").replace(/: /g, ":") : css;
}
function removeAccents(str) {
  const accentCheckRegex = /[\xC0-\xFF\u0100-\u017E]/;
  if (str && accentCheckRegex.test(str)) {
    const accentsMap = {
      A: /[\xC0-\xC5\u0100\u0102\u0104]/g,
      AE: /[\xC6]/g,
      C: /[\xC7\u0106\u0108\u010A\u010C]/g,
      D: /[\xD0\u010E\u0110]/g,
      E: /[\xC8-\xCB\u0112\u0114\u0116\u0118\u011A]/g,
      G: /[\u011C\u011E\u0120\u0122]/g,
      H: /[\u0124\u0126]/g,
      I: /[\xCC-\xCF\u0128\u012A\u012C\u012E\u0130]/g,
      IJ: /[\u0132]/g,
      J: /[\u0134]/g,
      K: /[\u0136]/g,
      L: /[\u0139\u013B\u013D\u013F\u0141]/g,
      N: /[\xD1\u0143\u0145\u0147\u014A]/g,
      O: /[\xD2-\xD6\xD8\u014C\u014E\u0150]/g,
      OE: /[\u0152]/g,
      R: /[\u0154\u0156\u0158]/g,
      S: /[\u015A\u015C\u015E\u0160]/g,
      T: /[\u0162\u0164\u0166]/g,
      U: /[\xD9-\xDC\u0168\u016A\u016C\u016E\u0170\u0172]/g,
      W: /[\u0174]/g,
      Y: /[\xDD\u0176\u0178]/g,
      Z: /[\u0179\u017B\u017D]/g,
      a: /[\xE0-\xE5\u0101\u0103\u0105]/g,
      ae: /[\xE6]/g,
      c: /[\xE7\u0107\u0109\u010B\u010D]/g,
      d: /[\u010F\u0111]/g,
      e: /[\xE8-\xEB\u0113\u0115\u0117\u0119\u011B]/g,
      g: /[\u011D\u011F\u0121\u0123]/g,
      i: /[\xEC-\xEF\u0129\u012B\u012D\u012F\u0131]/g,
      ij: /[\u0133]/g,
      j: /[\u0135]/g,
      k: /[\u0137,\u0138]/g,
      l: /[\u013A\u013C\u013E\u0140\u0142]/g,
      n: /[\xF1\u0144\u0146\u0148\u014B]/g,
      p: /[\xFE]/g,
      o: /[\xF2-\xF6\xF8\u014D\u014F\u0151]/g,
      oe: /[\u0153]/g,
      r: /[\u0155\u0157\u0159]/g,
      s: /[\u015B\u015D\u015F\u0161]/g,
      t: /[\u0163\u0165\u0167]/g,
      u: /[\xF9-\xFC\u0169\u016B\u016D\u016F\u0171\u0173]/g,
      w: /[\u0175]/g,
      y: /[\xFD\xFF\u0177]/g,
      z: /[\u017A\u017C\u017E]/g
    };
    for (let key in accentsMap) {
      str = str.replace(accentsMap[key], key);
    }
  }
  return str;
}
function toKebabCase(str) {
  return isString(str) ? str.replace(/(_)/g, "-").replace(/[A-Z]/g, (c, i) => i === 0 ? c : "-" + c.toLowerCase()).toLowerCase() : str;
}
function toTokenKey(str) {
  return isString(str) ? str.replace(/[A-Z]/g, (c, i) => i === 0 ? c : "." + c.toLowerCase()).toLowerCase() : str;
}

// node_modules/@primeuix/utils/uuid/index.mjs
var lastIds = {};
function uuid(prefix = "pui_id_") {
  if (!lastIds.hasOwnProperty(prefix)) {
    lastIds[prefix] = 0;
  }
  lastIds[prefix]++;
  return `${prefix}${lastIds[prefix]}`;
}

// node_modules/@primeuix/utils/zindex/index.mjs
function handler() {
  let zIndexes = [];
  const generateZIndex = (key, autoZIndex, baseZIndex = 999) => {
    const lastZIndex = getLastZIndex(key, autoZIndex, baseZIndex);
    const newZIndex = lastZIndex.value + (lastZIndex.key === key ? 0 : baseZIndex) + 1;
    zIndexes.push({
      key,
      value: newZIndex
    });
    return newZIndex;
  };
  const revertZIndex = (zIndex) => {
    zIndexes = zIndexes.filter((obj) => obj.value !== zIndex);
  };
  const getCurrentZIndex = (key, autoZIndex) => {
    return getLastZIndex(key, autoZIndex).value;
  };
  const getLastZIndex = (key, autoZIndex, baseZIndex = 0) => {
    return [...zIndexes].reverse().find((obj) => autoZIndex ? true : obj.key === key) || {
      key,
      value: baseZIndex
    };
  };
  const getZIndex = (element) => {
    return element ? parseInt(element.style.zIndex, 10) || 0 : 0;
  };
  return {
    get: getZIndex,
    set: (key, element, baseZIndex) => {
      if (element) {
        element.style.zIndex = String(generateZIndex(key, true, baseZIndex));
      }
    },
    clear: (element) => {
      if (element) {
        revertZIndex(getZIndex(element));
        element.style.zIndex = "";
      }
    },
    getCurrent: (key) => getCurrentZIndex(key, true)
  };
}
var ZIndex = handler();

// node_modules/primeng/fesm2022/primeng-api.mjs
var ConfirmEventType;
(function(ConfirmEventType2) {
  ConfirmEventType2[ConfirmEventType2["ACCEPT"] = 0] = "ACCEPT";
  ConfirmEventType2[ConfirmEventType2["REJECT"] = 1] = "REJECT";
  ConfirmEventType2[ConfirmEventType2["CANCEL"] = 2] = "CANCEL";
})(ConfirmEventType || (ConfirmEventType = {}));
var ConfirmationService = class _ConfirmationService {
  requireConfirmationSource = new Subject();
  acceptConfirmationSource = new Subject();
  requireConfirmation$ = this.requireConfirmationSource.asObservable();
  accept = this.acceptConfirmationSource.asObservable();
  /**
   * Callback to invoke on confirm.
   * @param {Confirmation} confirmation - Represents a confirmation dialog configuration.
   * @group Method
   */
  confirm(confirmation) {
    this.requireConfirmationSource.next(confirmation);
    return this;
  }
  /**
   * Closes the dialog.
   * @group Method
   */
  close() {
    this.requireConfirmationSource.next(null);
    return this;
  }
  /**
   * Accepts the dialog.
   * @group Method
   */
  onAccept() {
    this.acceptConfirmationSource.next(null);
  }
  static ɵfac = function ConfirmationService_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _ConfirmationService)();
  };
  static ɵprov = ɵɵdefineInjectable({
    token: _ConfirmationService,
    factory: _ConfirmationService.ɵfac
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ConfirmationService, [{
    type: Injectable
  }], null, null);
})();
var ContextMenuService = class _ContextMenuService {
  activeItemKeyChange = new Subject();
  activeItemKeyChange$ = this.activeItemKeyChange.asObservable();
  activeItemKey;
  changeKey(key) {
    this.activeItemKey = key;
    this.activeItemKeyChange.next(this.activeItemKey);
  }
  reset() {
    this.activeItemKey = null;
    this.activeItemKeyChange.next(this.activeItemKey);
  }
  static ɵfac = function ContextMenuService_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _ContextMenuService)();
  };
  static ɵprov = ɵɵdefineInjectable({
    token: _ContextMenuService,
    factory: _ContextMenuService.ɵfac
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ContextMenuService, [{
    type: Injectable
  }], null, null);
})();
var FilterMatchMode = class {
  static STARTS_WITH = "startsWith";
  static CONTAINS = "contains";
  static NOT_CONTAINS = "notContains";
  static ENDS_WITH = "endsWith";
  static EQUALS = "equals";
  static NOT_EQUALS = "notEquals";
  static IN = "in";
  static LESS_THAN = "lt";
  static LESS_THAN_OR_EQUAL_TO = "lte";
  static GREATER_THAN = "gt";
  static GREATER_THAN_OR_EQUAL_TO = "gte";
  static BETWEEN = "between";
  static IS = "is";
  static IS_NOT = "isNot";
  static BEFORE = "before";
  static AFTER = "after";
  static DATE_IS = "dateIs";
  static DATE_IS_NOT = "dateIsNot";
  static DATE_BEFORE = "dateBefore";
  static DATE_AFTER = "dateAfter";
};
var FilterOperator = class {
  static AND = "and";
  static OR = "or";
};
var FilterService = class _FilterService {
  filter(value, fields, filterValue, filterMatchMode, filterLocale) {
    let filteredItems = [];
    if (value) {
      for (let item of value) {
        for (let field of fields) {
          let fieldValue = resolveFieldData(item, field);
          if (this.filters[filterMatchMode](fieldValue, filterValue, filterLocale)) {
            filteredItems.push(item);
            break;
          }
        }
      }
    }
    return filteredItems;
  }
  filters = {
    startsWith: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null || filter.trim() === "") {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      let filterValue = removeAccents(filter.toString()).toLocaleLowerCase(filterLocale);
      let stringValue = removeAccents(value.toString()).toLocaleLowerCase(filterLocale);
      return stringValue.slice(0, filterValue.length) === filterValue;
    },
    contains: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null || typeof filter === "string" && filter.trim() === "") {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      let filterValue = removeAccents(filter.toString()).toLocaleLowerCase(filterLocale);
      let stringValue = removeAccents(value.toString()).toLocaleLowerCase(filterLocale);
      return stringValue.indexOf(filterValue) !== -1;
    },
    notContains: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null || typeof filter === "string" && filter.trim() === "") {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      let filterValue = removeAccents(filter.toString()).toLocaleLowerCase(filterLocale);
      let stringValue = removeAccents(value.toString()).toLocaleLowerCase(filterLocale);
      return stringValue.indexOf(filterValue) === -1;
    },
    endsWith: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null || filter.trim() === "") {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      let filterValue = removeAccents(filter.toString()).toLocaleLowerCase(filterLocale);
      let stringValue = removeAccents(value.toString()).toLocaleLowerCase(filterLocale);
      return stringValue.indexOf(filterValue, stringValue.length - filterValue.length) !== -1;
    },
    equals: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null || typeof filter === "string" && filter.trim() === "") {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      if (value.getTime && filter.getTime) return value.getTime() === filter.getTime();
      else if (value == filter) return true;
      else return removeAccents(value.toString()).toLocaleLowerCase(filterLocale) == removeAccents(filter.toString()).toLocaleLowerCase(filterLocale);
    },
    notEquals: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null || typeof filter === "string" && filter.trim() === "") {
        return false;
      }
      if (value === void 0 || value === null) {
        return true;
      }
      if (value.getTime && filter.getTime) return value.getTime() !== filter.getTime();
      else if (value == filter) return false;
      else return removeAccents(value.toString()).toLocaleLowerCase(filterLocale) != removeAccents(filter.toString()).toLocaleLowerCase(filterLocale);
    },
    in: (value, filter) => {
      if (filter === void 0 || filter === null || filter.length === 0) {
        return true;
      }
      for (let i = 0; i < filter.length; i++) {
        if (equals(value, filter[i])) {
          return true;
        }
      }
      return false;
    },
    between: (value, filter) => {
      if (filter == null || filter[0] == null || filter[1] == null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      if (value.getTime) return filter[0].getTime() <= value.getTime() && value.getTime() <= filter[1].getTime();
      else return filter[0] <= value && value <= filter[1];
    },
    lt: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      if (value.getTime && filter.getTime) return value.getTime() < filter.getTime();
      else return value < filter;
    },
    lte: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      if (value.getTime && filter.getTime) return value.getTime() <= filter.getTime();
      else return value <= filter;
    },
    gt: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      if (value.getTime && filter.getTime) return value.getTime() > filter.getTime();
      else return value > filter;
    },
    gte: (value, filter, filterLocale) => {
      if (filter === void 0 || filter === null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      if (value.getTime && filter.getTime) return value.getTime() >= filter.getTime();
      else return value >= filter;
    },
    is: (value, filter, filterLocale) => {
      return this.filters.equals(value, filter, filterLocale);
    },
    isNot: (value, filter, filterLocale) => {
      return this.filters.notEquals(value, filter, filterLocale);
    },
    before: (value, filter, filterLocale) => {
      return this.filters.lt(value, filter, filterLocale);
    },
    after: (value, filter, filterLocale) => {
      return this.filters.gt(value, filter, filterLocale);
    },
    dateIs: (value, filter) => {
      if (filter === void 0 || filter === null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      return value.toDateString() === filter.toDateString();
    },
    dateIsNot: (value, filter) => {
      if (filter === void 0 || filter === null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      return value.toDateString() !== filter.toDateString();
    },
    dateBefore: (value, filter) => {
      if (filter === void 0 || filter === null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      return value.getTime() < filter.getTime();
    },
    dateAfter: (value, filter) => {
      if (filter === void 0 || filter === null) {
        return true;
      }
      if (value === void 0 || value === null) {
        return false;
      }
      value.setHours(0, 0, 0, 0);
      return value.getTime() > filter.getTime();
    }
  };
  register(rule, fn) {
    this.filters[rule] = fn;
  }
  static ɵfac = function FilterService_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _FilterService)();
  };
  static ɵprov = ɵɵdefineInjectable({
    token: _FilterService,
    factory: _FilterService.ɵfac,
    providedIn: "root"
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(FilterService, [{
    type: Injectable,
    args: [{
      providedIn: "root"
    }]
  }], null, null);
})();
var MessageService = class _MessageService {
  messageSource = new Subject();
  clearSource = new Subject();
  messageObserver = this.messageSource.asObservable();
  clearObserver = this.clearSource.asObservable();
  /**
   * Inserts single message.
   * @param {ToastMessageOptions} message - Message to be added.
   * @group Method
   */
  add(message) {
    if (message) {
      this.messageSource.next(message);
    }
  }
  /**
   * Inserts new messages.
   * @param {Message[]} messages - Messages to be added.
   * @group Method
   */
  addAll(messages) {
    if (messages && messages.length) {
      this.messageSource.next(messages);
    }
  }
  /**
   * Clears the message with the given key.
   * @param {string} key - Key of the message to be cleared.
   * @group Method
   */
  clear(key) {
    this.clearSource.next(key || null);
  }
  static ɵfac = function MessageService_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _MessageService)();
  };
  static ɵprov = ɵɵdefineInjectable({
    token: _MessageService,
    factory: _MessageService.ɵfac
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(MessageService, [{
    type: Injectable
  }], null, null);
})();
var OverlayService = class _OverlayService {
  clickSource = new Subject();
  clickObservable = this.clickSource.asObservable();
  add(event) {
    if (event) {
      this.clickSource.next(event);
    }
  }
  static ɵfac = function OverlayService_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _OverlayService)();
  };
  static ɵprov = ɵɵdefineInjectable({
    token: _OverlayService,
    factory: _OverlayService.ɵfac,
    providedIn: "root"
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(OverlayService, [{
    type: Injectable,
    args: [{
      providedIn: "root"
    }]
  }], null, null);
})();
var PrimeIcons = class {
  static ADDRESS_BOOK = "pi pi-address-book";
  static ALIGN_CENTER = "pi pi-align-center";
  static ALIGN_JUSTIFY = "pi pi-align-justify";
  static ALIGN_LEFT = "pi pi-align-left";
  static ALIGN_RIGHT = "pi pi-align-right";
  static AMAZON = "pi pi-amazon";
  static ANDROID = "pi pi-android";
  static ANGLE_DOUBLE_DOWN = "pi pi-angle-double-down";
  static ANGLE_DOUBLE_LEFT = "pi pi-angle-double-left";
  static ANGLE_DOUBLE_RIGHT = "pi pi-angle-double-right";
  static ANGLE_DOUBLE_UP = "pi pi-angle-double-up";
  static ANGLE_DOWN = "pi pi-angle-down";
  static ANGLE_LEFT = "pi pi-angle-left";
  static ANGLE_RIGHT = "pi pi-angle-right";
  static ANGLE_UP = "pi pi-angle-up";
  static APPLE = "pi pi-apple";
  static ARROWS_ALT = "pi pi-arrows-alt";
  static ARROW_CIRCLE_DOWN = "pi pi-arrow-circle-down";
  static ARROW_CIRCLE_LEFT = "pi pi-arrow-circle-left";
  static ARROW_CIRCLE_RIGHT = "pi pi-arrow-circle-right";
  static ARROW_CIRCLE_UP = "pi pi-arrow-circle-up";
  static ARROW_DOWN = "pi pi-arrow-down";
  static ARROW_DOWN_LEFT = "pi pi-arrow-down-left";
  static ARROW_DOWN_LEFT_AND_ARROW_UP_RIGHT_TO_CENTER = "pi pi-arrow-down-left-and-arrow-up-right-to-center";
  static ARROW_DOWN_RIGHT = "pi pi-arrow-down-right";
  static ARROW_LEFT = "pi pi-arrow-left";
  static ARROW_RIGHT_ARROW_LEFT = "pi pi-arrow-right-arrow-left";
  static ARROW_RIGHT = "pi pi-arrow-right";
  static ARROW_UP = "pi pi-arrow-up";
  static ARROW_UP_LEFT = "pi pi-arrow-up-left";
  static ARROW_UP_RIGHT = "pi pi-arrow-up-right";
  static ARROW_UP_RIGHT_AND_ARROW_DOWN_LEFT_FROM_CENTER = "pi pi-arrow-up-right-and-arrow-down-left-from-center";
  static ARROWS_H = "pi pi-arrows-h";
  static ARROWS_V = "pi pi-arrows-v";
  static ASTERISK = "pi pi-asterisk";
  static AT = "pi pi-at";
  static BACKWARD = "pi pi-backward";
  static BAN = "pi pi-ban";
  static BARCODE = "pi pi-barcode";
  static BARS = "pi pi-bars";
  static BELL = "pi pi-bell";
  static BELL_SLASH = "pi pi-bell-slash";
  static BITCOIN = "pi pi-bitcoin";
  static BOLT = "pi pi-bolt";
  static BOOK = "pi pi-book";
  static BOOKMARK = "pi pi-bookmark";
  static BOOKMARK_FILL = "pi pi-bookmark-fill";
  static BOX = "pi pi-box";
  static BRIEFCASE = "pi pi-briefcase";
  static BUILDING = "pi pi-building";
  static BUILDING_COLUMNS = "pi pi-building-columns";
  static BULLSEYE = "pi pi-bullseye";
  static CALCULATOR = "pi pi-calculator";
  static CALENDAR = "pi pi-calendar";
  static CALENDAR_CLOCK = "pi pi-calendar-clock";
  static CALENDAR_MINUS = "pi pi-calendar-minus";
  static CALENDAR_PLUS = "pi pi-calendar-plus";
  static CALENDAR_TIMES = "pi pi-calendar-times";
  static CAMERA = "pi pi-camera";
  static CAR = "pi pi-car";
  static CARET_DOWN = "pi pi-caret-down";
  static CARET_LEFT = "pi pi-caret-left";
  static CARET_RIGHT = "pi pi-caret-right";
  static CARET_UP = "pi pi-caret-up";
  static CART_ARROW_DOWN = "pi pi-cart-arrow-down";
  static CART_MINUS = "pi pi-cart-minus";
  static CART_PLUS = "pi pi-cart-plus";
  static CHART_BAR = "pi pi-chart-bar";
  static CHART_LINE = "pi pi-chart-line";
  static CHART_PIE = "pi pi-chart-pie";
  static CHART_SCATTER = "pi pi-chart-scatter";
  static CHECK = "pi pi-check";
  static CHECK_CIRCLE = "pi pi-check-circle";
  static CHECK_SQUARE = "pi pi-check-square";
  static CHEVRON_CIRCLE_DOWN = "pi pi-chevron-circle-down";
  static CHEVRON_CIRCLE_LEFT = "pi pi-chevron-circle-left";
  static CHEVRON_CIRCLE_RIGHT = "pi pi-chevron-circle-right";
  static CHEVRON_CIRCLE_UP = "pi pi-chevron-circle-up";
  static CHEVRON_DOWN = "pi pi-chevron-down";
  static CHEVRON_LEFT = "pi pi-chevron-left";
  static CHEVRON_RIGHT = "pi pi-chevron-right";
  static CHEVRON_UP = "pi pi-chevron-up";
  static CIRCLE = "pi pi-circle";
  static CIRCLE_FILL = "pi pi-circle-fill";
  static CLIPBOARD = "pi pi-clipboard";
  static CLOCK = "pi pi-clock";
  static CLONE = "pi pi-clone";
  static CLOUD = "pi pi-cloud";
  static CLOUD_DOWNLOAD = "pi pi-cloud-download";
  static CLOUD_UPLOAD = "pi pi-cloud-upload";
  static CODE = "pi pi-code";
  static COG = "pi pi-cog";
  static COMMENT = "pi pi-comment";
  static COMMENTS = "pi pi-comments";
  static COMPASS = "pi pi-compass";
  static COPY = "pi pi-copy";
  static CREDIT_CARD = "pi pi-credit-card";
  static CROWN = "pi pi-crown";
  static DATABASE = "pi pi-database";
  static DESKTOP = "pi pi-desktop";
  static DELETE_LEFT = "pi pi-delete-left";
  static DIRECTIONS = "pi pi-directions";
  static DIRECTIONS_ALT = "pi pi-directions-alt";
  static DISCORD = "pi pi-discord";
  static DOLLAR = "pi pi-dollar";
  static DOWNLOAD = "pi pi-download";
  static EJECT = "pi pi-eject";
  static ELLIPSIS_H = "pi pi-ellipsis-h";
  static ELLIPSIS_V = "pi pi-ellipsis-v";
  static ENVELOPE = "pi pi-envelope";
  static EQUALS = "pi pi-equals";
  static ERASER = "pi pi-eraser";
  static ETHEREUM = "pi pi-ethereum";
  static EURO = "pi pi-euro";
  static EXCLAMATION_CIRCLE = "pi pi-exclamation-circle";
  static EXCLAMATION_TRIANGLE = "pi pi-exclamation-triangle";
  static EXPAND = "pi pi-expand";
  static EXTERNAL_LINK = "pi pi-external-link";
  static EYE = "pi pi-eye";
  static EYE_SLASH = "pi pi-eye-slash";
  static FACE_SMILE = "pi pi-face-smile";
  static FACEBOOK = "pi pi-facebook";
  static FAST_BACKWARD = "pi pi-fast-backward";
  static FAST_FORWARD = "pi pi-fast-forward";
  static FILE = "pi pi-file";
  static FILE_ARROW_UP = "pi pi-file-arrow-up";
  static FILE_CHECK = "pi pi-file-check";
  static FILE_EDIT = "pi pi-file-edit";
  static FILE_IMPORT = "pi pi-file-import";
  static FILE_PDF = "pi pi-file-pdf";
  static FILE_PLUS = "pi pi-file-plus";
  static FILE_EXCEL = "pi pi-file-excel";
  static FILE_EXPORT = "pi pi-file-export";
  static FILE_WORD = "pi pi-file-word";
  static FILTER = "pi pi-filter";
  static FILTER_FILL = "pi pi-filter-fill";
  static FILTER_SLASH = "pi pi-filter-slash";
  static FLAG = "pi pi-flag";
  static FLAG_FILL = "pi pi-flag-fill";
  static FOLDER = "pi pi-folder";
  static FOLDER_OPEN = "pi pi-folder-open";
  static FOLDER_PLUS = "pi pi-folder-plus";
  static FORWARD = "pi pi-forward";
  static GAUGE = "pi pi-gauge";
  static GIFT = "pi pi-gift";
  static GITHUB = "pi pi-github";
  static GLOBE = "pi pi-globe";
  static GOOGLE = "pi pi-google";
  static GRADUATION_CAP = "pi pi-graduation-cap";
  static HAMMER = "pi pi-hammer";
  static HASHTAG = "pi pi-hashtag";
  static HEADPHONES = "pi pi-headphones";
  static HEART = "pi pi-heart";
  static HEART_FILL = "pi pi-heart-fill";
  static HISTORY = "pi pi-history";
  static HOME = "pi pi-home";
  static HOURGLASS = "pi pi-hourglass";
  static ID_CARD = "pi pi-id-card";
  static IMAGE = "pi pi-image";
  static IMAGES = "pi pi-images";
  static INBOX = "pi pi-inbox";
  static INDIAN_RUPEE = "pi pi-indian-rupee";
  static INFO = "pi pi-info";
  static INFO_CIRCLE = "pi pi-info-circle";
  static INSTAGRAM = "pi pi-instagram";
  static KEY = "pi pi-key";
  static LANGUAGE = "pi pi-language";
  static LIGHTBULB = "pi pi-lightbulb";
  static LINK = "pi pi-link";
  static LINKEDIN = "pi pi-linkedin";
  static LIST = "pi pi-list";
  static LIST_CHECK = "pi pi-list-check";
  static LOCK = "pi pi-lock";
  static LOCK_OPEN = "pi pi-lock-open";
  static MAP = "pi pi-map";
  static MAP_MARKER = "pi pi-map-marker";
  static MARS = "pi pi-mars";
  static MEGAPHONE = "pi pi-megaphone";
  static MICROCHIP = "pi pi-microchip";
  static MICROCHIP_AI = "pi pi-microchip-ai";
  static MICROPHONE = "pi pi-microphone";
  static MICROSOFT = "pi pi-microsoft";
  static MINUS = "pi pi-minus";
  static MINUS_CIRCLE = "pi pi-minus-circle";
  static MOBILE = "pi pi-mobile";
  static MONEY_BILL = "pi pi-money-bill";
  static MOON = "pi pi-moon";
  static OBJECTS_COLUMN = "pi pi-objects-column";
  static PALETTE = "pi pi-palette";
  static PAPERCLIP = "pi pi-paperclip";
  static PAUSE = "pi pi-pause";
  static PAUSE_CIRCLE = "pi pi-pause-circle";
  static PAYPAL = "pi pi-paypal";
  static PEN_TO_SQUARE = "pi pi-pen-to-square";
  static PENCIL = "pi pi-pencil";
  static PERCENTAGE = "pi pi-percentage";
  static PHONE = "pi pi-phone";
  static PINTEREST = "pi pi-pinterest";
  static PLAY = "pi pi-play";
  static PLAY_CIRCLE = "pi pi-play-circle";
  static PLUS = "pi pi-plus";
  static PLUS_CIRCLE = "pi pi-plus-circle";
  static POUND = "pi pi-pound";
  static POWER_OFF = "pi pi-power-off";
  static PRIME = "pi pi-prime";
  static PRINT = "pi pi-print";
  static QRCODE = "pi pi-qrcode";
  static QUESTION = "pi pi-question";
  static QUESTION_CIRCLE = "pi pi-question-circle";
  static RECEIPT = "pi pi-receipt";
  static REDDIT = "pi pi-reddit";
  static REFRESH = "pi pi-refresh";
  static REPLAY = "pi pi-replay";
  static REPLY = "pi pi-reply";
  static SAVE = "pi pi-save";
  static SEARCH = "pi pi-search";
  static SEARCH_MINUS = "pi pi-search-minus";
  static SEARCH_PLUS = "pi pi-search-plus";
  static SEND = "pi pi-send";
  static SERVER = "pi pi-server";
  static SHARE_ALT = "pi pi-share-alt";
  static SHIELD = "pi pi-shield";
  static SHOP = "pi pi-shop";
  static SHOPPING_BAG = "pi pi-shopping-bag";
  static SHOPPING_CART = "pi pi-shopping-cart";
  static SIGN_IN = "pi pi-sign-in";
  static SIGN_OUT = "pi pi-sign-out";
  static SITEMAP = "pi pi-sitemap";
  static SLACK = "pi pi-slack";
  static SLIDERS_H = "pi pi-sliders-h";
  static SLIDERS_V = "pi pi-sliders-v";
  static SORT = "pi pi-sort";
  static SORT_ALPHA_DOWN = "pi pi-sort-alpha-down";
  static SORT_ALPHA_DOWN_ALT = "pi pi-sort-alpha-down-alt";
  static SORT_ALPHA_UP = "pi pi-sort-alpha-up";
  static SORT_ALPHA_UP_ALT = "pi pi-sort-alpha-up-alt";
  static SORT_ALT = "pi pi-sort-alt";
  static SORT_ALT_SLASH = "pi pi-sort-alt-slash";
  static SORT_AMOUNT_DOWN = "pi pi-sort-amount-down";
  static SORT_AMOUNT_DOWN_ALT = "pi pi-sort-amount-down-alt";
  static SORT_AMOUNT_UP = "pi pi-sort-amount-up";
  static SORT_AMOUNT_UP_ALT = "pi pi-sort-amount-up-alt";
  static SORT_DOWN = "pi pi-sort-down";
  static SORT_DOWN_FILL = "pi pi-sort-down-fill";
  static SORT_NUMERIC_DOWN = "pi pi-sort-numeric-down";
  static SORT_NUMERIC_DOWN_ALT = "pi pi-sort-numeric-down-alt";
  static SORT_NUMERIC_UP = "pi pi-sort-numeric-up";
  static SORT_NUMERIC_UP_ALT = "pi pi-sort-numeric-up-alt";
  static SORT_UP = "pi pi-sort-up";
  static SORT_UP_FILL = "pi pi-sort-up-fill";
  static SPARKLES = "pi pi-sparkles";
  static SPINNER = "pi pi-spinner";
  static SPINNER_DOTTED = "pi pi-spinner-dotted";
  static STAR = "pi pi-star";
  static STAR_FILL = "pi pi-star-fill";
  static STAR_HALF = "pi pi-star-half";
  static STAR_HALF_FILL = "pi pi-star-half-fill";
  static STEP_BACKWARD = "pi pi-step-backward";
  static STEP_BACKWARD_ALT = "pi pi-step-backward-alt";
  static STEP_FORWARD = "pi pi-step-forward";
  static STEP_FORWARD_ALT = "pi pi-step-forward-alt";
  static STOP = "pi pi-stop";
  static STOP_CIRCLE = "pi pi-stop-circle";
  static STOPWATCH = "pi pi-stopwatch";
  static SUN = "pi pi-sun";
  static SYNC = "pi pi-sync";
  static TABLE = "pi pi-table";
  static TABLET = "pi pi-tablet";
  static TAG = "pi pi-tag";
  static TAGS = "pi pi-tags";
  static TELEGRAM = "pi pi-telegram";
  static TH_LARGE = "pi pi-th-large";
  static THUMBS_DOWN = "pi pi-thumbs-down";
  static THUMBS_DOWN_FILL = "pi pi-thumbs-down-fill";
  static THUMBS_UP = "pi pi-thumbs-up";
  static THUMBS_UP_FILL = "pi pi-thumbs-up-fill";
  static THUMBTACK = "pi pi-thumbtack";
  static TICKET = "pi pi-ticket";
  static TIKTOK = "pi pi-tiktok";
  static TIMES = "pi pi-times";
  static TIMES_CIRCLE = "pi pi-times-circle";
  static TRASH = "pi pi-trash";
  static TROPHY = "pi pi-trophy";
  static TRUCK = "pi pi-truck";
  static TURKISH_LIRA = "pi pi-turkish-lira";
  static TWITCH = "pi pi-twitch";
  static TWITTER = "pi pi-twitter";
  static UNDO = "pi pi-undo";
  static UNLOCK = "pi pi-unlock";
  static UPLOAD = "pi pi-upload";
  static USER = "pi pi-user";
  static USER_EDIT = "pi pi-user-edit";
  static USER_MINUS = "pi pi-user-minus";
  static USER_PLUS = "pi pi-user-plus";
  static USERS = "pi pi-users";
  static VENUS = "pi pi-venus";
  static VERIFIED = "pi pi-verified";
  static VIDEO = "pi pi-video";
  static VIMEO = "pi pi-vimeo";
  static VOLUME_DOWN = "pi pi-volume-down";
  static VOLUME_OFF = "pi pi-volume-off";
  static VOLUME_UP = "pi pi-volume-up";
  static WALLET = "pi pi-wallet";
  static WAREHOUSE = "pi pi-warehouse";
  static WAVE_PULSE = "pi pi-wave-pulse";
  static WHATSAPP = "pi pi-whatsapp";
  static WIFI = "pi pi-wifi";
  static WINDOW_MAXIMIZE = "pi pi-window-maximize";
  static WINDOW_MINIMIZE = "pi pi-window-minimize";
  static WRENCH = "pi pi-wrench";
  static YOUTUBE = "pi pi-youtube";
};
var _c0 = ["*"];
var Header = class _Header {
  static ɵfac = function Header_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _Header)();
  };
  static ɵcmp = ɵɵdefineComponent({
    type: _Header,
    selectors: [["p-header"]],
    ngContentSelectors: _c0,
    decls: 1,
    vars: 0,
    template: function Header_Template(rf, ctx) {
      if (rf & 1) {
        ɵɵprojectionDef();
        ɵɵprojection(0);
      }
    },
    encapsulation: 2
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(Header, [{
    type: Component,
    args: [{
      selector: "p-header",
      template: "<ng-content></ng-content>",
      standalone: false
    }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && ɵsetClassDebugInfo(Header, {
    className: "Header"
  });
})();
var Footer = class _Footer {
  static ɵfac = function Footer_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _Footer)();
  };
  static ɵcmp = ɵɵdefineComponent({
    type: _Footer,
    selectors: [["p-footer"]],
    ngContentSelectors: _c0,
    decls: 1,
    vars: 0,
    template: function Footer_Template(rf, ctx) {
      if (rf & 1) {
        ɵɵprojectionDef();
        ɵɵprojection(0);
      }
    },
    encapsulation: 2
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(Footer, [{
    type: Component,
    args: [{
      selector: "p-footer",
      template: "<ng-content></ng-content>",
      standalone: false
    }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && ɵsetClassDebugInfo(Footer, {
    className: "Footer"
  });
})();
var PrimeTemplate = class _PrimeTemplate {
  template;
  type;
  name;
  constructor(template) {
    this.template = template;
  }
  getType() {
    return this.name;
  }
  static ɵfac = function PrimeTemplate_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _PrimeTemplate)(ɵɵdirectiveInject(TemplateRef));
  };
  static ɵdir = ɵɵdefineDirective({
    type: _PrimeTemplate,
    selectors: [["", "pTemplate", ""]],
    inputs: {
      type: "type",
      name: [0, "pTemplate", "name"]
    },
    standalone: true
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(PrimeTemplate, [{
    type: Directive,
    args: [{
      selector: "[pTemplate]",
      standalone: true
    }]
  }], () => [{
    type: TemplateRef
  }], {
    type: [{
      type: Input
    }],
    name: [{
      type: Input,
      args: ["pTemplate"]
    }]
  });
})();
var SharedModule = class _SharedModule {
  static ɵfac = function SharedModule_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _SharedModule)();
  };
  static ɵmod = ɵɵdefineNgModule({
    type: _SharedModule
  });
  static ɵinj = ɵɵdefineInjector({
    imports: [CommonModule]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(SharedModule, [{
    type: NgModule,
    args: [{
      imports: [CommonModule, PrimeTemplate],
      exports: [Header, Footer, PrimeTemplate],
      declarations: [Header, Footer]
    }]
  }], null, null);
})();
var TranslationKeys = class {
  static STARTS_WITH = "startsWith";
  static CONTAINS = "contains";
  static NOT_CONTAINS = "notContains";
  static ENDS_WITH = "endsWith";
  static EQUALS = "equals";
  static NOT_EQUALS = "notEquals";
  static NO_FILTER = "noFilter";
  static LT = "lt";
  static LTE = "lte";
  static GT = "gt";
  static GTE = "gte";
  static IS = "is";
  static IS_NOT = "isNot";
  static BEFORE = "before";
  static AFTER = "after";
  static CLEAR = "clear";
  static APPLY = "apply";
  static MATCH_ALL = "matchAll";
  static MATCH_ANY = "matchAny";
  static ADD_RULE = "addRule";
  static REMOVE_RULE = "removeRule";
  static ACCEPT = "accept";
  static REJECT = "reject";
  static CHOOSE = "choose";
  static UPLOAD = "upload";
  static CANCEL = "cancel";
  static PENDING = "pending";
  static FILE_SIZE_TYPES = "fileSizeTypes";
  static DAY_NAMES = "dayNames";
  static DAY_NAMES_SHORT = "dayNamesShort";
  static DAY_NAMES_MIN = "dayNamesMin";
  static MONTH_NAMES = "monthNames";
  static MONTH_NAMES_SHORT = "monthNamesShort";
  static FIRST_DAY_OF_WEEK = "firstDayOfWeek";
  static TODAY = "today";
  static WEEK_HEADER = "weekHeader";
  static WEAK = "weak";
  static MEDIUM = "medium";
  static STRONG = "strong";
  static PASSWORD_PROMPT = "passwordPrompt";
  static EMPTY_MESSAGE = "emptyMessage";
  static EMPTY_FILTER_MESSAGE = "emptyFilterMessage";
  static SHOW_FILTER_MENU = "showFilterMenu";
  static HIDE_FILTER_MENU = "hideFilterMenu";
  static SELECTION_MESSAGE = "selectionMessage";
  static ARIA = "aria";
  static SELECT_COLOR = "selectColor";
  static BROWSE_FILES = "browseFiles";
};
var TreeDragDropService = class _TreeDragDropService {
  dragStartSource = new Subject();
  dragStopSource = new Subject();
  dragStart$ = this.dragStartSource.asObservable();
  dragStop$ = this.dragStopSource.asObservable();
  startDrag(event) {
    this.dragStartSource.next(event);
  }
  stopDrag(event) {
    this.dragStopSource.next(event);
  }
  static ɵfac = function TreeDragDropService_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _TreeDragDropService)();
  };
  static ɵprov = ɵɵdefineInjectable({
    token: _TreeDragDropService,
    factory: _TreeDragDropService.ɵfac
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(TreeDragDropService, [{
    type: Injectable
  }], null, null);
})();

export {
  hasClass,
  addClass,
  removeClass,
  getViewport,
  getWindowScrollLeft,
  getWindowScrollTop,
  getOuterWidth,
  appendChild,
  setAttributes,
  fadeIn,
  find,
  findSingle,
  focus,
  getHeight,
  getOffset,
  getOuterHeight,
  getWidth,
  isVisible,
  isTouchDevice,
  remove,
  removeChild,
  setAttribute,
  EventBus,
  isEmpty,
  isNotEmpty,
  resolveFieldData,
  equals,
  contains,
  isObject,
  resolve,
  isString,
  getKeyValue,
  isArray,
  isNumber,
  matchRegex,
  minifyCSS,
  removeAccents,
  toKebabCase,
  toTokenKey,
  uuid,
  ConfirmEventType,
  ConfirmationService,
  ContextMenuService,
  FilterMatchMode,
  FilterOperator,
  FilterService,
  MessageService,
  OverlayService,
  PrimeIcons,
  Header,
  Footer,
  PrimeTemplate,
  SharedModule,
  TranslationKeys,
  TreeDragDropService
};
//# sourceMappingURL=chunk-CILROAXJ.js.map
