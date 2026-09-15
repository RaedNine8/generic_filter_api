import {
  DomHandler
} from "./chunk-5G7WYC4N.js";
import {
  Ripple,
  SpinnerIcon
} from "./chunk-YQRE7Q4U.js";
import {
  BaseComponent
} from "./chunk-ITS6ZSZJ.js";
import {
  BaseStyle
} from "./chunk-SWOMUL3X.js";
import {
  PrimeTemplate,
  SharedModule,
  addClass,
  findSingle,
  hasClass,
  isEmpty,
  isNotEmpty,
  removeClass,
  uuid
} from "./chunk-CILROAXJ.js";
import {
  CommonModule,
  DOCUMENT,
  NgClass,
  NgIf,
  NgStyle,
  NgTemplateOutlet,
  isPlatformBrowser
} from "./chunk-GUBNNMHS.js";
import {
  ChangeDetectionStrategy,
  Component,
  ContentChild,
  ContentChildren,
  Directive,
  ElementRef,
  EventEmitter,
  Injectable,
  Input,
  NgModule,
  Output,
  PLATFORM_ID,
  ViewEncapsulation$1,
  booleanAttribute,
  computed,
  contentChild,
  inject,
  input,
  numberAttribute,
  setClassMetadata,
  ɵsetClassDebugInfo,
  ɵɵInheritDefinitionFeature,
  ɵɵInputTransformsFeature,
  ɵɵNgOnChangesFeature,
  ɵɵProvidersFeature,
  ɵɵStandaloneFeature,
  ɵɵadvance,
  ɵɵattribute,
  ɵɵclassMap,
  ɵɵclassProp,
  ɵɵcontentQuery,
  ɵɵcontentQuerySignal,
  ɵɵdefineComponent,
  ɵɵdefineDirective,
  ɵɵdefineInjectable,
  ɵɵdefineInjector,
  ɵɵdefineNgModule,
  ɵɵelement,
  ɵɵelementContainer,
  ɵɵelementContainerEnd,
  ɵɵelementContainerStart,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetInheritedFactory,
  ɵɵlistener,
  ɵɵloadQuery,
  ɵɵnextContext,
  ɵɵprojection,
  ɵɵprojectionDef,
  ɵɵproperty,
  ɵɵpureFunction1,
  ɵɵqueryAdvance,
  ɵɵqueryRefresh,
  ɵɵstyleMap,
  ɵɵstyleProp,
  ɵɵtemplate,
  ɵɵtext,
  ɵɵtextInterpolate
} from "./chunk-MEHXH6ZQ.js";
import "./chunk-PEBH6BBU.js";
import "./chunk-WPM5VTLQ.js";
import "./chunk-4S3KYZTJ.js";
import "./chunk-WDMUDEB6.js";

// node_modules/primeng/fesm2022/primeng-autofocus.mjs
var AutoFocus = class _AutoFocus extends BaseComponent {
  /**
   * When present, it specifies that the component should automatically get focus on load.
   * @deprecated use [pAutoFocus]="true"
   * @group Props
   */
  autofocus = false;
  /**
   * When present, it specifies that the component should automatically get focus on load.
   * @group Props
   */
  _autofocus = false;
  focused = false;
  platformId = inject(PLATFORM_ID);
  document = inject(DOCUMENT);
  host = inject(ElementRef);
  ngAfterContentChecked() {
    if (this.autofocus === false) {
      this.host.nativeElement.removeAttribute("autofocus");
    } else {
      this.host.nativeElement.setAttribute("autofocus", true);
    }
    if (!this.focused) {
      this.autoFocus();
    }
  }
  ngAfterViewChecked() {
    if (!this.focused) {
      this.autoFocus();
    }
  }
  autoFocus() {
    if (isPlatformBrowser(this.platformId) && this._autofocus) {
      setTimeout(() => {
        const focusableElements = DomHandler.getFocusableElements(this.host?.nativeElement);
        if (focusableElements.length === 0) {
          this.host.nativeElement.focus();
        }
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        }
        this.focused = true;
      });
    }
  }
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵAutoFocus_BaseFactory;
    return function AutoFocus_Factory(__ngFactoryType__) {
      return (ɵAutoFocus_BaseFactory || (ɵAutoFocus_BaseFactory = ɵɵgetInheritedFactory(_AutoFocus)))(__ngFactoryType__ || _AutoFocus);
    };
  })();
  static ɵdir = ɵɵdefineDirective({
    type: _AutoFocus,
    selectors: [["", "pAutoFocus", ""]],
    inputs: {
      autofocus: [2, "autofocus", "autofocus", booleanAttribute],
      _autofocus: [0, "pAutoFocus", "_autofocus"]
    },
    standalone: true,
    features: [ɵɵInputTransformsFeature, ɵɵInheritDefinitionFeature]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(AutoFocus, [{
    type: Directive,
    args: [{
      selector: "[pAutoFocus]",
      standalone: true
    }]
  }], null, {
    autofocus: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    _autofocus: [{
      type: Input,
      args: ["pAutoFocus"]
    }]
  });
})();
var AutoFocusModule = class _AutoFocusModule {
  static ɵfac = function AutoFocusModule_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _AutoFocusModule)();
  };
  static ɵmod = ɵɵdefineNgModule({
    type: _AutoFocusModule
  });
  static ɵinj = ɵɵdefineInjector({});
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(AutoFocusModule, [{
    type: NgModule,
    args: [{
      imports: [AutoFocus],
      exports: [AutoFocus]
    }]
  }], null, null);
})();

// node_modules/primeng/fesm2022/primeng-badge.mjs
var theme = ({
  dt
}) => `
.p-badge {
    display: inline-flex;
    border-radius: ${dt("badge.border.radius")};
    justify-content: center;
    padding: ${dt("badge.padding")};
    background: ${dt("badge.primary.background")};
    color: ${dt("badge.primary.color")};
    font-size: ${dt("badge.font.size")};
    font-weight: ${dt("badge.font.weight")};
    min-width: ${dt("badge.min.width")};
    height: ${dt("badge.height")};
    line-height: ${dt("badge.height")};
}

.p-badge-dot {
    width: ${dt("badge.dot.size")};
    min-width: ${dt("badge.dot.size")};
    height: ${dt("badge.dot.size")};
    border-radius: 50%;
    padding: 0;
}

.p-badge-circle {
    padding: 0;
    border-radius: 50%;
}

.p-badge-secondary {
    background: ${dt("badge.secondary.background")};
    color: ${dt("badge.secondary.color")};
}

.p-badge-success {
    background: ${dt("badge.success.background")};
    color: ${dt("badge.success.color")};
}

.p-badge-info {
    background: ${dt("badge.info.background")};
    color: ${dt("badge.info.color")};
}

.p-badge-warn {
    background: ${dt("badge.warn.background")};
    color: ${dt("badge.warn.color")};
}

.p-badge-danger {
    background: ${dt("badge.danger.background")};
    color: ${dt("badge.danger.color")};
}

.p-badge-contrast {
    background: ${dt("badge.contrast.background")};
    color: ${dt("badge.contrast.color")};
}

.p-badge-sm {
    font-size: ${dt("badge.sm.font.size")};
    min-width: ${dt("badge.sm.min.width")};
    height: ${dt("badge.sm.height")};
    line-height: ${dt("badge.sm.height")};
}

.p-badge-lg {
    font-size: ${dt("badge.lg.font.size")};
    min-width: ${dt("badge.lg.min.width")};
    height: ${dt("badge.lg.height")};
    line-height: ${dt("badge.lg.height")};
}

.p-badge-xl {
    font-size: ${dt("badge.xl.font.size")};
    min-width: ${dt("badge.xl.min.width")};
    height: ${dt("badge.xl.height")};
    line-height: ${dt("badge.xl.height")};
}

/* For PrimeNG (directive)*/

.p-overlay-badge {
    position: relative;
}

.p-overlay-badge > .p-badge {
    position: absolute;
    top: 0;
    inset-inline-end: 0;
    transform: translate(50%, -50%);
    transform-origin: 100% 0;
    margin: 0;
}
`;
var classes = {
  root: ({
    props,
    instance
  }) => ["p-badge p-component", {
    "p-badge-circle": isNotEmpty(props.value) && String(props.value).length === 1,
    "p-badge-dot": isEmpty(props.value) && !instance.$slots.default,
    "p-badge-sm": props.size === "small",
    "p-badge-lg": props.size === "large",
    "p-badge-xl": props.size === "xlarge",
    "p-badge-info": props.severity === "info",
    "p-badge-success": props.severity === "success",
    "p-badge-warn": props.severity === "warn",
    "p-badge-danger": props.severity === "danger",
    "p-badge-secondary": props.severity === "secondary",
    "p-badge-contrast": props.severity === "contrast"
  }]
};
var BadgeStyle = class _BadgeStyle extends BaseStyle {
  name = "badge";
  theme = theme;
  classes = classes;
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵBadgeStyle_BaseFactory;
    return function BadgeStyle_Factory(__ngFactoryType__) {
      return (ɵBadgeStyle_BaseFactory || (ɵBadgeStyle_BaseFactory = ɵɵgetInheritedFactory(_BadgeStyle)))(__ngFactoryType__ || _BadgeStyle);
    };
  })();
  static ɵprov = ɵɵdefineInjectable({
    token: _BadgeStyle,
    factory: _BadgeStyle.ɵfac
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(BadgeStyle, [{
    type: Injectable
  }], null, null);
})();
var BadgeClasses;
(function(BadgeClasses2) {
  BadgeClasses2["root"] = "p-badge";
})(BadgeClasses || (BadgeClasses = {}));
var BadgeDirective = class _BadgeDirective extends BaseComponent {
  /**
   * When specified, disables the component.
   * @group Props
   */
  disabled;
  /**
   * Size of the badge, valid options are "large" and "xlarge".
   * @group Props
   */
  badgeSize;
  /**
   * Size of the badge, valid options are "large" and "xlarge".
   * @group Props
   * @deprecated use badgeSize instead.
   */
  set size(value) {
    this._size = value;
    console.log("size property is deprecated and will removed in v18, use badgeSize instead.");
  }
  get size() {
    return this._size;
  }
  _size;
  /**
   * Severity type of the badge.
   * @group Props
   */
  severity;
  /**
   * Value to display inside the badge.
   * @group Props
   */
  value;
  /**
   * Inline style of the element.
   * @group Props
   */
  badgeStyle;
  /**
   * Class of the element.
   * @group Props
   */
  badgeStyleClass;
  id;
  badgeEl;
  _componentStyle = inject(BadgeStyle);
  get activeElement() {
    return this.el.nativeElement.nodeName.indexOf("-") != -1 ? this.el.nativeElement.firstChild : this.el.nativeElement;
  }
  get canUpdateBadge() {
    return this.id && !this.disabled;
  }
  constructor() {
    super();
  }
  ngOnChanges({
    value,
    size,
    severity,
    disabled,
    badgeStyle,
    badgeStyleClass
  }) {
    super.ngOnChanges({
      value,
      size,
      severity,
      disabled
    });
    if (disabled) {
      this.toggleDisableState();
    }
    if (!this.canUpdateBadge) {
      return;
    }
    if (severity) {
      this.setSeverity(severity.previousValue);
    }
    if (size) {
      this.setSizeClasses();
    }
    if (value) {
      this.setValue();
    }
    if (badgeStyle || badgeStyleClass) {
      this.applyStyles();
    }
  }
  ngAfterViewInit() {
    this.id = uuid("pn_id_") + "_badge";
    this.renderBadgeContent();
  }
  setValue(element) {
    const badge = element ?? this.document.getElementById(this.id);
    if (!badge) {
      return;
    }
    if (this.value != null) {
      if (hasClass(badge, "p-badge-dot")) {
        removeClass(badge, "p-badge-dot");
      }
      if (this.value && String(this.value).length === 1) {
        addClass(badge, "p-badge-circle");
      } else {
        removeClass(badge, "p-badge-circle");
      }
    } else {
      if (!hasClass(badge, "p-badge-dot")) {
        addClass(badge, "p-badge-dot");
      }
      removeClass(badge, "p-badge-circle");
    }
    badge.innerHTML = "";
    const badgeValue = this.value != null ? String(this.value) : "";
    this.renderer.appendChild(badge, this.document.createTextNode(badgeValue));
  }
  setSizeClasses(element) {
    const badge = element ?? this.document.getElementById(this.id);
    if (!badge) {
      return;
    }
    if (this.badgeSize) {
      if (this.badgeSize === "large") {
        addClass(badge, "p-badge-lg");
        removeClass(badge, "p-badge-xl");
      }
      if (this.badgeSize === "xlarge") {
        addClass(badge, "p-badge-xl");
        removeClass(badge, "p-badge-lg");
      }
    } else if (this.size && !this.badgeSize) {
      if (this.size === "large") {
        addClass(badge, "p-badge-lg");
        removeClass(badge, "p-badge-xl");
      }
      if (this.size === "xlarge") {
        addClass(badge, "p-badge-xl");
        removeClass(badge, "p-badge-lg");
      }
    } else {
      removeClass(badge, "p-badge-lg");
      removeClass(badge, "p-badge-xl");
    }
  }
  renderBadgeContent() {
    if (this.disabled) {
      return null;
    }
    const el = this.activeElement;
    const badge = this.document.createElement("span");
    badge.id = this.id;
    badge.className = "p-badge p-component";
    this.setSeverity(null, badge);
    this.setSizeClasses(badge);
    this.setValue(badge);
    addClass(el, "p-overlay-badge");
    this.renderer.appendChild(el, badge);
    this.badgeEl = badge;
    this.applyStyles();
  }
  applyStyles() {
    if (this.badgeEl && this.badgeStyle && typeof this.badgeStyle === "object") {
      for (const [key, value] of Object.entries(this.badgeStyle)) {
        this.renderer.setStyle(this.badgeEl, key, value);
      }
    }
    if (this.badgeEl && this.badgeStyleClass) {
      this.badgeEl.classList.add(...this.badgeStyleClass.split(" "));
    }
  }
  setSeverity(oldSeverity, element) {
    const badge = element ?? this.document.getElementById(this.id);
    if (!badge) {
      return;
    }
    if (this.severity) {
      addClass(badge, `p-badge-${this.severity}`);
    }
    if (oldSeverity) {
      removeClass(badge, `p-badge-${oldSeverity}`);
    }
  }
  toggleDisableState() {
    if (!this.id) {
      return;
    }
    if (this.disabled) {
      const badge = this.activeElement?.querySelector(`#${this.id}`);
      if (badge) {
        this.renderer.removeChild(this.activeElement, badge);
      }
    } else {
      this.renderBadgeContent();
    }
  }
  static ɵfac = function BadgeDirective_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _BadgeDirective)();
  };
  static ɵdir = ɵɵdefineDirective({
    type: _BadgeDirective,
    selectors: [["", "pBadge", ""]],
    inputs: {
      disabled: [0, "badgeDisabled", "disabled"],
      badgeSize: "badgeSize",
      size: "size",
      severity: "severity",
      value: "value",
      badgeStyle: "badgeStyle",
      badgeStyleClass: "badgeStyleClass"
    },
    standalone: true,
    features: [ɵɵProvidersFeature([BadgeStyle]), ɵɵInheritDefinitionFeature, ɵɵNgOnChangesFeature]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(BadgeDirective, [{
    type: Directive,
    args: [{
      selector: "[pBadge]",
      providers: [BadgeStyle],
      standalone: true
    }]
  }], () => [], {
    disabled: [{
      type: Input,
      args: ["badgeDisabled"]
    }],
    badgeSize: [{
      type: Input
    }],
    size: [{
      type: Input
    }],
    severity: [{
      type: Input
    }],
    value: [{
      type: Input
    }],
    badgeStyle: [{
      type: Input
    }],
    badgeStyleClass: [{
      type: Input
    }]
  });
})();
var Badge = class _Badge extends BaseComponent {
  /**
   * Class of the element.
   * @group Props
   */
  styleClass = input();
  /**
   * Inline style of the element.
   * @group Props
   */
  style = input();
  /**
   * Size of the badge, valid options are "large" and "xlarge".
   * @group Props
   */
  badgeSize = input();
  /**
   * Size of the badge, valid options are "large" and "xlarge".
   * @group Props
   */
  size = input();
  /**
   * Severity type of the badge.
   * @group Props
   */
  severity = input();
  /**
   * Value to display inside the badge.
   * @group Props
   */
  value = input();
  /**
   * When specified, disables the component.
   * @group Props
   */
  badgeDisabled = input(false, {
    transform: booleanAttribute
  });
  _componentStyle = inject(BadgeStyle);
  /**
   * Computes the container class for the badge element based on its properties.
   * @returns An object representing the CSS classes to be applied to the badge container.
   */
  containerClass = computed(() => {
    let classes3 = "p-badge p-component";
    if (isNotEmpty(this.value()) && String(this.value()).length === 1) {
      classes3 += " p-badge-circle";
    }
    if (this.badgeSize() === "large") {
      classes3 += " p-badge-lg";
    } else if (this.badgeSize() === "xlarge") {
      classes3 += " p-badge-xl";
    } else if (this.badgeSize() === "small") {
      classes3 += " p-badge-sm";
    }
    if (isEmpty(this.value())) {
      classes3 += " p-badge-dot";
    }
    if (this.styleClass()) {
      classes3 += ` ${this.styleClass()}`;
    }
    if (this.severity()) {
      classes3 += ` p-badge-${this.severity()}`;
    }
    return classes3;
  });
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵBadge_BaseFactory;
    return function Badge_Factory(__ngFactoryType__) {
      return (ɵBadge_BaseFactory || (ɵBadge_BaseFactory = ɵɵgetInheritedFactory(_Badge)))(__ngFactoryType__ || _Badge);
    };
  })();
  static ɵcmp = ɵɵdefineComponent({
    type: _Badge,
    selectors: [["p-badge"]],
    hostVars: 6,
    hostBindings: function Badge_HostBindings(rf, ctx) {
      if (rf & 2) {
        ɵɵstyleMap(ctx.style());
        ɵɵclassMap(ctx.containerClass());
        ɵɵstyleProp("display", ctx.badgeDisabled() && "none");
      }
    },
    inputs: {
      styleClass: [1, "styleClass"],
      style: [1, "style"],
      badgeSize: [1, "badgeSize"],
      size: [1, "size"],
      severity: [1, "severity"],
      value: [1, "value"],
      badgeDisabled: [1, "badgeDisabled"]
    },
    standalone: true,
    features: [ɵɵProvidersFeature([BadgeStyle]), ɵɵInheritDefinitionFeature, ɵɵStandaloneFeature],
    decls: 1,
    vars: 1,
    template: function Badge_Template(rf, ctx) {
      if (rf & 1) {
        ɵɵtext(0);
      }
      if (rf & 2) {
        ɵɵtextInterpolate(ctx.value());
      }
    },
    dependencies: [CommonModule, SharedModule],
    encapsulation: 2,
    changeDetection: 0
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(Badge, [{
    type: Component,
    args: [{
      selector: "p-badge",
      template: `{{ value() }}`,
      standalone: true,
      imports: [CommonModule, SharedModule],
      changeDetection: ChangeDetectionStrategy.OnPush,
      encapsulation: ViewEncapsulation$1.None,
      providers: [BadgeStyle],
      host: {
        "[class]": "containerClass()",
        "[style.display]": 'badgeDisabled() && "none"',
        "[style]": "style()"
      }
    }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && ɵsetClassDebugInfo(Badge, {
    className: "Badge"
  });
})();
var BadgeModule = class _BadgeModule {
  static ɵfac = function BadgeModule_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _BadgeModule)();
  };
  static ɵmod = ɵɵdefineNgModule({
    type: _BadgeModule
  });
  static ɵinj = ɵɵdefineInjector({
    imports: [Badge, SharedModule, SharedModule]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(BadgeModule, [{
    type: NgModule,
    args: [{
      imports: [Badge, BadgeDirective, SharedModule],
      exports: [Badge, BadgeDirective, SharedModule]
    }]
  }], null, null);
})();

// node_modules/primeng/fesm2022/primeng-button.mjs
var theme2 = ({
  dt
}) => `
.p-button {
    display: inline-flex;
    cursor: pointer;
    user-select: none;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
    color: ${dt("button.primary.color")};
    background: ${dt("button.primary.background")};
    border: 1px solid ${dt("button.primary.border.color")};
    padding-block: ${dt("button.padding.y")};
    padding-inline: ${dt("button.padding.x")};
    font-size: 1rem;
    font-family: inherit;
    font-feature-settings: inherit;
    transition: background ${dt("button.transition.duration")}, color ${dt("button.transition.duration")}, border-color ${dt("button.transition.duration")},
            outline-color ${dt("button.transition.duration")}, box-shadow ${dt("button.transition.duration")};
    border-radius: ${dt("button.border.radius")};
    outline-color: transparent;
    gap: ${dt("button.gap")};
}

.p-button:disabled {
    cursor: default;
}

.p-button-icon-right {
    order: 1;
}

.p-button-icon-right:dir(rtl) {
    order: -1;
}

.p-button:not(.p-button-vertical) .p-button-icon:not(.p-button-icon-right):dir(rtl) {
    order: 1;
}

.p-button-icon-bottom {
    order: 2;
}

.p-button-icon-only {
    width: ${dt("button.icon.only.width")};
    padding-inline-start: 0;
    padding-inline-end: 0;
    gap: 0;
}

.p-button-icon-only.p-button-rounded {
    border-radius: 50%;
    height: ${dt("button.icon.only.width")};
}

.p-button-icon-only .p-button-label {
    visibility: hidden;
    width: 0;
}

.p-button-sm {
    font-size: ${dt("button.sm.font.size")};
    padding-block: ${dt("button.sm.padding.y")};
    padding-inline: ${dt("button.sm.padding.x")};
}

.p-button-sm .p-button-icon {
    font-size: ${dt("button.sm.font.size")};
}

.p-button-lg {
    font-size: ${dt("button.lg.font.size")};
    padding-block: ${dt("button.lg.padding.y")};
    padding-inline: ${dt("button.lg.padding.x")};
}

.p-button-lg .p-button-icon {
    font-size: ${dt("button.lg.font.size")};
}

.p-button-vertical {
    flex-direction: column;
}

.p-button-label {
    font-weight: ${dt("button.label.font.weight")};
}

.p-button-fluid {
    width: 100%;
}

.p-button-fluid.p-button-icon-only {
    width: ${dt("button.icon.only.width")};
}

.p-button:not(:disabled):hover {
    background: ${dt("button.primary.hover.background")};
    border: 1px solid ${dt("button.primary.hover.border.color")};
    color: ${dt("button.primary.hover.color")};
}

.p-button:not(:disabled):active {
    background: ${dt("button.primary.active.background")};
    border: 1px solid ${dt("button.primary.active.border.color")};
    color: ${dt("button.primary.active.color")};
}

.p-button:focus-visible {
    box-shadow: ${dt("button.primary.focus.ring.shadow")};
    outline: ${dt("button.focus.ring.width")} ${dt("button.focus.ring.style")} ${dt("button.primary.focus.ring.color")};
    outline-offset: ${dt("button.focus.ring.offset")};
}

.p-button .p-badge {
    min-width: ${dt("button.badge.size")};
    height: ${dt("button.badge.size")};
    line-height: ${dt("button.badge.size")};
}

.p-button-raised {
    box-shadow: ${dt("button.raised.shadow")};
}

.p-button-rounded {
    border-radius: ${dt("button.rounded.border.radius")};
}

.p-button-secondary {
    background: ${dt("button.secondary.background")};
    border: 1px solid ${dt("button.secondary.border.color")};
    color: ${dt("button.secondary.color")};
}

.p-button-secondary:not(:disabled):hover {
    background: ${dt("button.secondary.hover.background")};
    border: 1px solid ${dt("button.secondary.hover.border.color")};
    color: ${dt("button.secondary.hover.color")};
}

.p-button-secondary:not(:disabled):active {
    background: ${dt("button.secondary.active.background")};
    border: 1px solid ${dt("button.secondary.active.border.color")};
    color: ${dt("button.secondary.active.color")};
}

.p-button-secondary:focus-visible {
    outline-color: ${dt("button.secondary.focus.ring.color")};
    box-shadow: ${dt("button.secondary.focus.ring.shadow")};
}

.p-button-success {
    background: ${dt("button.success.background")};
    border: 1px solid ${dt("button.success.border.color")};
    color: ${dt("button.success.color")};
}

.p-button-success:not(:disabled):hover {
    background: ${dt("button.success.hover.background")};
    border: 1px solid ${dt("button.success.hover.border.color")};
    color: ${dt("button.success.hover.color")};
}

.p-button-success:not(:disabled):active {
    background: ${dt("button.success.active.background")};
    border: 1px solid ${dt("button.success.active.border.color")};
    color: ${dt("button.success.active.color")};
}

.p-button-success:focus-visible {
    outline-color: ${dt("button.success.focus.ring.color")};
    box-shadow: ${dt("button.success.focus.ring.shadow")};
}

.p-button-info {
    background: ${dt("button.info.background")};
    border: 1px solid ${dt("button.info.border.color")};
    color: ${dt("button.info.color")};
}

.p-button-info:not(:disabled):hover {
    background: ${dt("button.info.hover.background")};
    border: 1px solid ${dt("button.info.hover.border.color")};
    color: ${dt("button.info.hover.color")};
}

.p-button-info:not(:disabled):active {
    background: ${dt("button.info.active.background")};
    border: 1px solid ${dt("button.info.active.border.color")};
    color: ${dt("button.info.active.color")};
}

.p-button-info:focus-visible {
    outline-color: ${dt("button.info.focus.ring.color")};
    box-shadow: ${dt("button.info.focus.ring.shadow")};
}

.p-button-warn {
    background: ${dt("button.warn.background")};
    border: 1px solid ${dt("button.warn.border.color")};
    color: ${dt("button.warn.color")};
}

.p-button-warn:not(:disabled):hover {
    background: ${dt("button.warn.hover.background")};
    border: 1px solid ${dt("button.warn.hover.border.color")};
    color: ${dt("button.warn.hover.color")};
}

.p-button-warn:not(:disabled):active {
    background: ${dt("button.warn.active.background")};
    border: 1px solid ${dt("button.warn.active.border.color")};
    color: ${dt("button.warn.active.color")};
}

.p-button-warn:focus-visible {
    outline-color: ${dt("button.warn.focus.ring.color")};
    box-shadow: ${dt("button.warn.focus.ring.shadow")};
}

.p-button-help {
    background: ${dt("button.help.background")};
    border: 1px solid ${dt("button.help.border.color")};
    color: ${dt("button.help.color")};
}

.p-button-help:not(:disabled):hover {
    background: ${dt("button.help.hover.background")};
    border: 1px solid ${dt("button.help.hover.border.color")};
    color: ${dt("button.help.hover.color")};
}

.p-button-help:not(:disabled):active {
    background: ${dt("button.help.active.background")};
    border: 1px solid ${dt("button.help.active.border.color")};
    color: ${dt("button.help.active.color")};
}

.p-button-help:focus-visible {
    outline-color: ${dt("button.help.focus.ring.color")};
    box-shadow: ${dt("button.help.focus.ring.shadow")};
}

.p-button-danger {
    background: ${dt("button.danger.background")};
    border: 1px solid ${dt("button.danger.border.color")};
    color: ${dt("button.danger.color")};
}

.p-button-danger:not(:disabled):hover {
    background: ${dt("button.danger.hover.background")};
    border: 1px solid ${dt("button.danger.hover.border.color")};
    color: ${dt("button.danger.hover.color")};
}

.p-button-danger:not(:disabled):active {
    background: ${dt("button.danger.active.background")};
    border: 1px solid ${dt("button.danger.active.border.color")};
    color: ${dt("button.danger.active.color")};
}

.p-button-danger:focus-visible {
    outline-color: ${dt("button.danger.focus.ring.color")};
    box-shadow: ${dt("button.danger.focus.ring.shadow")};
}

.p-button-contrast {
    background: ${dt("button.contrast.background")};
    border: 1px solid ${dt("button.contrast.border.color")};
    color: ${dt("button.contrast.color")};
}

.p-button-contrast:not(:disabled):hover {
    background: ${dt("button.contrast.hover.background")};
    border: 1px solid ${dt("button.contrast.hover.border.color")};
    color: ${dt("button.contrast.hover.color")};
}

.p-button-contrast:not(:disabled):active {
    background: ${dt("button.contrast.active.background")};
    border: 1px solid ${dt("button.contrast.active.border.color")};
    color: ${dt("button.contrast.active.color")};
}

.p-button-contrast:focus-visible {
    outline-color: ${dt("button.contrast.focus.ring.color")};
    box-shadow: ${dt("button.contrast.focus.ring.shadow")};
}

.p-button-outlined {
    background: transparent;
    border-color: ${dt("button.outlined.primary.border.color")};
    color: ${dt("button.outlined.primary.color")};
}

.p-button-outlined:not(:disabled):hover {
    background: ${dt("button.outlined.primary.hover.background")};
    border-color: ${dt("button.outlined.primary.border.color")};
    color: ${dt("button.outlined.primary.color")};
}

.p-button-outlined:not(:disabled):active {
    background: ${dt("button.outlined.primary.active.background")};
    border-color: ${dt("button.outlined.primary.border.color")};
    color: ${dt("button.outlined.primary.color")};
}

.p-button-outlined.p-button-secondary {
    border-color: ${dt("button.outlined.secondary.border.color")};
    color: ${dt("button.outlined.secondary.color")};
}

.p-button-outlined.p-button-secondary:not(:disabled):hover {
    background: ${dt("button.outlined.secondary.hover.background")};
    border-color: ${dt("button.outlined.secondary.border.color")};
    color: ${dt("button.outlined.secondary.color")};
}

.p-button-outlined.p-button-secondary:not(:disabled):active {
    background: ${dt("button.outlined.secondary.active.background")};
    border-color: ${dt("button.outlined.secondary.border.color")};
    color: ${dt("button.outlined.secondary.color")};
}

.p-button-outlined.p-button-success {
    border-color: ${dt("button.outlined.success.border.color")};
    color: ${dt("button.outlined.success.color")};
}

.p-button-outlined.p-button-success:not(:disabled):hover {
    background: ${dt("button.outlined.success.hover.background")};
    border-color: ${dt("button.outlined.success.border.color")};
    color: ${dt("button.outlined.success.color")};
}

.p-button-outlined.p-button-success:not(:disabled):active {
    background: ${dt("button.outlined.success.active.background")};
    border-color: ${dt("button.outlined.success.border.color")};
    color: ${dt("button.outlined.success.color")};
}

.p-button-outlined.p-button-info {
    border-color: ${dt("button.outlined.info.border.color")};
    color: ${dt("button.outlined.info.color")};
}

.p-button-outlined.p-button-info:not(:disabled):hover {
    background: ${dt("button.outlined.info.hover.background")};
    border-color: ${dt("button.outlined.info.border.color")};
    color: ${dt("button.outlined.info.color")};
}

.p-button-outlined.p-button-info:not(:disabled):active {
    background: ${dt("button.outlined.info.active.background")};
    border-color: ${dt("button.outlined.info.border.color")};
    color: ${dt("button.outlined.info.color")};
}

.p-button-outlined.p-button-warn {
    border-color: ${dt("button.outlined.warn.border.color")};
    color: ${dt("button.outlined.warn.color")};
}

.p-button-outlined.p-button-warn:not(:disabled):hover {
    background: ${dt("button.outlined.warn.hover.background")};
    border-color: ${dt("button.outlined.warn.border.color")};
    color: ${dt("button.outlined.warn.color")};
}

.p-button-outlined.p-button-warn:not(:disabled):active {
    background: ${dt("button.outlined.warn.active.background")};
    border-color: ${dt("button.outlined.warn.border.color")};
    color: ${dt("button.outlined.warn.color")};
}

.p-button-outlined.p-button-help {
    border-color: ${dt("button.outlined.help.border.color")};
    color: ${dt("button.outlined.help.color")};
}

.p-button-outlined.p-button-help:not(:disabled):hover {
    background: ${dt("button.outlined.help.hover.background")};
    border-color: ${dt("button.outlined.help.border.color")};
    color: ${dt("button.outlined.help.color")};
}

.p-button-outlined.p-button-help:not(:disabled):active {
    background: ${dt("button.outlined.help.active.background")};
    border-color: ${dt("button.outlined.help.border.color")};
    color: ${dt("button.outlined.help.color")};
}

.p-button-outlined.p-button-danger {
    border-color: ${dt("button.outlined.danger.border.color")};
    color: ${dt("button.outlined.danger.color")};
}

.p-button-outlined.p-button-danger:not(:disabled):hover {
    background: ${dt("button.outlined.danger.hover.background")};
    border-color: ${dt("button.outlined.danger.border.color")};
    color: ${dt("button.outlined.danger.color")};
}

.p-button-outlined.p-button-danger:not(:disabled):active {
    background: ${dt("button.outlined.danger.active.background")};
    border-color: ${dt("button.outlined.danger.border.color")};
    color: ${dt("button.outlined.danger.color")};
}

.p-button-outlined.p-button-contrast {
    border-color: ${dt("button.outlined.contrast.border.color")};
    color: ${dt("button.outlined.contrast.color")};
}

.p-button-outlined.p-button-contrast:not(:disabled):hover {
    background: ${dt("button.outlined.contrast.hover.background")};
    border-color: ${dt("button.outlined.contrast.border.color")};
    color: ${dt("button.outlined.contrast.color")};
}

.p-button-outlined.p-button-contrast:not(:disabled):active {
    background: ${dt("button.outlined.contrast.active.background")};
    border-color: ${dt("button.outlined.contrast.border.color")};
    color: ${dt("button.outlined.contrast.color")};
}

.p-button-outlined.p-button-plain {
    border-color: ${dt("button.outlined.plain.border.color")};
    color: ${dt("button.outlined.plain.color")};
}

.p-button-outlined.p-button-plain:not(:disabled):hover {
    background: ${dt("button.outlined.plain.hover.background")};
    border-color: ${dt("button.outlined.plain.border.color")};
    color: ${dt("button.outlined.plain.color")};
}

.p-button-outlined.p-button-plain:not(:disabled):active {
    background: ${dt("button.outlined.plain.active.background")};
    border-color: ${dt("button.outlined.plain.border.color")};
    color: ${dt("button.outlined.plain.color")};
}

.p-button-text {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.primary.color")};
}

.p-button-text:not(:disabled):hover {
    background: ${dt("button.text.primary.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.primary.color")};
}

.p-button-text:not(:disabled):active {
    background: ${dt("button.text.primary.active.background")};
    border-color: transparent;
    color: ${dt("button.text.primary.color")};
}

.p-button-text.p-button-secondary {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.secondary.color")};
}

.p-button-text.p-button-secondary:not(:disabled):hover {
    background: ${dt("button.text.secondary.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.secondary.color")};
}

.p-button-text.p-button-secondary:not(:disabled):active {
    background: ${dt("button.text.secondary.active.background")};
    border-color: transparent;
    color: ${dt("button.text.secondary.color")};
}

.p-button-text.p-button-success {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.success.color")};
}

.p-button-text.p-button-success:not(:disabled):hover {
    background: ${dt("button.text.success.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.success.color")};
}

.p-button-text.p-button-success:not(:disabled):active {
    background: ${dt("button.text.success.active.background")};
    border-color: transparent;
    color: ${dt("button.text.success.color")};
}

.p-button-text.p-button-info {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.info.color")};
}

.p-button-text.p-button-info:not(:disabled):hover {
    background: ${dt("button.text.info.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.info.color")};
}

.p-button-text.p-button-info:not(:disabled):active {
    background: ${dt("button.text.info.active.background")};
    border-color: transparent;
    color: ${dt("button.text.info.color")};
}

.p-button-text.p-button-warn {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.warn.color")};
}

.p-button-text.p-button-warn:not(:disabled):hover {
    background: ${dt("button.text.warn.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.warn.color")};
}

.p-button-text.p-button-warn:not(:disabled):active {
    background: ${dt("button.text.warn.active.background")};
    border-color: transparent;
    color: ${dt("button.text.warn.color")};
}

.p-button-text.p-button-help {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.help.color")};
}

.p-button-text.p-button-help:not(:disabled):hover {
    background: ${dt("button.text.help.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.help.color")};
}

.p-button-text.p-button-help:not(:disabled):active {
    background: ${dt("button.text.help.active.background")};
    border-color: transparent;
    color: ${dt("button.text.help.color")};
}

.p-button-text.p-button-danger {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.danger.color")};
}

.p-button-text.p-button-danger:not(:disabled):hover {
    background: ${dt("button.text.danger.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.danger.color")};
}

.p-button-text.p-button-danger:not(:disabled):active {
    background: ${dt("button.text.danger.active.background")};
    border-color: transparent;
    color: ${dt("button.text.danger.color")};
}

.p-button-text.p-button-plain {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.plain.color")};
}

.p-button-text.p-button-plain:not(:disabled):hover {
    background: ${dt("button.text.plain.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.plain.color")};
}

.p-button-text.p-button-plain:not(:disabled):active {
    background: ${dt("button.text.plain.active.background")};
    border-color: transparent;
    color: ${dt("button.text.plain.color")};
}

.p-button-text.p-button-contrast {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.text.contrast.color")};
}

.p-button-text.p-button-contrast:not(:disabled):hover {
    background: ${dt("button.text.contrast.hover.background")};
    border-color: transparent;
    color: ${dt("button.text.contrast.color")};
}

.p-button-text.p-button-contrast:not(:disabled):active {
    background: ${dt("button.text.contrast.active.background")};
    border-color: transparent;
    color: ${dt("button.text.contrast.color")};
}

.p-button-link {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.link.color")};
}

.p-button-link:not(:disabled):hover {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.link.hover.color")};
}

.p-button-link:not(:disabled):hover .p-button-label {
    text-decoration: underline;
}

.p-button-link:not(:disabled):active {
    background: transparent;
    border-color: transparent;
    color: ${dt("button.link.active.color")};
}

/* For PrimeNG */
.p-button-icon-right {
    order: 1;
}

p-button[iconpos='right'] spinnericon {
    order: 1;
}
`;
var classes2 = {
  root: ({
    instance,
    props
  }) => ["p-button p-component", {
    "p-button-icon-only": instance.hasIcon && !props.label && !props.badge,
    "p-button-vertical": (props.iconPos === "top" || props.iconPos === "bottom") && props.label,
    "p-button-loading": props.loading,
    "p-button-link": props.link,
    [`p-button-${props.severity}`]: props.severity,
    "p-button-raised": props.raised,
    "p-button-rounded": props.rounded,
    "p-button-text": props.text,
    "p-button-outlined": props.outlined,
    "p-button-sm": props.size === "small",
    "p-button-lg": props.size === "large",
    "p-button-plain": props.plain,
    "p-button-fluid": props.fluid
  }],
  loadingIcon: "p-button-loading-icon",
  icon: ({
    props
  }) => ["p-button-icon", {
    [`p-button-icon-${props.iconPos}`]: props.label
  }],
  label: "p-button-label"
};
var ButtonStyle = class _ButtonStyle extends BaseStyle {
  name = "button";
  theme = theme2;
  classes = classes2;
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵButtonStyle_BaseFactory;
    return function ButtonStyle_Factory(__ngFactoryType__) {
      return (ɵButtonStyle_BaseFactory || (ɵButtonStyle_BaseFactory = ɵɵgetInheritedFactory(_ButtonStyle)))(__ngFactoryType__ || _ButtonStyle);
    };
  })();
  static ɵprov = ɵɵdefineInjectable({
    token: _ButtonStyle,
    factory: _ButtonStyle.ɵfac
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ButtonStyle, [{
    type: Injectable
  }], null, null);
})();
var ButtonClasses;
(function(ButtonClasses2) {
  ButtonClasses2["root"] = "p-button";
  ButtonClasses2["loadingIcon"] = "p-button-loading-icon";
  ButtonClasses2["icon"] = "p-button-icon";
  ButtonClasses2["label"] = "p-button-label";
})(ButtonClasses || (ButtonClasses = {}));
var _c0 = ["content"];
var _c1 = ["loading"];
var _c2 = ["icon"];
var _c3 = ["*"];
var _c4 = (a0) => ({
  class: a0
});
function Button_ng_container_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainer(0);
  }
}
function Button_ng_container_3_ng_container_1_span_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "span", 8);
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(3);
    ɵɵproperty("ngClass", ctx_r0.iconClass());
    ɵɵattribute("aria-hidden", true)("data-pc-section", "loadingicon");
  }
}
function Button_ng_container_3_ng_container_1_SpinnerIcon_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "SpinnerIcon", 9);
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(3);
    ɵɵproperty("styleClass", ctx_r0.spinnerIconClass())("spin", true);
    ɵɵattribute("aria-hidden", true)("data-pc-section", "loadingicon");
  }
}
function Button_ng_container_3_ng_container_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, Button_ng_container_3_ng_container_1_span_1_Template, 1, 3, "span", 6)(2, Button_ng_container_3_ng_container_1_SpinnerIcon_2_Template, 1, 4, "SpinnerIcon", 7);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r0.loadingIcon);
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r0.loadingIcon);
  }
}
function Button_ng_container_3_2_ng_template_0_Template(rf, ctx) {
}
function Button_ng_container_3_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Button_ng_container_3_2_ng_template_0_Template, 0, 0, "ng-template", 10);
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵproperty("ngIf", ctx_r0.loadingIconTemplate || ctx_r0._loadingIconTemplate);
  }
}
function Button_ng_container_3_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, Button_ng_container_3_ng_container_1_Template, 3, 2, "ng-container", 2)(2, Button_ng_container_3_2_Template, 1, 1, null, 5);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r0.loadingIconTemplate && !ctx_r0._loadingIconTemplate);
    ɵɵadvance();
    ɵɵproperty("ngTemplateOutlet", ctx_r0.loadingIconTemplate || ctx_r0._loadingIconTemplate)("ngTemplateOutletContext", ɵɵpureFunction1(3, _c4, ctx_r0.iconClass()));
  }
}
function Button_ng_container_4_span_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "span", 8);
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵclassMap(ctx_r0.icon);
    ɵɵproperty("ngClass", ctx_r0.iconClass());
    ɵɵattribute("data-pc-section", "icon");
  }
}
function Button_ng_container_4_2_ng_template_0_Template(rf, ctx) {
}
function Button_ng_container_4_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Button_ng_container_4_2_ng_template_0_Template, 0, 0, "ng-template", 10);
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵproperty("ngIf", !ctx_r0.icon && (ctx_r0.iconTemplate || ctx_r0._iconTemplate));
  }
}
function Button_ng_container_4_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, Button_ng_container_4_span_1_Template, 1, 4, "span", 11)(2, Button_ng_container_4_2_Template, 1, 1, null, 5);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r0.icon && !ctx_r0.iconTemplate && !ctx_r0._iconTemplate);
    ɵɵadvance();
    ɵɵproperty("ngTemplateOutlet", ctx_r0.iconTemplate || ctx_r0._iconTemplate)("ngTemplateOutletContext", ɵɵpureFunction1(3, _c4, ctx_r0.iconClass()));
  }
}
function Button_span_5_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "span", 12);
    ɵɵtext(1);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵattribute("aria-hidden", ctx_r0.icon && !ctx_r0.label)("data-pc-section", "label");
    ɵɵadvance();
    ɵɵtextInterpolate(ctx_r0.label);
  }
}
function Button_p_badge_6_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "p-badge", 13);
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵproperty("value", ctx_r0.badge)("severity", ctx_r0.badgeSeverity);
  }
}
var INTERNAL_BUTTON_CLASSES = {
  button: "p-button",
  component: "p-component",
  iconOnly: "p-button-icon-only",
  disabled: "p-disabled",
  loading: "p-button-loading",
  labelOnly: "p-button-loading-label-only"
};
var ButtonLabel = class _ButtonLabel extends BaseComponent {
  _componentStyle = inject(ButtonStyle);
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵButtonLabel_BaseFactory;
    return function ButtonLabel_Factory(__ngFactoryType__) {
      return (ɵButtonLabel_BaseFactory || (ɵButtonLabel_BaseFactory = ɵɵgetInheritedFactory(_ButtonLabel)))(__ngFactoryType__ || _ButtonLabel);
    };
  })();
  static ɵdir = ɵɵdefineDirective({
    type: _ButtonLabel,
    selectors: [["", "pButtonLabel", ""]],
    hostVars: 2,
    hostBindings: function ButtonLabel_HostBindings(rf, ctx) {
      if (rf & 2) {
        ɵɵclassProp("p-button-label", true);
      }
    },
    standalone: true,
    features: [ɵɵProvidersFeature([ButtonStyle]), ɵɵInheritDefinitionFeature]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ButtonLabel, [{
    type: Directive,
    args: [{
      selector: "[pButtonLabel]",
      providers: [ButtonStyle],
      standalone: true,
      host: {
        "[class.p-button-label]": "true"
      }
    }]
  }], null, null);
})();
var ButtonIcon = class _ButtonIcon extends BaseComponent {
  _componentStyle = inject(ButtonStyle);
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵButtonIcon_BaseFactory;
    return function ButtonIcon_Factory(__ngFactoryType__) {
      return (ɵButtonIcon_BaseFactory || (ɵButtonIcon_BaseFactory = ɵɵgetInheritedFactory(_ButtonIcon)))(__ngFactoryType__ || _ButtonIcon);
    };
  })();
  static ɵdir = ɵɵdefineDirective({
    type: _ButtonIcon,
    selectors: [["", "pButtonIcon", ""]],
    hostVars: 2,
    hostBindings: function ButtonIcon_HostBindings(rf, ctx) {
      if (rf & 2) {
        ɵɵclassProp("p-button-icon", true);
      }
    },
    standalone: true,
    features: [ɵɵProvidersFeature([ButtonStyle]), ɵɵInheritDefinitionFeature]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ButtonIcon, [{
    type: Directive,
    args: [{
      selector: "[pButtonIcon]",
      providers: [ButtonStyle],
      standalone: true,
      host: {
        "[class.p-button-icon]": "true"
      }
    }]
  }], null, null);
})();
var ButtonDirective = class _ButtonDirective extends BaseComponent {
  /**
   * Position of the icon.
   * @deprecated utilize pButtonIcon and pButtonLabel directives.
   * @group Props
   */
  iconPos = "left";
  /**
   * Uses to pass attributes to the loading icon's DOM element.
   * @deprecated utilize pButonIcon instead.
   * @group Props
   */
  loadingIcon;
  set label(val) {
    this._label = val;
    if (this.initialized) {
      this.updateLabel();
      this.updateIcon();
      this.setStyleClass();
    }
  }
  set icon(val) {
    this._icon = val;
    if (this.initialized) {
      this.updateIcon();
      this.setStyleClass();
    }
  }
  /**
   * Whether the button is in loading state.
   * @group Props
   */
  get loading() {
    return this._loading;
  }
  set loading(val) {
    this._loading = val;
    if (this.initialized) {
      this.updateIcon();
      this.setStyleClass();
    }
  }
  _buttonProps;
  iconSignal = contentChild(ButtonIcon);
  labelSignal = contentChild(ButtonLabel);
  isIconOnly = computed(() => !!(!this.labelSignal() && this.iconSignal()));
  set buttonProps(val) {
    this._buttonProps = val;
    if (val && typeof val === "object") {
      Object.entries(val).forEach(([k, v]) => this[`_${k}`] !== v && (this[`_${k}`] = v));
    }
  }
  /**
   * Defines the style of the button.
   * @group Props
   */
  severity;
  /**
   * Add a shadow to indicate elevation.
   * @group Props
   */
  raised = false;
  /**
   * Add a circular border radius to the button.
   * @group Props
   */
  rounded = false;
  /**
   * Add a textual class to the button without a background initially.
   * @group Props
   */
  text = false;
  /**
   * Add a border class without a background initially.
   * @group Props
   */
  outlined = false;
  /**
   * Defines the size of the button.
   * @group Props
   */
  size = null;
  /**
   * Add a plain textual class to the button without a background initially.
   * @deprecated use variant property instead.
   * @group Props
   */
  plain = false;
  /**
   * Spans 100% width of the container when enabled.
   * @group Props
   */
  fluid;
  _label;
  _icon;
  _loading = false;
  initialized;
  get htmlElement() {
    return this.el.nativeElement;
  }
  _internalClasses = Object.values(INTERNAL_BUTTON_CLASSES);
  isTextButton = computed(() => !!(!this.iconSignal() && this.labelSignal() && this.text));
  /**
   * Text of the button.
   * @deprecated use pButtonLabel directive instead.
   * @group Props
   */
  get label() {
    return this._label;
  }
  /**
   * Name of the icon.
   * @deprecated use pButtonIcon directive instead
   * @group Props
   */
  get icon() {
    return this._icon;
  }
  /**
   * Used to pass all properties of the ButtonProps to the Button component.
   * @deprecated assign props directly to the button element.
   * @group Props
   */
  get buttonProps() {
    return this._buttonProps;
  }
  spinnerIcon = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" class="p-icon-spin">
        <g clip-path="url(#clip0_417_21408)">
            <path
                d="M6.99701 14C5.85441 13.999 4.72939 13.7186 3.72012 13.1832C2.71084 12.6478 1.84795 11.8737 1.20673 10.9284C0.565504 9.98305 0.165424 8.89526 0.041387 7.75989C-0.0826496 6.62453 0.073125 5.47607 0.495122 4.4147C0.917119 3.35333 1.59252 2.4113 2.46241 1.67077C3.33229 0.930247 4.37024 0.413729 5.4857 0.166275C6.60117 -0.0811796 7.76026 -0.0520535 8.86188 0.251112C9.9635 0.554278 10.9742 1.12227 11.8057 1.90555C11.915 2.01493 11.9764 2.16319 11.9764 2.31778C11.9764 2.47236 11.915 2.62062 11.8057 2.73C11.7521 2.78503 11.688 2.82877 11.6171 2.85864C11.5463 2.8885 11.4702 2.90389 11.3933 2.90389C11.3165 2.90389 11.2404 2.8885 11.1695 2.85864C11.0987 2.82877 11.0346 2.78503 10.9809 2.73C9.9998 1.81273 8.73246 1.26138 7.39226 1.16876C6.05206 1.07615 4.72086 1.44794 3.62279 2.22152C2.52471 2.99511 1.72683 4.12325 1.36345 5.41602C1.00008 6.70879 1.09342 8.08723 1.62775 9.31926C2.16209 10.5513 3.10478 11.5617 4.29713 12.1803C5.48947 12.7989 6.85865 12.988 8.17414 12.7157C9.48963 12.4435 10.6711 11.7264 11.5196 10.6854C12.3681 9.64432 12.8319 8.34282 12.8328 7C12.8328 6.84529 12.8943 6.69692 13.0038 6.58752C13.1132 6.47812 13.2616 6.41667 13.4164 6.41667C13.5712 6.41667 13.7196 6.47812 13.8291 6.58752C13.9385 6.69692 14 6.84529 14 7C14 8.85651 13.2622 10.637 11.9489 11.9497C10.6356 13.2625 8.85432 14 6.99701 14Z"
                fill="currentColor"
            />
        </g>
        <defs>
            <clipPath id="clip0_417_21408">
                <rect width="14" height="14" fill="white" />
            </clipPath>
        </defs>
    </svg>`;
  _componentStyle = inject(ButtonStyle);
  ngAfterViewInit() {
    super.ngAfterViewInit();
    addClass(this.htmlElement, this.getStyleClass().join(" "));
    this.createIcon();
    this.createLabel();
    this.initialized = true;
  }
  ngOnChanges(simpleChanges) {
    super.ngOnChanges(simpleChanges);
    const {
      buttonProps
    } = simpleChanges;
    if (buttonProps) {
      const props = buttonProps.currentValue;
      for (const property in props) {
        this[property] = props[property];
      }
    }
  }
  getStyleClass() {
    const styleClass = [INTERNAL_BUTTON_CLASSES.button, INTERNAL_BUTTON_CLASSES.component];
    if (this.icon && !this.label && isEmpty(this.htmlElement.textContent)) {
      styleClass.push(INTERNAL_BUTTON_CLASSES.iconOnly);
    }
    if (this.loading) {
      styleClass.push(INTERNAL_BUTTON_CLASSES.disabled, INTERNAL_BUTTON_CLASSES.loading);
      if (!this.icon && this.label) {
        styleClass.push(INTERNAL_BUTTON_CLASSES.labelOnly);
      }
      if (this.icon && !this.label && !isEmpty(this.htmlElement.textContent)) {
        styleClass.push(INTERNAL_BUTTON_CLASSES.iconOnly);
      }
    }
    if (this.text) {
      styleClass.push("p-button-text");
    }
    if (this.severity) {
      styleClass.push(`p-button-${this.severity}`);
    }
    if (this.plain) {
      styleClass.push("p-button-plain");
    }
    if (this.raised) {
      styleClass.push("p-button-raised");
    }
    if (this.size) {
      styleClass.push(`p-button-${this.size}`);
    }
    if (this.outlined) {
      styleClass.push("p-button-outlined");
    }
    if (this.rounded) {
      styleClass.push("p-button-rounded");
    }
    if (this.size === "small") {
      styleClass.push("p-button-sm");
    }
    if (this.size === "large") {
      styleClass.push("p-button-lg");
    }
    if (this.hasFluid) {
      styleClass.push("p-button-fluid");
    }
    return styleClass;
  }
  get hasFluid() {
    const nativeElement = this.el.nativeElement;
    const fluidComponent = nativeElement.closest("p-fluid");
    return isEmpty(this.fluid) ? !!fluidComponent : this.fluid;
  }
  setStyleClass() {
    const styleClass = this.getStyleClass();
    this.htmlElement.classList.remove(...this._internalClasses);
    this.htmlElement.classList.add(...styleClass);
  }
  createLabel() {
    const created = findSingle(this.htmlElement, ".p-button-label");
    if (!created && this.label) {
      let labelElement = this.document.createElement("span");
      if (this.icon && !this.label) {
        labelElement.setAttribute("aria-hidden", "true");
      }
      labelElement.className = "p-button-label";
      labelElement.appendChild(this.document.createTextNode(this.label));
      this.htmlElement.appendChild(labelElement);
    }
  }
  createIcon() {
    const created = findSingle(this.htmlElement, ".p-button-icon");
    if (!created && (this.icon || this.loading)) {
      let iconElement = this.document.createElement("span");
      iconElement.className = "p-button-icon";
      iconElement.setAttribute("aria-hidden", "true");
      let iconPosClass = this.label ? "p-button-icon-" + this.iconPos : null;
      if (iconPosClass) {
        addClass(iconElement, iconPosClass);
      }
      let iconClass = this.getIconClass();
      if (iconClass) {
        addClass(iconElement, iconClass);
      }
      if (!this.loadingIcon && this.loading) {
        iconElement.innerHTML = this.spinnerIcon;
      }
      this.htmlElement.insertBefore(iconElement, this.htmlElement.firstChild);
    }
  }
  updateLabel() {
    let labelElement = findSingle(this.htmlElement, ".p-button-label");
    if (!this.label) {
      labelElement && this.htmlElement.removeChild(labelElement);
      return;
    }
    labelElement ? labelElement.textContent = this.label : this.createLabel();
  }
  updateIcon() {
    let iconElement = findSingle(this.htmlElement, ".p-button-icon");
    let labelElement = findSingle(this.htmlElement, ".p-button-label");
    if (this.loading && !this.loadingIcon && iconElement) {
      iconElement.innerHTML = this.spinnerIcon;
    } else if (iconElement?.innerHTML) {
      iconElement.innerHTML = "";
    }
    if (iconElement) {
      if (this.iconPos) {
        iconElement.className = "p-button-icon " + (labelElement ? "p-button-icon-" + this.iconPos : "") + " " + this.getIconClass();
      } else {
        iconElement.className = "p-button-icon " + this.getIconClass();
      }
    } else {
      this.createIcon();
    }
  }
  getIconClass() {
    return this.loading ? "p-button-loading-icon " + (this.loadingIcon ? this.loadingIcon : "p-icon") : this.icon || "p-hidden";
  }
  ngOnDestroy() {
    this.initialized = false;
    super.ngOnDestroy();
  }
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵButtonDirective_BaseFactory;
    return function ButtonDirective_Factory(__ngFactoryType__) {
      return (ɵButtonDirective_BaseFactory || (ɵButtonDirective_BaseFactory = ɵɵgetInheritedFactory(_ButtonDirective)))(__ngFactoryType__ || _ButtonDirective);
    };
  })();
  static ɵdir = ɵɵdefineDirective({
    type: _ButtonDirective,
    selectors: [["", "pButton", ""]],
    contentQueries: function ButtonDirective_ContentQueries(rf, ctx, dirIndex) {
      if (rf & 1) {
        ɵɵcontentQuerySignal(dirIndex, ctx.iconSignal, ButtonIcon, 5);
        ɵɵcontentQuerySignal(dirIndex, ctx.labelSignal, ButtonLabel, 5);
      }
      if (rf & 2) {
        ɵɵqueryAdvance(2);
      }
    },
    hostVars: 4,
    hostBindings: function ButtonDirective_HostBindings(rf, ctx) {
      if (rf & 2) {
        ɵɵclassProp("p-button-icon-only", ctx.isIconOnly())("p-button-text", ctx.isTextButton());
      }
    },
    inputs: {
      iconPos: "iconPos",
      loadingIcon: "loadingIcon",
      loading: "loading",
      severity: "severity",
      raised: [2, "raised", "raised", booleanAttribute],
      rounded: [2, "rounded", "rounded", booleanAttribute],
      text: [2, "text", "text", booleanAttribute],
      outlined: [2, "outlined", "outlined", booleanAttribute],
      size: "size",
      plain: [2, "plain", "plain", booleanAttribute],
      fluid: [2, "fluid", "fluid", booleanAttribute],
      label: "label",
      icon: "icon",
      buttonProps: "buttonProps"
    },
    standalone: true,
    features: [ɵɵProvidersFeature([ButtonStyle]), ɵɵInputTransformsFeature, ɵɵInheritDefinitionFeature, ɵɵNgOnChangesFeature]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ButtonDirective, [{
    type: Directive,
    args: [{
      selector: "[pButton]",
      standalone: true,
      providers: [ButtonStyle],
      host: {
        "[class.p-button-icon-only]": "isIconOnly()",
        "[class.p-button-text]": "isTextButton()"
      }
    }]
  }], null, {
    iconPos: [{
      type: Input
    }],
    loadingIcon: [{
      type: Input
    }],
    loading: [{
      type: Input
    }],
    severity: [{
      type: Input
    }],
    raised: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    rounded: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    text: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    outlined: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    size: [{
      type: Input
    }],
    plain: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    fluid: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    label: [{
      type: Input
    }],
    icon: [{
      type: Input
    }],
    buttonProps: [{
      type: Input
    }]
  });
})();
var Button = class _Button extends BaseComponent {
  /**
   * Type of the button.
   * @group Props
   */
  type = "button";
  /**
   * Position of the icon.
   * @group Props
   */
  iconPos = "left";
  /**
   * Name of the icon.
   * @group Props
   */
  icon;
  /**
   * Value of the badge.
   * @group Props
   */
  badge;
  /**
   * Uses to pass attributes to the label's DOM element.
   * @group Props
   */
  label;
  /**
   * When present, it specifies that the component should be disabled.
   * @group Props
   */
  disabled;
  /**
   * Whether the button is in loading state.
   * @group Props
   */
  loading = false;
  /**
   * Icon to display in loading state.
   * @group Props
   */
  loadingIcon;
  /**
   * Add a shadow to indicate elevation.
   * @group Props
   */
  raised = false;
  /**
   * Add a circular border radius to the button.
   * @group Props
   */
  rounded = false;
  /**
   * Add a textual class to the button without a background initially.
   * @group Props
   */
  text = false;
  /**
   * Add a plain textual class to the button without a background initially.
   * @deprecated use variant property instead.
   * @group Props
   */
  plain = false;
  /**
   * Defines the style of the button.
   * @group Props
   */
  severity;
  /**
   * Add a border class without a background initially.
   * @group Props
   */
  outlined = false;
  /**
   * Add a link style to the button.
   * @group Props
   */
  link = false;
  /**
   * Add a tabindex to the button.
   * @group Props
   */
  tabindex;
  /**
   * Defines the size of the button.
   * @group Props
   */
  size;
  /**
   * Specifies the variant of the component.
   * @group Props
   */
  variant;
  /**
   * Inline style of the element.
   * @group Props
   */
  style;
  /**
   * Class of the element.
   * @group Props
   */
  styleClass;
  /**
   * Style class of the badge.
   * @group Props
   * @deprecated use badgeSeverity instead.
   */
  badgeClass;
  /**
   * Severity type of the badge.
   * @group Props
   * @defaultValue secondary
   */
  badgeSeverity = "secondary";
  /**
   * Used to define a string that autocomplete attribute the current element.
   * @group Props
   */
  ariaLabel;
  /**
   * When present, it specifies that the component should automatically get focus on load.
   * @group Props
   */
  autofocus;
  /**
   * Spans 100% width of the container when enabled.
   * @group Props
   */
  fluid;
  /**
   * Callback to execute when button is clicked.
   * This event is intended to be used with the <p-button> component. Using a regular <button> element, use (click).
   * @param {MouseEvent} event - Mouse event.
   * @group Emits
   */
  onClick = new EventEmitter();
  /**
   * Callback to execute when button is focused.
   * This event is intended to be used with the <p-button> component. Using a regular <button> element, use (focus).
   * @param {FocusEvent} event - Focus event.
   * @group Emits
   */
  onFocus = new EventEmitter();
  /**
   * Callback to execute when button loses focus.
   * This event is intended to be used with the <p-button> component. Using a regular <button> element, use (blur).
   * @param {FocusEvent} event - Focus event.
   * @group Emits
   */
  onBlur = new EventEmitter();
  /**
   * Template of the content.
   * @group Templates
   **/
  contentTemplate;
  /**
   * Template of the loading.
   * @group Templates
   **/
  loadingIconTemplate;
  /**
   * Template of the icon.
   * @group Templates
   **/
  iconTemplate;
  _buttonProps;
  /**
   * Used to pass all properties of the ButtonProps to the Button component.
   * @group Props
   */
  get buttonProps() {
    return this._buttonProps;
  }
  set buttonProps(val) {
    this._buttonProps = val;
    if (val && typeof val === "object") {
      Object.entries(val).forEach(([k, v]) => this[`_${k}`] !== v && (this[`_${k}`] = v));
    }
  }
  get hasFluid() {
    const nativeElement = this.el.nativeElement;
    const fluidComponent = nativeElement.closest("p-fluid");
    return isEmpty(this.fluid) ? !!fluidComponent : this.fluid;
  }
  _componentStyle = inject(ButtonStyle);
  templates;
  _contentTemplate;
  _iconTemplate;
  _loadingIconTemplate;
  ngAfterContentInit() {
    this.templates?.forEach((item) => {
      switch (item.getType()) {
        case "content":
          this.contentTemplate = item.template;
          break;
        case "icon":
          this.iconTemplate = item.template;
          break;
        case "loadingicon":
          this.loadingIconTemplate = item.template;
          break;
        default:
          this.contentTemplate = item.template;
          break;
      }
    });
  }
  ngOnChanges(simpleChanges) {
    super.ngOnChanges(simpleChanges);
    const {
      buttonProps
    } = simpleChanges;
    if (buttonProps) {
      const props = buttonProps.currentValue;
      for (const property in props) {
        this[property] = props[property];
      }
    }
  }
  spinnerIconClass() {
    return Object.entries(this.iconClass()).filter(([, value]) => !!value).reduce((acc, [key]) => acc + ` ${key}`, "p-button-loading-icon");
  }
  iconClass() {
    return {
      [`p-button-loading-icon pi-spin ${this.loadingIcon ?? ""}`]: this.loading,
      "p-button-icon": true,
      "p-button-icon-left": this.iconPos === "left" && this.label,
      "p-button-icon-right": this.iconPos === "right" && this.label,
      "p-button-icon-top": this.iconPos === "top" && this.label,
      "p-button-icon-bottom": this.iconPos === "bottom" && this.label
    };
  }
  get buttonClass() {
    return {
      "p-button p-component": true,
      "p-button-icon-only": (this.icon || this.iconTemplate || this.loadingIcon || this.loadingIconTemplate || this._loadingIconTemplate) && !this.label,
      "p-button-vertical": (this.iconPos === "top" || this.iconPos === "bottom") && this.label,
      "p-button-loading": this.loading,
      "p-button-loading-label-only": this.loading && !this.icon && this.label && !this.loadingIcon && this.iconPos === "left",
      "p-button-link": this.link,
      [`p-button-${this.severity}`]: this.severity,
      "p-button-raised": this.raised,
      "p-button-rounded": this.rounded,
      "p-button-text": this.text || this.variant == "text",
      "p-button-outlined": this.outlined || this.variant == "outlined",
      "p-button-sm": this.size === "small",
      "p-button-lg": this.size === "large",
      "p-button-plain": this.plain,
      "p-button-fluid": this.hasFluid,
      [`${this.styleClass}`]: this.styleClass
    };
  }
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵButton_BaseFactory;
    return function Button_Factory(__ngFactoryType__) {
      return (ɵButton_BaseFactory || (ɵButton_BaseFactory = ɵɵgetInheritedFactory(_Button)))(__ngFactoryType__ || _Button);
    };
  })();
  static ɵcmp = ɵɵdefineComponent({
    type: _Button,
    selectors: [["p-button"]],
    contentQueries: function Button_ContentQueries(rf, ctx, dirIndex) {
      if (rf & 1) {
        ɵɵcontentQuery(dirIndex, _c0, 5);
        ɵɵcontentQuery(dirIndex, _c1, 5);
        ɵɵcontentQuery(dirIndex, _c2, 5);
        ɵɵcontentQuery(dirIndex, PrimeTemplate, 4);
      }
      if (rf & 2) {
        let _t;
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.contentTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.loadingIconTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.iconTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.templates = _t);
      }
    },
    inputs: {
      type: "type",
      iconPos: "iconPos",
      icon: "icon",
      badge: "badge",
      label: "label",
      disabled: [2, "disabled", "disabled", booleanAttribute],
      loading: [2, "loading", "loading", booleanAttribute],
      loadingIcon: "loadingIcon",
      raised: [2, "raised", "raised", booleanAttribute],
      rounded: [2, "rounded", "rounded", booleanAttribute],
      text: [2, "text", "text", booleanAttribute],
      plain: [2, "plain", "plain", booleanAttribute],
      severity: "severity",
      outlined: [2, "outlined", "outlined", booleanAttribute],
      link: [2, "link", "link", booleanAttribute],
      tabindex: [2, "tabindex", "tabindex", numberAttribute],
      size: "size",
      variant: "variant",
      style: "style",
      styleClass: "styleClass",
      badgeClass: "badgeClass",
      badgeSeverity: "badgeSeverity",
      ariaLabel: "ariaLabel",
      autofocus: [2, "autofocus", "autofocus", booleanAttribute],
      fluid: [2, "fluid", "fluid", booleanAttribute],
      buttonProps: "buttonProps"
    },
    outputs: {
      onClick: "onClick",
      onFocus: "onFocus",
      onBlur: "onBlur"
    },
    standalone: true,
    features: [ɵɵProvidersFeature([ButtonStyle]), ɵɵInputTransformsFeature, ɵɵInheritDefinitionFeature, ɵɵNgOnChangesFeature, ɵɵStandaloneFeature],
    ngContentSelectors: _c3,
    decls: 7,
    vars: 14,
    consts: [["pRipple", "", 3, "click", "focus", "blur", "ngStyle", "disabled", "ngClass", "pAutoFocus"], [4, "ngTemplateOutlet"], [4, "ngIf"], ["class", "p-button-label", 4, "ngIf"], [3, "value", "severity", 4, "ngIf"], [4, "ngTemplateOutlet", "ngTemplateOutletContext"], [3, "ngClass", 4, "ngIf"], [3, "styleClass", "spin", 4, "ngIf"], [3, "ngClass"], [3, "styleClass", "spin"], [3, "ngIf"], [3, "class", "ngClass", 4, "ngIf"], [1, "p-button-label"], [3, "value", "severity"]],
    template: function Button_Template(rf, ctx) {
      if (rf & 1) {
        ɵɵprojectionDef();
        ɵɵelementStart(0, "button", 0);
        ɵɵlistener("click", function Button_Template_button_click_0_listener($event) {
          return ctx.onClick.emit($event);
        })("focus", function Button_Template_button_focus_0_listener($event) {
          return ctx.onFocus.emit($event);
        })("blur", function Button_Template_button_blur_0_listener($event) {
          return ctx.onBlur.emit($event);
        });
        ɵɵprojection(1);
        ɵɵtemplate(2, Button_ng_container_2_Template, 1, 0, "ng-container", 1)(3, Button_ng_container_3_Template, 3, 5, "ng-container", 2)(4, Button_ng_container_4_Template, 3, 5, "ng-container", 2)(5, Button_span_5_Template, 2, 3, "span", 3)(6, Button_p_badge_6_Template, 1, 2, "p-badge", 4);
        ɵɵelementEnd();
      }
      if (rf & 2) {
        ɵɵproperty("ngStyle", ctx.style)("disabled", ctx.disabled || ctx.loading)("ngClass", ctx.buttonClass)("pAutoFocus", ctx.autofocus);
        ɵɵattribute("type", ctx.type)("aria-label", ctx.ariaLabel)("data-pc-name", "button")("data-pc-section", "root")("tabindex", ctx.tabindex);
        ɵɵadvance(2);
        ɵɵproperty("ngTemplateOutlet", ctx.contentTemplate || ctx._contentTemplate);
        ɵɵadvance();
        ɵɵproperty("ngIf", ctx.loading);
        ɵɵadvance();
        ɵɵproperty("ngIf", !ctx.loading);
        ɵɵadvance();
        ɵɵproperty("ngIf", !ctx.contentTemplate && !ctx._contentTemplate && ctx.label);
        ɵɵadvance();
        ɵɵproperty("ngIf", !ctx.contentTemplate && !ctx._contentTemplate && ctx.badge);
      }
    },
    dependencies: [CommonModule, NgClass, NgIf, NgTemplateOutlet, NgStyle, Ripple, AutoFocus, SpinnerIcon, BadgeModule, Badge, SharedModule],
    encapsulation: 2,
    changeDetection: 0
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(Button, [{
    type: Component,
    args: [{
      selector: "p-button",
      standalone: true,
      imports: [CommonModule, Ripple, AutoFocus, SpinnerIcon, BadgeModule, SharedModule],
      template: `
        <button
            [attr.type]="type"
            [attr.aria-label]="ariaLabel"
            [ngStyle]="style"
            [disabled]="disabled || loading"
            [ngClass]="buttonClass"
            (click)="onClick.emit($event)"
            (focus)="onFocus.emit($event)"
            (blur)="onBlur.emit($event)"
            pRipple
            [attr.data-pc-name]="'button'"
            [attr.data-pc-section]="'root'"
            [attr.tabindex]="tabindex"
            [pAutoFocus]="autofocus"
        >
            <ng-content></ng-content>
            <ng-container *ngTemplateOutlet="contentTemplate || _contentTemplate"></ng-container>
            <ng-container *ngIf="loading">
                <ng-container *ngIf="!loadingIconTemplate && !_loadingIconTemplate">
                    <span *ngIf="loadingIcon" [ngClass]="iconClass()" [attr.aria-hidden]="true" [attr.data-pc-section]="'loadingicon'"></span>
                    <SpinnerIcon *ngIf="!loadingIcon" [styleClass]="spinnerIconClass()" [spin]="true" [attr.aria-hidden]="true" [attr.data-pc-section]="'loadingicon'" />
                </ng-container>
                <ng-template [ngIf]="loadingIconTemplate || _loadingIconTemplate" *ngTemplateOutlet="loadingIconTemplate || _loadingIconTemplate; context: { class: iconClass() }"></ng-template>
            </ng-container>
            <ng-container *ngIf="!loading">
                <span *ngIf="icon && !iconTemplate && !_iconTemplate" [class]="icon" [ngClass]="iconClass()" [attr.data-pc-section]="'icon'"></span>
                <ng-template [ngIf]="!icon && (iconTemplate || _iconTemplate)" *ngTemplateOutlet="iconTemplate || _iconTemplate; context: { class: iconClass() }"></ng-template>
            </ng-container>
            <span class="p-button-label" [attr.aria-hidden]="icon && !label" *ngIf="!contentTemplate && !_contentTemplate && label" [attr.data-pc-section]="'label'">{{ label }}</span>
            <p-badge *ngIf="!contentTemplate && !_contentTemplate && badge" [value]="badge" [severity]="badgeSeverity"></p-badge>
        </button>
    `,
      changeDetection: ChangeDetectionStrategy.OnPush,
      encapsulation: ViewEncapsulation$1.None,
      providers: [ButtonStyle]
    }]
  }], null, {
    type: [{
      type: Input
    }],
    iconPos: [{
      type: Input
    }],
    icon: [{
      type: Input
    }],
    badge: [{
      type: Input
    }],
    label: [{
      type: Input
    }],
    disabled: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    loading: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    loadingIcon: [{
      type: Input
    }],
    raised: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    rounded: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    text: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    plain: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    severity: [{
      type: Input
    }],
    outlined: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    link: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    tabindex: [{
      type: Input,
      args: [{
        transform: numberAttribute
      }]
    }],
    size: [{
      type: Input
    }],
    variant: [{
      type: Input
    }],
    style: [{
      type: Input
    }],
    styleClass: [{
      type: Input
    }],
    badgeClass: [{
      type: Input
    }],
    badgeSeverity: [{
      type: Input
    }],
    ariaLabel: [{
      type: Input
    }],
    autofocus: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    fluid: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    onClick: [{
      type: Output
    }],
    onFocus: [{
      type: Output
    }],
    onBlur: [{
      type: Output
    }],
    contentTemplate: [{
      type: ContentChild,
      args: ["content"]
    }],
    loadingIconTemplate: [{
      type: ContentChild,
      args: ["loading"]
    }],
    iconTemplate: [{
      type: ContentChild,
      args: ["icon"]
    }],
    buttonProps: [{
      type: Input
    }],
    templates: [{
      type: ContentChildren,
      args: [PrimeTemplate]
    }]
  });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && ɵsetClassDebugInfo(Button, {
    className: "Button"
  });
})();
var ButtonModule = class _ButtonModule {
  static ɵfac = function ButtonModule_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _ButtonModule)();
  };
  static ɵmod = ɵɵdefineNgModule({
    type: _ButtonModule
  });
  static ɵinj = ɵɵdefineInjector({
    imports: [CommonModule, Button, SharedModule, SharedModule]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ButtonModule, [{
    type: NgModule,
    args: [{
      imports: [CommonModule, ButtonDirective, Button, SharedModule, ButtonLabel, ButtonIcon],
      exports: [ButtonDirective, Button, ButtonLabel, ButtonIcon, SharedModule]
    }]
  }], null, null);
})();
export {
  Button,
  ButtonClasses,
  ButtonDirective,
  ButtonIcon,
  ButtonLabel,
  ButtonModule,
  ButtonStyle
};
//# sourceMappingURL=primeng_button.js.map
