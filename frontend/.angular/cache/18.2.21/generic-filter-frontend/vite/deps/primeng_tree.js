import {
  IconField,
  InputIcon,
  Scroller
} from "./chunk-RLZ5GWGV.js";
import {
  Ripple
} from "./chunk-LEWWZTBW.js";
import {
  CheckIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  MinusIcon,
  SearchIcon,
  SpinnerIcon
} from "./chunk-OZV3QA4W.js";
import {
  InputText
} from "./chunk-G4C7QY43.js";
import {
  BaseComponent
} from "./chunk-MRDH5YK7.js";
import {
  FormsModule,
  NG_VALUE_ACCESSOR,
  NgControl,
  NgControlStatus,
  NgModel
} from "./chunk-UXM7BPGO.js";
import {
  BaseStyle
} from "./chunk-RNVRA2EI.js";
import {
  PrimeTemplate,
  SharedModule,
  TranslationKeys,
  TreeDragDropService,
  contains,
  equals,
  find,
  findSingle,
  focus,
  hasClass,
  removeAccents,
  resolveFieldData
} from "./chunk-BQHGYFM7.js";
import {
  CommonModule,
  NgClass,
  NgForOf,
  NgIf,
  NgStyle,
  NgTemplateOutlet
} from "./chunk-GUBNNMHS.js";
import {
  ChangeDetectionStrategy,
  Component,
  ContentChild,
  ContentChildren,
  EventEmitter,
  Injectable,
  Input,
  NgModule,
  Optional,
  Output,
  ViewChild,
  ViewEncapsulation$1,
  booleanAttribute,
  forwardRef,
  inject,
  numberAttribute,
  setClassMetadata,
  signal,
  ɵsetClassDebugInfo,
  ɵɵInheritDefinitionFeature,
  ɵɵInputTransformsFeature,
  ɵɵNgOnChangesFeature,
  ɵɵProvidersFeature,
  ɵɵStandaloneFeature,
  ɵɵadvance,
  ɵɵattribute,
  ɵɵclassMap,
  ɵɵconditional,
  ɵɵcontentQuery,
  ɵɵdefineComponent,
  ɵɵdefineInjectable,
  ɵɵdefineInjector,
  ɵɵdefineNgModule,
  ɵɵdirectiveInject,
  ɵɵelement,
  ɵɵelementContainer,
  ɵɵelementContainerEnd,
  ɵɵelementContainerStart,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetCurrentView,
  ɵɵgetInheritedFactory,
  ɵɵlistener,
  ɵɵloadQuery,
  ɵɵnextContext,
  ɵɵproperty,
  ɵɵpureFunction0,
  ɵɵpureFunction1,
  ɵɵpureFunction2,
  ɵɵqueryRefresh,
  ɵɵresetView,
  ɵɵrestoreView,
  ɵɵstyleMap,
  ɵɵstyleProp,
  ɵɵtemplate,
  ɵɵtemplateRefExtractor,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtextInterpolate1,
  ɵɵviewQuery
} from "./chunk-MEHXH6ZQ.js";
import "./chunk-PEBH6BBU.js";
import "./chunk-WPM5VTLQ.js";
import "./chunk-4S3KYZTJ.js";
import {
  __spreadValues
} from "./chunk-WDMUDEB6.js";

// node_modules/primeng/fesm2022/primeng-checkbox.mjs
var theme = ({
  dt
}) => `
.p-checkbox {
    position: relative;
    display: inline-flex;
    user-select: none;
    vertical-align: bottom;
    width: ${dt("checkbox.width")};
    height: ${dt("checkbox.height")};
}

.p-checkbox-input {
    cursor: pointer;
    appearance: none;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    padding: 0;
    margin: 0;
    opacity: 0;
    z-index: 1;
    outline: 0 none;
    border: 1px solid transparent;
    border-radius: ${dt("checkbox.border.radius")};
}

.p-checkbox-box {
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: ${dt("checkbox.border.radius")};
    border: 1px solid ${dt("checkbox.border.color")};
    background: ${dt("checkbox.background")};
    width: ${dt("checkbox.width")};
    height: ${dt("checkbox.height")};
    transition: background ${dt("checkbox.transition.duration")}, color ${dt("checkbox.transition.duration")}, border-color ${dt("checkbox.transition.duration")}, box-shadow ${dt("checkbox.transition.duration")}, outline-color ${dt("checkbox.transition.duration")};
    outline-color: transparent;
    box-shadow: ${dt("checkbox.shadow")};
}

.p-checkbox-icon {
    transition-duration: ${dt("checkbox.transition.duration")};
    color: ${dt("checkbox.icon.color")};
    font-size: ${dt("checkbox.icon.size")};
    width: ${dt("checkbox.icon.size")};
    height: ${dt("checkbox.icon.size")};
}

.p-checkbox:not(.p-disabled):has(.p-checkbox-input:hover) .p-checkbox-box {
    border-color: ${dt("checkbox.hover.border.color")};
}

.p-checkbox-checked .p-checkbox-box {
    border-color: ${dt("checkbox.checked.border.color")};
    background: ${dt("checkbox.checked.background")};
}

.p-checkbox-checked .p-checkbox-icon {
    color: ${dt("checkbox.icon.checked.color")};
}

.p-checkbox-checked:not(.p-disabled):has(.p-checkbox-input:hover) .p-checkbox-box {
    background: ${dt("checkbox.checked.hover.background")};
    border-color: ${dt("checkbox.checked.hover.border.color")};
}

.p-checkbox-checked:not(.p-disabled):has(.p-checkbox-input:hover) .p-checkbox-icon {
    color: ${dt("checkbox.icon.checked.hover.color")};
}

.p-checkbox:not(.p-disabled):has(.p-checkbox-input:focus-visible) .p-checkbox-box {
    border-color: ${dt("checkbox.focus.border.color")};
    box-shadow: ${dt("checkbox.focus.ring.shadow")};
    outline: ${dt("checkbox.focus.ring.width")} ${dt("checkbox.focus.ring.style")} ${dt("checkbox.focus.ring.color")};
    outline-offset: ${dt("checkbox.focus.ring.offset")};
}

.p-checkbox-checked:not(.p-disabled):has(.p-checkbox-input:focus-visible) .p-checkbox-box {
    border-color: ${dt("checkbox.checked.focus.border.color")};
}

.p-checkbox.ng-invalid.ng-dirty > .p-checkbox-box {
    border-color: ${dt("checkbox.invalid.border.color")};
}

.p-checkbox.p-variant-filled .p-checkbox-box {
    background: ${dt("checkbox.filled.background")};
}

.p-checkbox-checked.p-variant-filled .p-checkbox-box {
    background: ${dt("checkbox.checked.background")};
}

.p-checkbox-checked.p-variant-filled:not(.p-disabled):has(.p-checkbox-input:hover) .p-checkbox-box {
    background: ${dt("checkbox.checked.hover.background")};
}

.p-checkbox.p-disabled {
    opacity: 1;
}

.p-checkbox.p-disabled .p-checkbox-box {
    background: ${dt("checkbox.disabled.background")};
    border-color: ${dt("checkbox.checked.disabled.border.color")};
}

.p-checkbox.p-disabled .p-checkbox-box .p-checkbox-icon {
    color: ${dt("checkbox.icon.disabled.color")};
}

.p-checkbox-sm,
.p-checkbox-sm .p-checkbox-box {
    width: ${dt("checkbox.sm.width")};
    height: ${dt("checkbox.sm.height")};
}

.p-checkbox-sm .p-checkbox-icon {
    font-size: ${dt("checkbox.icon.sm.size")};
    width: ${dt("checkbox.icon.sm.size")};
    height: ${dt("checkbox.icon.sm.size")};
}

.p-checkbox-lg,
.p-checkbox-lg .p-checkbox-box {
    width: ${dt("checkbox.lg.width")};
    height: ${dt("checkbox.lg.height")};
}

.p-checkbox-lg .p-checkbox-icon {
    font-size: ${dt("checkbox.icon.lg.size")};
    width: ${dt("checkbox.icon.lg.size")};
    height: ${dt("checkbox.icon.lg.size")};
}
`;
var classes = {
  root: ({
    instance,
    props
  }) => ["p-checkbox p-component", {
    "p-checkbox-checked": instance.checked,
    "p-disabled": props.disabled,
    "p-invalid": props.invalid,
    "p-variant-filled": props.variant ? props.variant === "filled" : instance.config.inputStyle === "filled" || instance.config.inputVariant === "filled"
  }],
  box: "p-checkbox-box",
  input: "p-checkbox-input",
  icon: "p-checkbox-icon"
};
var CheckboxStyle = class _CheckboxStyle extends BaseStyle {
  name = "checkbox";
  theme = theme;
  classes = classes;
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵCheckboxStyle_BaseFactory;
    return function CheckboxStyle_Factory(__ngFactoryType__) {
      return (ɵCheckboxStyle_BaseFactory || (ɵCheckboxStyle_BaseFactory = ɵɵgetInheritedFactory(_CheckboxStyle)))(__ngFactoryType__ || _CheckboxStyle);
    };
  })();
  static ɵprov = ɵɵdefineInjectable({
    token: _CheckboxStyle,
    factory: _CheckboxStyle.ɵfac
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(CheckboxStyle, [{
    type: Injectable
  }], null, null);
})();
var CheckboxClasses;
(function(CheckboxClasses2) {
  CheckboxClasses2["root"] = "p-checkbox";
  CheckboxClasses2["box"] = "p-checkbox-box";
  CheckboxClasses2["input"] = "p-checkbox-input";
  CheckboxClasses2["icon"] = "p-checkbox-icon";
})(CheckboxClasses || (CheckboxClasses = {}));
var _c0 = ["checkboxicon"];
var _c1 = ["input"];
var _c2 = () => ({
  "p-checkbox-input": true
});
var _c3 = (a0) => ({
  checked: a0,
  class: "p-checkbox-icon"
});
function Checkbox_ng_container_4_ng_container_1_span_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "span", 8);
  }
  if (rf & 2) {
    const ctx_r1 = ɵɵnextContext(3);
    ɵɵproperty("ngClass", ctx_r1.checkboxIcon);
    ɵɵattribute("data-pc-section", "icon");
  }
}
function Checkbox_ng_container_4_ng_container_1_CheckIcon_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "CheckIcon", 9);
  }
  if (rf & 2) {
    ɵɵproperty("styleClass", "p-checkbox-icon");
    ɵɵattribute("data-pc-section", "icon");
  }
}
function Checkbox_ng_container_4_ng_container_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, Checkbox_ng_container_4_ng_container_1_span_1_Template, 1, 2, "span", 7)(2, Checkbox_ng_container_4_ng_container_1_CheckIcon_2_Template, 1, 2, "CheckIcon", 6);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r1 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r1.checkboxIcon);
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r1.checkboxIcon);
  }
}
function Checkbox_ng_container_4_MinusIcon_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "MinusIcon", 9);
  }
  if (rf & 2) {
    ɵɵproperty("styleClass", "p-checkbox-icon");
    ɵɵattribute("data-pc-section", "icon");
  }
}
function Checkbox_ng_container_4_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, Checkbox_ng_container_4_ng_container_1_Template, 3, 2, "ng-container", 4)(2, Checkbox_ng_container_4_MinusIcon_2_Template, 1, 2, "MinusIcon", 6);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r1 = ɵɵnextContext();
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r1.checked);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r1._indeterminate());
  }
}
function Checkbox_5_ng_template_0_Template(rf, ctx) {
}
function Checkbox_5_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Checkbox_5_ng_template_0_Template, 0, 0, "ng-template");
  }
}
var CHECKBOX_VALUE_ACCESSOR = {
  provide: NG_VALUE_ACCESSOR,
  useExisting: forwardRef(() => Checkbox),
  multi: true
};
var Checkbox = class _Checkbox extends BaseComponent {
  /**
   * Value of the checkbox.
   * @group Props
   */
  value;
  /**
   * Name of the checkbox group.
   * @group Props
   */
  name;
  /**
   * When present, it specifies that the element should be disabled.
   * @group Props
   */
  disabled;
  /**
   * Allows to select a boolean value instead of multiple values.
   * @group Props
   */
  binary;
  /**
   * Establishes relationships between the component and label(s) where its value should be one or more element IDs.
   * @group Props
   */
  ariaLabelledBy;
  /**
   * Used to define a string that labels the input element.
   * @group Props
   */
  ariaLabel;
  /**
   * Index of the element in tabbing order.
   * @group Props
   */
  tabindex;
  /**
   * Identifier of the focus input to match a label defined for the component.
   * @group Props
   */
  inputId;
  /**
   * Inline style of the component.
   * @group Props
   */
  style;
  /**
   * Inline style of the input element.
   * @group Props
   */
  inputStyle;
  /**
   * Style class of the component.
   * @group Props
   */
  styleClass;
  /**
   * Style class of the input element.
   * @group Props
   */
  inputClass;
  /**
   * When present, it specifies input state as indeterminate.
   * @group Props
   */
  indeterminate = false;
  /**
   * Defines the size of the component.
   * @group Props
   */
  size;
  /**
   * Form control value.
   * @group Props
   */
  formControl;
  /**
   * Icon class of the checkbox icon.
   * @group Props
   */
  checkboxIcon;
  /**
   * When present, it specifies that the component cannot be edited.
   * @group Props
   */
  readonly;
  /**
   * When present, it specifies that checkbox must be checked before submitting the form.
   * @group Props
   */
  required;
  /**
   * When present, it specifies that the component should automatically get focus on load.
   * @group Props
   */
  autofocus;
  /**
   * Value in checked state.
   * @group Props
   */
  trueValue = true;
  /**
   * Value in unchecked state.
   * @group Props
   */
  falseValue = false;
  /**
   * Specifies the input variant of the component.
   * @group Props
   */
  variant = "outlined";
  /**
   * Callback to invoke on value change.
   * @param {CheckboxChangeEvent} event - Custom value change event.
   * @group Emits
   */
  onChange = new EventEmitter();
  /**
   * Callback to invoke when the receives focus.
   * @param {Event} event - Browser event.
   * @group Emits
   */
  onFocus = new EventEmitter();
  /**
   * Callback to invoke when the loses focus.
   * @param {Event} event - Browser event.
   * @group Emits
   */
  onBlur = new EventEmitter();
  inputViewChild;
  get checked() {
    return this._indeterminate() ? false : this.binary ? this.model === this.trueValue : contains(this.value, this.model);
  }
  get containerClass() {
    return {
      "p-checkbox p-component": true,
      "p-checkbox-checked p-highlight": this.checked,
      "p-disabled": this.disabled,
      "p-variant-filled": this.variant === "filled" || this.config.inputStyle() === "filled" || this.config.inputVariant() === "filled",
      "p-checkbox-sm p-inputfield-sm": this.size === "small",
      "p-checkbox-lg p-inputfield-lg": this.size === "large"
    };
  }
  _indeterminate = signal(void 0);
  /**
   * The template of the checkbox icon.
   * @group Templates
   */
  checkboxIconTemplate;
  templates;
  _checkboxIconTemplate;
  model;
  onModelChange = () => {
  };
  onModelTouched = () => {
  };
  focused = false;
  _componentStyle = inject(CheckboxStyle);
  ngAfterContentInit() {
    this.templates.forEach((item) => {
      switch (item.getType()) {
        case "icon":
          this._checkboxIconTemplate = item.template;
          break;
        case "checkboxicon":
          this._checkboxIconTemplate = item.template;
          break;
      }
    });
  }
  ngOnChanges(changes) {
    super.ngOnChanges(changes);
    if (changes.indeterminate) {
      this._indeterminate.set(changes.indeterminate.currentValue);
    }
  }
  updateModel(event) {
    let newModelValue;
    const selfControl = this.injector.get(NgControl, null, {
      optional: true,
      self: true
    });
    const currentModelValue = selfControl && !this.formControl ? selfControl.value : this.model;
    if (!this.binary) {
      if (this.checked || this._indeterminate()) newModelValue = currentModelValue.filter((val) => !equals(val, this.value));
      else newModelValue = currentModelValue ? [...currentModelValue, this.value] : [this.value];
      this.onModelChange(newModelValue);
      this.model = newModelValue;
      if (this.formControl) {
        this.formControl.setValue(newModelValue);
      }
    } else {
      newModelValue = this._indeterminate() ? this.trueValue : this.checked ? this.falseValue : this.trueValue;
      this.model = newModelValue;
      this.onModelChange(newModelValue);
    }
    if (this._indeterminate()) {
      this._indeterminate.set(false);
    }
    this.onChange.emit({
      checked: newModelValue,
      originalEvent: event
    });
  }
  handleChange(event) {
    if (!this.readonly) {
      this.updateModel(event);
    }
  }
  onInputFocus(event) {
    this.focused = true;
    this.onFocus.emit(event);
  }
  onInputBlur(event) {
    this.focused = false;
    this.onBlur.emit(event);
    this.onModelTouched();
  }
  focus() {
    this.inputViewChild.nativeElement.focus();
  }
  writeValue(model) {
    this.model = model;
    this.cd.markForCheck();
  }
  registerOnChange(fn) {
    this.onModelChange = fn;
  }
  registerOnTouched(fn) {
    this.onModelTouched = fn;
  }
  setDisabledState(val) {
    setTimeout(() => {
      this.disabled = val;
      this.cd.markForCheck();
    });
  }
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵCheckbox_BaseFactory;
    return function Checkbox_Factory(__ngFactoryType__) {
      return (ɵCheckbox_BaseFactory || (ɵCheckbox_BaseFactory = ɵɵgetInheritedFactory(_Checkbox)))(__ngFactoryType__ || _Checkbox);
    };
  })();
  static ɵcmp = ɵɵdefineComponent({
    type: _Checkbox,
    selectors: [["p-checkbox"], ["p-checkBox"], ["p-check-box"]],
    contentQueries: function Checkbox_ContentQueries(rf, ctx, dirIndex) {
      if (rf & 1) {
        ɵɵcontentQuery(dirIndex, _c0, 4);
        ɵɵcontentQuery(dirIndex, PrimeTemplate, 4);
      }
      if (rf & 2) {
        let _t;
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.checkboxIconTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.templates = _t);
      }
    },
    viewQuery: function Checkbox_Query(rf, ctx) {
      if (rf & 1) {
        ɵɵviewQuery(_c1, 5);
      }
      if (rf & 2) {
        let _t;
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.inputViewChild = _t.first);
      }
    },
    inputs: {
      value: "value",
      name: "name",
      disabled: [2, "disabled", "disabled", booleanAttribute],
      binary: [2, "binary", "binary", booleanAttribute],
      ariaLabelledBy: "ariaLabelledBy",
      ariaLabel: "ariaLabel",
      tabindex: [2, "tabindex", "tabindex", numberAttribute],
      inputId: "inputId",
      style: "style",
      inputStyle: "inputStyle",
      styleClass: "styleClass",
      inputClass: "inputClass",
      indeterminate: [2, "indeterminate", "indeterminate", booleanAttribute],
      size: "size",
      formControl: "formControl",
      checkboxIcon: "checkboxIcon",
      readonly: [2, "readonly", "readonly", booleanAttribute],
      required: [2, "required", "required", booleanAttribute],
      autofocus: [2, "autofocus", "autofocus", booleanAttribute],
      trueValue: "trueValue",
      falseValue: "falseValue",
      variant: "variant"
    },
    outputs: {
      onChange: "onChange",
      onFocus: "onFocus",
      onBlur: "onBlur"
    },
    standalone: true,
    features: [ɵɵProvidersFeature([CHECKBOX_VALUE_ACCESSOR, CheckboxStyle]), ɵɵInputTransformsFeature, ɵɵInheritDefinitionFeature, ɵɵNgOnChangesFeature, ɵɵStandaloneFeature],
    decls: 6,
    vars: 29,
    consts: [["input", ""], [3, "ngClass"], ["type", "checkbox", 3, "focus", "blur", "change", "value", "checked", "disabled", "readonly", "ngClass"], [1, "p-checkbox-box"], [4, "ngIf"], [4, "ngTemplateOutlet", "ngTemplateOutletContext"], [3, "styleClass", 4, "ngIf"], ["class", "p-checkbox-icon", 3, "ngClass", 4, "ngIf"], [1, "p-checkbox-icon", 3, "ngClass"], [3, "styleClass"]],
    template: function Checkbox_Template(rf, ctx) {
      if (rf & 1) {
        const _r1 = ɵɵgetCurrentView();
        ɵɵelementStart(0, "div", 1)(1, "input", 2, 0);
        ɵɵlistener("focus", function Checkbox_Template_input_focus_1_listener($event) {
          ɵɵrestoreView(_r1);
          return ɵɵresetView(ctx.onInputFocus($event));
        })("blur", function Checkbox_Template_input_blur_1_listener($event) {
          ɵɵrestoreView(_r1);
          return ɵɵresetView(ctx.onInputBlur($event));
        })("change", function Checkbox_Template_input_change_1_listener($event) {
          ɵɵrestoreView(_r1);
          return ɵɵresetView(ctx.handleChange($event));
        });
        ɵɵelementEnd();
        ɵɵelementStart(3, "div", 3);
        ɵɵtemplate(4, Checkbox_ng_container_4_Template, 3, 2, "ng-container", 4)(5, Checkbox_5_Template, 1, 0, null, 5);
        ɵɵelementEnd()();
      }
      if (rf & 2) {
        ɵɵstyleMap(ctx.style);
        ɵɵclassMap(ctx.styleClass);
        ɵɵproperty("ngClass", ctx.containerClass);
        ɵɵattribute("data-p-highlight", ctx.checked)("data-p-checked", ctx.checked)("data-p-disabled", ctx.disabled);
        ɵɵadvance();
        ɵɵstyleMap(ctx.inputStyle);
        ɵɵclassMap(ctx.inputClass);
        ɵɵproperty("value", ctx.value)("checked", ctx.checked)("disabled", ctx.disabled)("readonly", ctx.readonly)("ngClass", ɵɵpureFunction0(26, _c2));
        ɵɵattribute("id", ctx.inputId)("name", ctx.name)("tabindex", ctx.tabindex)("required", ctx.required)("aria-labelledby", ctx.ariaLabelledBy)("aria-label", ctx.ariaLabel);
        ɵɵadvance(3);
        ɵɵproperty("ngIf", !ctx.checkboxIconTemplate && !ctx._checkboxIconTemplate);
        ɵɵadvance();
        ɵɵproperty("ngTemplateOutlet", ctx.checkboxIconTemplate || ctx._checkboxIconTemplate)("ngTemplateOutletContext", ɵɵpureFunction1(27, _c3, ctx.checked));
      }
    },
    dependencies: [CommonModule, NgClass, NgIf, NgTemplateOutlet, CheckIcon, MinusIcon, SharedModule],
    encapsulation: 2,
    changeDetection: 0
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(Checkbox, [{
    type: Component,
    args: [{
      selector: "p-checkbox, p-checkBox, p-check-box",
      standalone: true,
      imports: [CommonModule, CheckIcon, MinusIcon, SharedModule],
      template: `
        <div [style]="style" [class]="styleClass" [ngClass]="containerClass" [attr.data-p-highlight]="checked" [attr.data-p-checked]="checked" [attr.data-p-disabled]="disabled">
            <input
                #input
                [attr.id]="inputId"
                type="checkbox"
                [value]="value"
                [attr.name]="name"
                [checked]="checked"
                [attr.tabindex]="tabindex"
                [disabled]="disabled"
                [readonly]="readonly"
                [attr.required]="required"
                [attr.aria-labelledby]="ariaLabelledBy"
                [attr.aria-label]="ariaLabel"
                [style]="inputStyle"
                [class]="inputClass"
                [ngClass]="{ 'p-checkbox-input': true }"
                (focus)="onInputFocus($event)"
                (blur)="onInputBlur($event)"
                (change)="handleChange($event)"
            />
            <div class="p-checkbox-box">
                <ng-container *ngIf="!checkboxIconTemplate && !_checkboxIconTemplate">
                    <ng-container *ngIf="checked">
                        <span *ngIf="checkboxIcon" class="p-checkbox-icon" [ngClass]="checkboxIcon" [attr.data-pc-section]="'icon'"></span>
                        <CheckIcon *ngIf="!checkboxIcon" [styleClass]="'p-checkbox-icon'" [attr.data-pc-section]="'icon'" />
                    </ng-container>
                    <MinusIcon *ngIf="_indeterminate()" [styleClass]="'p-checkbox-icon'" [attr.data-pc-section]="'icon'" />
                </ng-container>
                <ng-template *ngTemplateOutlet="checkboxIconTemplate || _checkboxIconTemplate; context: { checked: checked, class: 'p-checkbox-icon' }"></ng-template>
            </div>
        </div>
    `,
      providers: [CHECKBOX_VALUE_ACCESSOR, CheckboxStyle],
      changeDetection: ChangeDetectionStrategy.OnPush,
      encapsulation: ViewEncapsulation$1.None
    }]
  }], null, {
    value: [{
      type: Input
    }],
    name: [{
      type: Input
    }],
    disabled: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    binary: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    ariaLabelledBy: [{
      type: Input
    }],
    ariaLabel: [{
      type: Input
    }],
    tabindex: [{
      type: Input,
      args: [{
        transform: numberAttribute
      }]
    }],
    inputId: [{
      type: Input
    }],
    style: [{
      type: Input
    }],
    inputStyle: [{
      type: Input
    }],
    styleClass: [{
      type: Input
    }],
    inputClass: [{
      type: Input
    }],
    indeterminate: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    size: [{
      type: Input
    }],
    formControl: [{
      type: Input
    }],
    checkboxIcon: [{
      type: Input
    }],
    readonly: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    required: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    autofocus: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    trueValue: [{
      type: Input
    }],
    falseValue: [{
      type: Input
    }],
    variant: [{
      type: Input
    }],
    onChange: [{
      type: Output
    }],
    onFocus: [{
      type: Output
    }],
    onBlur: [{
      type: Output
    }],
    inputViewChild: [{
      type: ViewChild,
      args: ["input"]
    }],
    checkboxIconTemplate: [{
      type: ContentChild,
      args: ["checkboxicon", {
        descendants: false
      }]
    }],
    templates: [{
      type: ContentChildren,
      args: [PrimeTemplate]
    }]
  });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && ɵsetClassDebugInfo(Checkbox, {
    className: "Checkbox"
  });
})();
var CheckboxModule = class _CheckboxModule {
  static ɵfac = function CheckboxModule_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _CheckboxModule)();
  };
  static ɵmod = ɵɵdefineNgModule({
    type: _CheckboxModule
  });
  static ɵinj = ɵɵdefineInjector({
    imports: [Checkbox, SharedModule, SharedModule]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(CheckboxModule, [{
    type: NgModule,
    args: [{
      imports: [Checkbox, SharedModule],
      exports: [Checkbox, SharedModule]
    }]
  }], null, null);
})();

// node_modules/primeng/fesm2022/primeng-tree.mjs
var theme2 = ({
  dt
}) => `
.p-tree {
    background: ${dt("tree.background")};
    color: ${dt("tree.color")};
    padding: ${dt("tree.padding")};
}

.p-tree-root-children,
.p-tree-node-children {
    display: flex;
    list-style-type: none;
    flex-direction: column;
    margin: 0;
    gap: ${dt("tree.gap")};
}

.p-tree-root-children {
    padding: 0;
    padding-block-start: ${dt("tree.gap")};
}

.p-tree-node-children {
    padding-block-start: ${dt("tree.gap")};
    padding-inline-start: ${dt("tree.indent")};
}

.p-tree-node {
    padding: 0;
    outline: 0 none;
}

.p-tree-node-content {
    border-radius: ${dt("tree.node.border.radius")};
    padding: ${dt("tree.node.padding")};
    display: flex;
    align-items: center;
    outline-color: transparent;
    color: ${dt("tree.node.color")};
    gap: ${dt("tree.node.gap")};
    transition: background ${dt("tree.transition.duration")}, color ${dt("tree.transition.duration")}, outline-color ${dt("tree.transition.duration")}, box-shadow ${dt("tree.transition.duration")};
}

.p-tree-node:focus-visible > .p-tree-node-content {
    box-shadow: ${dt("tree.node.focus.ring.shadow")};
    outline: ${dt("tree.node.focus.ring.width")} ${dt("tree.node.focus.ring.style")} ${dt("tree.node.focus.ring.color")};
    outline-offset: ${dt("tree.node.focus.ring.offset")};
}

.p-tree-node-content.p-tree-node-selectable:not(.p-tree-node-selected):hover {
    background: ${dt("tree.node.hover.background")};
    color: ${dt("tree.node.hover.color")};
}

.p-tree-node-content.p-tree-node-selectable:not(.p-tree-node-selected):hover .p-tree-node-icon {
    color: ${dt("tree.node.icon.hover.color")};
}

.p-tree-node-content.p-tree-node-selected {
    background: ${dt("tree.node.selected.background")};
    color: ${dt("tree.node.selected.color")};
}

.p-tree-node-content.p-tree-node-selected .p-tree-node-toggle-button {
    color: inherit;
}

.p-tree-node-toggle-button {
    cursor: pointer;
    user-select: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
    flex-shrink: 0;
    width: ${dt("tree.node.toggle.button.size")};
    height: ${dt("tree.node.toggle.button.size")};
    color: ${dt("tree.node.toggle.button.color")};
    border: 0 none;
    background: transparent;
    border-radius: ${dt("tree.node.toggle.button.border.radius")};
    transition: background ${dt("tree.transition.duration")}, color ${dt("tree.transition.duration")}, border-color ${dt("tree.transition.duration")}, outline-color ${dt("tree.transition.duration")}, box-shadow ${dt("tree.transition.duration")};
    outline-color: transparent;
    padding: 0;
}

.p-tree-node-toggle-button:enabled:hover {
    background: ${dt("tree.node.toggle.button.hover.background")};
    color: ${dt("tree.node.toggle.button.hover.color")};
}

.p-tree-node-content.p-tree-node-selected .p-tree-node-toggle-button:hover {
    background: ${dt("tree.node.toggle.button.selected.hover.background")};
    color: ${dt("tree.node.toggle.button.selected.hover.color")};
}

.p-tree-root {
    overflow: auto;
}

.p-tree-node-selectable {
    cursor: pointer;
    user-select: none;
}

.p-tree-node-leaf > .p-tree-node-content .p-tree-node-toggle-button {
    visibility: hidden;
}

.p-tree-node-icon {
    color: ${dt("tree.node.icon.color")};
    transition: color ${dt("tree.transition.duration")};
}

.p-tree-node-content.p-tree-node-selected .p-tree-node-icon {
    color: ${dt("tree.node.icon.selected.color")};
}

.p-tree-filter-input {
    width: 100%;
}

.p-tree-loading {
    position: relative;
    height: 100%;
}

.p-tree-loading-icon {
    font-size: ${dt("tree.loading.icon.size")};
    width: ${dt("tree.loading.icon.size")};
    height: ${dt("tree.loading.icon.size")};
}

.p-tree .p-tree-mask {
    position: absolute;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}

.p-tree-flex-scrollable {
    display: flex;
    flex: 1;
    height: 100%;
    flex-direction: column;
}

.p-tree-flex-scrollable .p-tree-root {
    flex: 1;
}

/* For PrimeNG */
.p-tree .p-tree-node-droppoint {
    height: 4px;
    list-style-type: none;
}

.p-tree .p-tree-node-droppoint-active {
    border: 0 none;
    background-color: ${dt("primary.color")};
}

.p-tree-node-content.p-tree-node-dragover {
    background: ${dt("tree.node.hover.background")};
    color: ${dt("tree.node.hover.color")};
}

.p-tree-node-content.p-tree-node-dragover .p-tree-node-icon {
    color: ${dt("tree.node.icon.hover.color")};
}

.p-tree-horizontal {
    width: auto;
    padding-inline-start: 0;
    padding-inline-end: 0;
    overflow: auto;
}

.p-tree.p-tree-horizontal table,
.p-tree.p-tree-horizontal tr,
.p-tree.p-tree-horizontal td {
    border-collapse: collapse;
    margin: 0;
    padding: 0;
    vertical-align: middle;
}

.p-tree-horizontal .p-tree-node-content {
    font-weight: normal;
    padding: 0.4em 1em 0.4em 0.2em;
    display: flex;
    align-items: center;
}

.p-tree-horizontal .p-tree-node-parent .p-tree-node-content {
    font-weight: normal;
    white-space: nowrap;
}

.p-tree.p-tree-horizontal .p-tree-node.p-tree-node-leaf,
.p-tree.p-tree-horizontal .p-tree-node.p-tree-node-collapsed {
    padding-inline-end: 0;
}

.p-tree.p-tree-horizontal .p-tree-node-children {
    padding: 0;
    margin: 0;
}

.p-tree.p-tree-horizontal .p-tree-node-connector {
    width: 1px;
}

.p-tree.p-tree-horizontal .p-tree-node-connector-table {
    height: 100%;
    width: 1px;
}

.p-tree.p-tree-horizontal table {
    height: 0;
}
`;
var classes2 = {
  root: ({
    instance
  }) => ({
    "p-tree p-component": true,
    "p-tree-selectable": instance.selectionMode != null,
    "p-tree-loading": instance.loading,
    "p-tree-flex-scrollable": instance.scrollHeight === "flex",
    "p-tree-node-dragover": instance.dragHover
  }),
  mask: "p-tree-mask p-overlay-mask",
  loadingIcon: "p-tree-loading-icon",
  pcFilterInput: "p-tree-filter-input",
  wrapper: "p-tree-root",
  //TODO: discuss
  rootChildren: "p-tree-root-children",
  node: ({
    instance
  }) => ({
    "p-tree-node": true,
    "p-tree-node-leaf": instance.isLeaf()
  }),
  nodeContent: ({
    instance
  }) => ({
    "p-tree-node-content": true,
    [instance.styleClass]: !!instance.styleClass,
    "p-tree-node-selectable": instance.selectable,
    "p-tree-node-dragover": instance.draghoverNode,
    "p-tree-node-selected": instance.selectionMode === "checkbox" && instance.tree.highlightOnSelect ? instance.checked : instance.selected
  }),
  nodeToggleButton: "p-tree-node-toggle-button",
  nodeToggleIcon: "p-tree-node-toggle-icon",
  nodeCheckbox: "p-tree-node-checkbox",
  nodeIcon: "p-tree-node-icon",
  nodeLabel: "p-tree-node-label",
  nodeChildren: "p-tree-node-children"
};
var TreeStyle = class _TreeStyle extends BaseStyle {
  name = "tree";
  theme = theme2;
  classes = classes2;
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵTreeStyle_BaseFactory;
    return function TreeStyle_Factory(__ngFactoryType__) {
      return (ɵTreeStyle_BaseFactory || (ɵTreeStyle_BaseFactory = ɵɵgetInheritedFactory(_TreeStyle)))(__ngFactoryType__ || _TreeStyle);
    };
  })();
  static ɵprov = ɵɵdefineInjectable({
    token: _TreeStyle,
    factory: _TreeStyle.ɵfac
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(TreeStyle, [{
    type: Injectable
  }], null, null);
})();
var TreeClasses;
(function(TreeClasses2) {
  TreeClasses2["root"] = "p-tree";
  TreeClasses2["mask"] = "p-tree-mask";
  TreeClasses2["loadingIcon"] = "p-tree-loading-icon";
  TreeClasses2["pcFilterInput"] = "p-tree-filter-input";
  TreeClasses2["wrapper"] = "p-tree-root";
  TreeClasses2["rootChildren"] = "p-tree-root-children";
  TreeClasses2["node"] = "p-tree-node";
  TreeClasses2["nodeContent"] = "p-tree-node-content";
  TreeClasses2["nodeToggleButton"] = "p-tree-node-toggle-button";
  TreeClasses2["nodeToggleIcon"] = "p-tree-node-toggle-icon";
  TreeClasses2["nodeCheckbox"] = "p-tree-node-checkbox";
  TreeClasses2["nodeIcon"] = "p-tree-node-icon";
  TreeClasses2["nodeLabel"] = "p-tree-node-label";
  TreeClasses2["nodeChildren"] = "p-tree-node-children";
})(TreeClasses || (TreeClasses = {}));
var _c02 = (a0) => ({
  height: a0
});
var _c12 = (a0) => ({
  "p-tree-node-droppoint-active": a0
});
var _c22 = (a0) => ({
  $implicit: a0
});
var _c32 = (a0, a1) => ({
  $implicit: a0,
  partialSelected: a1,
  class: "p-tree-node-checkbox"
});
function UITreeNode_Conditional_0_li_0_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = ɵɵgetCurrentView();
    ɵɵelementStart(0, "li", 11);
    ɵɵlistener("drop", function UITreeNode_Conditional_0_li_0_Template_li_drop_0_listener($event) {
      ɵɵrestoreView(_r2);
      const ctx_r2 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r2.onDropPoint($event, -1));
    })("dragover", function UITreeNode_Conditional_0_li_0_Template_li_dragover_0_listener($event) {
      ɵɵrestoreView(_r2);
      const ctx_r2 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r2.onDropPointDragOver($event));
    })("dragenter", function UITreeNode_Conditional_0_li_0_Template_li_dragenter_0_listener($event) {
      ɵɵrestoreView(_r2);
      const ctx_r2 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r2.onDropPointDragEnter($event, -1));
    })("dragleave", function UITreeNode_Conditional_0_li_0_Template_li_dragleave_0_listener($event) {
      ɵɵrestoreView(_r2);
      const ctx_r2 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r2.onDropPointDragLeave($event));
    });
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵproperty("ngClass", ɵɵpureFunction1(2, _c12, ctx_r2.draghoverPrev));
    ɵɵattribute("aria-hidden", true);
  }
}
function UITreeNode_Conditional_0_ng_container_4_ng_container_1_ChevronRightIcon_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "ChevronRightIcon", 13);
  }
  if (rf & 2) {
    ɵɵproperty("styleClass", "p-tree-node-toggle-icon");
  }
}
function UITreeNode_Conditional_0_ng_container_4_ng_container_1_ChevronDownIcon_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "ChevronDownIcon", 13);
  }
  if (rf & 2) {
    ɵɵproperty("styleClass", "p-tree-node-toggle-icon");
  }
}
function UITreeNode_Conditional_0_ng_container_4_ng_container_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, UITreeNode_Conditional_0_ng_container_4_ng_container_1_ChevronRightIcon_1_Template, 1, 1, "ChevronRightIcon", 12)(2, UITreeNode_Conditional_0_ng_container_4_ng_container_1_ChevronDownIcon_2_Template, 1, 1, "ChevronDownIcon", 12);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(3);
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r2.node.expanded);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r2.node.expanded);
  }
}
function UITreeNode_Conditional_0_ng_container_4_ng_container_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵelement(1, "SpinnerIcon", 13);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    ɵɵadvance();
    ɵɵproperty("styleClass", "pi-spin p-tree-node-toggle-icon");
  }
}
function UITreeNode_Conditional_0_ng_container_4_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, UITreeNode_Conditional_0_ng_container_4_ng_container_1_Template, 3, 2, "ng-container", 5)(2, UITreeNode_Conditional_0_ng_container_4_ng_container_2_Template, 2, 1, "ng-container", 5);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r2.node.loading);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r2.loadingMode === "icon" && ctx_r2.node.loading);
  }
}
function UITreeNode_Conditional_0_span_5_1_ng_template_0_Template(rf, ctx) {
}
function UITreeNode_Conditional_0_span_5_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, UITreeNode_Conditional_0_span_5_1_ng_template_0_Template, 0, 0, "ng-template");
  }
}
function UITreeNode_Conditional_0_span_5_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "span", 14);
    ɵɵtemplate(1, UITreeNode_Conditional_0_span_5_1_Template, 1, 0, null, 15);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵproperty("ngTemplateOutlet", ctx_r2.tree.togglerIconTemplate || ctx_r2.tree._togglerIconTemplate)("ngTemplateOutletContext", ɵɵpureFunction1(2, _c22, ctx_r2.node.expanded));
  }
}
function UITreeNode_Conditional_0_p_checkbox_6_ng_container_1_ng_template_1_0_ng_template_0_Template(rf, ctx) {
}
function UITreeNode_Conditional_0_p_checkbox_6_ng_container_1_ng_template_1_0_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, UITreeNode_Conditional_0_p_checkbox_6_ng_container_1_ng_template_1_0_ng_template_0_Template, 0, 0, "ng-template");
  }
}
function UITreeNode_Conditional_0_p_checkbox_6_ng_container_1_ng_template_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, UITreeNode_Conditional_0_p_checkbox_6_ng_container_1_ng_template_1_0_Template, 1, 0, null, 15);
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(4);
    ɵɵproperty("ngTemplateOutlet", ctx_r2.tree.checkboxIconTemplate || ctx_r2.tree._checkboxIconTemplate)("ngTemplateOutletContext", ɵɵpureFunction2(2, _c32, ctx_r2.isSelected(), ctx_r2.node.partialSelected));
  }
}
function UITreeNode_Conditional_0_p_checkbox_6_ng_container_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, UITreeNode_Conditional_0_p_checkbox_6_ng_container_1_ng_template_1_Template, 1, 5, "ng-template", null, 0, ɵɵtemplateRefExtractor);
    ɵɵelementContainerEnd();
  }
}
function UITreeNode_Conditional_0_p_checkbox_6_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "p-checkbox", 16);
    ɵɵtemplate(1, UITreeNode_Conditional_0_p_checkbox_6_ng_container_1_Template, 3, 0, "ng-container", 5);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵproperty("ngModel", ctx_r2.isSelected())("binary", true)("indeterminate", ctx_r2.node.partialSelected)("disabled", ctx_r2.node.selectable === false)("variant", (ctx_r2.tree == null ? null : ctx_r2.tree.config.inputStyle()) === "filled" ? "filled" : "outlined" ? "filled" : "outlined")("tabindex", -1);
    ɵɵattribute("data-p-partialchecked", ctx_r2.node.partialSelected);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r2.tree.checkboxIconTemplate || ctx_r2.tree._checkboxIconTemplate);
  }
}
function UITreeNode_Conditional_0_span_7_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "span");
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵclassMap(ctx_r2.getIcon());
  }
}
function UITreeNode_Conditional_0_span_9_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "span");
    ɵɵtext(1);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵtextInterpolate(ctx_r2.node.label);
  }
}
function UITreeNode_Conditional_0_span_10_ng_container_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainer(0);
  }
}
function UITreeNode_Conditional_0_span_10_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "span");
    ɵɵtemplate(1, UITreeNode_Conditional_0_span_10_ng_container_1_Template, 1, 0, "ng-container", 15);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵproperty("ngTemplateOutlet", ctx_r2.tree.getTemplateForNode(ctx_r2.node))("ngTemplateOutletContext", ɵɵpureFunction1(2, _c22, ctx_r2.node));
  }
}
function UITreeNode_Conditional_0_ul_11_p_treeNode_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "p-treeNode", 19);
  }
  if (rf & 2) {
    const childNode_r4 = ctx.$implicit;
    const firstChild_r5 = ctx.first;
    const lastChild_r6 = ctx.last;
    const index_r7 = ctx.index;
    const ctx_r2 = ɵɵnextContext(3);
    ɵɵproperty("node", childNode_r4)("parentNode", ctx_r2.node)("firstChild", firstChild_r5)("lastChild", lastChild_r6)("index", index_r7)("itemSize", ctx_r2.itemSize)("level", ctx_r2.level + 1)("loadingMode", ctx_r2.loadingMode);
  }
}
function UITreeNode_Conditional_0_ul_11_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "ul", 17);
    ɵɵtemplate(1, UITreeNode_Conditional_0_ul_11_p_treeNode_1_Template, 1, 8, "p-treeNode", 18);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵstyleProp("display", ctx_r2.node.expanded ? "block" : "none");
    ɵɵadvance();
    ɵɵproperty("ngForOf", ctx_r2.node.children)("ngForTrackBy", ctx_r2.tree.trackBy.bind(ctx_r2));
  }
}
function UITreeNode_Conditional_0_li_12_Template(rf, ctx) {
  if (rf & 1) {
    const _r8 = ɵɵgetCurrentView();
    ɵɵelementStart(0, "li", 11);
    ɵɵlistener("drop", function UITreeNode_Conditional_0_li_12_Template_li_drop_0_listener($event) {
      ɵɵrestoreView(_r8);
      const ctx_r2 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r2.onDropPoint($event, 1));
    })("dragover", function UITreeNode_Conditional_0_li_12_Template_li_dragover_0_listener($event) {
      ɵɵrestoreView(_r8);
      const ctx_r2 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r2.onDropPointDragOver($event));
    })("dragenter", function UITreeNode_Conditional_0_li_12_Template_li_dragenter_0_listener($event) {
      ɵɵrestoreView(_r8);
      const ctx_r2 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r2.onDropPointDragEnter($event, 1));
    })("dragleave", function UITreeNode_Conditional_0_li_12_Template_li_dragleave_0_listener($event) {
      ɵɵrestoreView(_r8);
      const ctx_r2 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r2.onDropPointDragLeave($event));
    });
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext(2);
    ɵɵproperty("ngClass", ɵɵpureFunction1(2, _c12, ctx_r2.draghoverNext));
    ɵɵattribute("aria-hidden", true);
  }
}
function UITreeNode_Conditional_0_Template(rf, ctx) {
  if (rf & 1) {
    const _r1 = ɵɵgetCurrentView();
    ɵɵtemplate(0, UITreeNode_Conditional_0_li_0_Template, 1, 4, "li", 1);
    ɵɵelementStart(1, "li", 2);
    ɵɵlistener("keydown", function UITreeNode_Conditional_0_Template_li_keydown_1_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onKeyDown($event));
    });
    ɵɵelementStart(2, "div", 3);
    ɵɵlistener("click", function UITreeNode_Conditional_0_Template_div_click_2_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onNodeClick($event));
    })("contextmenu", function UITreeNode_Conditional_0_Template_div_contextmenu_2_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onNodeRightClick($event));
    })("touchend", function UITreeNode_Conditional_0_Template_div_touchend_2_listener() {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onNodeTouchEnd());
    })("drop", function UITreeNode_Conditional_0_Template_div_drop_2_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onDropNode($event));
    })("dragover", function UITreeNode_Conditional_0_Template_div_dragover_2_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onDropNodeDragOver($event));
    })("dragenter", function UITreeNode_Conditional_0_Template_div_dragenter_2_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onDropNodeDragEnter($event));
    })("dragleave", function UITreeNode_Conditional_0_Template_div_dragleave_2_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onDropNodeDragLeave($event));
    })("dragstart", function UITreeNode_Conditional_0_Template_div_dragstart_2_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onDragStart($event));
    })("dragend", function UITreeNode_Conditional_0_Template_div_dragend_2_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.onDragStop($event));
    });
    ɵɵelementStart(3, "button", 4);
    ɵɵlistener("click", function UITreeNode_Conditional_0_Template_button_click_3_listener($event) {
      ɵɵrestoreView(_r1);
      const ctx_r2 = ɵɵnextContext();
      return ɵɵresetView(ctx_r2.toggle($event));
    });
    ɵɵtemplate(4, UITreeNode_Conditional_0_ng_container_4_Template, 3, 2, "ng-container", 5)(5, UITreeNode_Conditional_0_span_5_Template, 2, 4, "span", 6);
    ɵɵelementEnd();
    ɵɵtemplate(6, UITreeNode_Conditional_0_p_checkbox_6_Template, 2, 8, "p-checkbox", 7)(7, UITreeNode_Conditional_0_span_7_Template, 1, 2, "span", 8);
    ɵɵelementStart(8, "span", 9);
    ɵɵtemplate(9, UITreeNode_Conditional_0_span_9_Template, 2, 1, "span", 5)(10, UITreeNode_Conditional_0_span_10_Template, 2, 4, "span", 5);
    ɵɵelementEnd()();
    ɵɵtemplate(11, UITreeNode_Conditional_0_ul_11_Template, 2, 4, "ul", 10);
    ɵɵelementEnd();
    ɵɵtemplate(12, UITreeNode_Conditional_0_li_12_Template, 1, 4, "li", 1);
  }
  if (rf & 2) {
    const ctx_r2 = ɵɵnextContext();
    ɵɵproperty("ngIf", ctx_r2.tree.droppableNodes);
    ɵɵadvance();
    ɵɵstyleMap(ctx_r2.node.style);
    ɵɵproperty("ngClass", ctx_r2.nodeClass)("ngStyle", ɵɵpureFunction1(27, _c02, ctx_r2.itemSize + "px"));
    ɵɵattribute("aria-label", ctx_r2.node.label)("aria-checked", ctx_r2.checked)("aria-setsize", ctx_r2.node.children ? ctx_r2.node.children.length : 0)("aria-selected", ctx_r2.selected)("aria-expanded", ctx_r2.node.expanded)("aria-posinset", ctx_r2.index + 1)("aria-level", ctx_r2.level + 1)("tabindex", ctx_r2.index === 0 ? 0 : -1)("data-id", ctx_r2.node.key);
    ɵɵadvance();
    ɵɵstyleProp("padding-left", ctx_r2.level * ctx_r2.indentation + "rem");
    ɵɵproperty("ngClass", ctx_r2.nodeContentClass)("draggable", ctx_r2.tree.draggableNodes);
    ɵɵadvance();
    ɵɵattribute("data-pc-section", "toggler");
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r2.tree.togglerIconTemplate && !ctx_r2.tree._togglerIconTemplate);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r2.tree.togglerIconTemplate || ctx_r2.tree._togglerIconTemplate);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r2.tree.selectionMode == "checkbox");
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r2.node.icon || ctx_r2.node.expandedIcon || ctx_r2.node.collapsedIcon);
    ɵɵadvance(2);
    ɵɵproperty("ngIf", !ctx_r2.tree.getTemplateForNode(ctx_r2.node));
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r2.tree.getTemplateForNode(ctx_r2.node));
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r2.tree.virtualScroll && ctx_r2.node.children && ctx_r2.node.expanded);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r2.tree.droppableNodes && ctx_r2.lastChild);
  }
}
var _c4 = ["filter"];
var _c5 = ["node"];
var _c6 = ["header"];
var _c7 = ["footer"];
var _c8 = ["loader"];
var _c9 = ["empty"];
var _c10 = ["togglericon"];
var _c11 = ["checkboxicon"];
var _c122 = ["loadingicon"];
var _c13 = ["filtericon"];
var _c14 = ["scroller"];
var _c15 = ["wrapper"];
var _c16 = (a0) => ({
  options: a0
});
function Tree_div_1_i_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "i");
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵclassMap("p-tree-loading-icon pi-spin " + ctx_r0.loadingIcon);
  }
}
function Tree_div_1_ng_container_2_SpinnerIcon_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "SpinnerIcon", 16);
  }
  if (rf & 2) {
    ɵɵproperty("spin", true)("styleClass", "p-tree-loading-icon");
  }
}
function Tree_div_1_ng_container_2_span_2_1_ng_template_0_Template(rf, ctx) {
}
function Tree_div_1_ng_container_2_span_2_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Tree_div_1_ng_container_2_span_2_1_ng_template_0_Template, 0, 0, "ng-template");
  }
}
function Tree_div_1_ng_container_2_span_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "span", 17);
    ɵɵtemplate(1, Tree_div_1_ng_container_2_span_2_1_Template, 1, 0, null, 9);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(3);
    ɵɵadvance();
    ɵɵproperty("ngTemplateOutlet", ctx_r0.loadingIconTemplate || ctx_r0._loadingIconTemplate);
  }
}
function Tree_div_1_ng_container_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, Tree_div_1_ng_container_2_SpinnerIcon_1_Template, 1, 2, "SpinnerIcon", 14)(2, Tree_div_1_ng_container_2_span_2_Template, 2, 1, "span", 15);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r0.loadingIconTemplate && !ctx_r0._loadingIconTemplate);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r0.loadingIconTemplate || ctx_r0._loadingIconTemplate);
  }
}
function Tree_div_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "div", 12);
    ɵɵtemplate(1, Tree_div_1_i_1_Template, 1, 2, "i", 13)(2, Tree_div_1_ng_container_2_Template, 3, 2, "ng-container", 10);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r0.loadingIcon);
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r0.loadingIcon);
  }
}
function Tree_ng_container_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainer(0);
  }
}
function Tree_Conditional_3_ng_container_0_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainer(0);
  }
}
function Tree_Conditional_3_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Tree_Conditional_3_ng_container_0_Template, 1, 0, "ng-container", 18);
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵproperty("ngTemplateOutlet", ctx_r0.filterTemplate || ctx_r0._filterTemplate)("ngTemplateOutletContext", ɵɵpureFunction1(2, _c22, ctx_r0.filterOptions));
  }
}
function Tree_Conditional_4_p_iconField_0_SearchIcon_4_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "SearchIcon", 21);
  }
}
function Tree_Conditional_4_p_iconField_0_span_5_1_ng_template_0_Template(rf, ctx) {
}
function Tree_Conditional_4_p_iconField_0_span_5_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Tree_Conditional_4_p_iconField_0_span_5_1_ng_template_0_Template, 0, 0, "ng-template");
  }
}
function Tree_Conditional_4_p_iconField_0_span_5_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "span");
    ɵɵtemplate(1, Tree_Conditional_4_p_iconField_0_span_5_1_Template, 1, 0, null, 9);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(3);
    ɵɵadvance();
    ɵɵproperty("ngTemplateOutlet", ctx_r0.filterIconTemplate || ctx_r0._filterIconTemplate);
  }
}
function Tree_Conditional_4_p_iconField_0_Template(rf, ctx) {
  if (rf & 1) {
    const _r2 = ɵɵgetCurrentView();
    ɵɵelementStart(0, "p-iconField")(1, "input", 19, 0);
    ɵɵlistener("keydown.enter", function Tree_Conditional_4_p_iconField_0_Template_input_keydown_enter_1_listener($event) {
      ɵɵrestoreView(_r2);
      return ɵɵresetView($event.preventDefault());
    })("input", function Tree_Conditional_4_p_iconField_0_Template_input_input_1_listener($event) {
      ɵɵrestoreView(_r2);
      const ctx_r0 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r0._filter($event.target.value));
    });
    ɵɵelementEnd();
    ɵɵelementStart(3, "p-inputIcon");
    ɵɵtemplate(4, Tree_Conditional_4_p_iconField_0_SearchIcon_4_Template, 1, 0, "SearchIcon", 20)(5, Tree_Conditional_4_p_iconField_0_span_5_Template, 2, 1, "span", 10);
    ɵɵelementEnd()();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵattribute("placeholder", ctx_r0.filterPlaceholder);
    ɵɵadvance(3);
    ɵɵproperty("ngIf", !ctx_r0.filterIconTemplate && !ctx_r0._filterIconTemplate);
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r0.filterIconTemplate || ctx_r0._filterIconTemplate);
  }
}
function Tree_Conditional_4_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Tree_Conditional_4_p_iconField_0_Template, 6, 3, "p-iconField", 10);
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵproperty("ngIf", ctx_r0.filter);
  }
}
function Tree_ng_container_5_p_scroller_1_ng_template_2_ul_0_p_treeNode_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "p-treeNode", 27, 3);
  }
  if (rf & 2) {
    const rowNode_r4 = ctx.$implicit;
    const firstChild_r5 = ctx.first;
    const lastChild_r6 = ctx.last;
    const index_r7 = ctx.index;
    const scrollerOptions_r8 = ɵɵnextContext(2).options;
    const ctx_r0 = ɵɵnextContext(3);
    ɵɵproperty("level", rowNode_r4.level)("rowNode", rowNode_r4)("node", rowNode_r4.node)("parentNode", rowNode_r4.parent)("firstChild", firstChild_r5)("lastChild", lastChild_r6)("index", ctx_r0.getIndex(scrollerOptions_r8, index_r7))("itemSize", scrollerOptions_r8.itemSize)("indentation", ctx_r0.indentation)("loadingMode", ctx_r0.loadingMode);
  }
}
function Tree_ng_container_5_p_scroller_1_ng_template_2_ul_0_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "ul", 25);
    ɵɵtemplate(1, Tree_ng_container_5_p_scroller_1_ng_template_2_ul_0_p_treeNode_1_Template, 2, 10, "p-treeNode", 26);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r8 = ɵɵnextContext();
    const items_r10 = ctx_r8.$implicit;
    const scrollerOptions_r8 = ctx_r8.options;
    const ctx_r0 = ɵɵnextContext(3);
    ɵɵstyleMap(scrollerOptions_r8.contentStyle);
    ɵɵproperty("ngClass", scrollerOptions_r8.contentStyleClass);
    ɵɵattribute("aria-label", ctx_r0.ariaLabel)("aria-labelledby", ctx_r0.ariaLabelledBy);
    ɵɵadvance();
    ɵɵproperty("ngForOf", items_r10)("ngForTrackBy", ctx_r0.trackBy);
  }
}
function Tree_ng_container_5_p_scroller_1_ng_template_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Tree_ng_container_5_p_scroller_1_ng_template_2_ul_0_Template, 2, 7, "ul", 24);
  }
  if (rf & 2) {
    const items_r10 = ctx.$implicit;
    ɵɵproperty("ngIf", items_r10);
  }
}
function Tree_ng_container_5_p_scroller_1_ng_container_4_ng_template_1_ng_container_0_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainer(0);
  }
}
function Tree_ng_container_5_p_scroller_1_ng_container_4_ng_template_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Tree_ng_container_5_p_scroller_1_ng_container_4_ng_template_1_ng_container_0_Template, 1, 0, "ng-container", 18);
  }
  if (rf & 2) {
    const scrollerOptions_r11 = ctx.options;
    const ctx_r0 = ɵɵnextContext(4);
    ɵɵproperty("ngTemplateOutlet", ctx_r0.loaderTemplate || ctx_r0._loaderTemplate)("ngTemplateOutletContext", ɵɵpureFunction1(2, _c16, scrollerOptions_r11));
  }
}
function Tree_ng_container_5_p_scroller_1_ng_container_4_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, Tree_ng_container_5_p_scroller_1_ng_container_4_ng_template_1_Template, 1, 4, "ng-template", null, 4, ɵɵtemplateRefExtractor);
    ɵɵelementContainerEnd();
  }
}
function Tree_ng_container_5_p_scroller_1_Template(rf, ctx) {
  if (rf & 1) {
    const _r3 = ɵɵgetCurrentView();
    ɵɵelementStart(0, "p-scroller", 23, 1);
    ɵɵlistener("onScroll", function Tree_ng_container_5_p_scroller_1_Template_p_scroller_onScroll_0_listener($event) {
      ɵɵrestoreView(_r3);
      const ctx_r0 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r0.onScroll.emit($event));
    })("onScrollIndexChange", function Tree_ng_container_5_p_scroller_1_Template_p_scroller_onScrollIndexChange_0_listener($event) {
      ɵɵrestoreView(_r3);
      const ctx_r0 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r0.onScrollIndexChange.emit($event));
    })("onLazyLoad", function Tree_ng_container_5_p_scroller_1_Template_p_scroller_onLazyLoad_0_listener($event) {
      ɵɵrestoreView(_r3);
      const ctx_r0 = ɵɵnextContext(2);
      return ɵɵresetView(ctx_r0.onLazyLoad.emit($event));
    });
    ɵɵtemplate(2, Tree_ng_container_5_p_scroller_1_ng_template_2_Template, 1, 1, "ng-template", null, 2, ɵɵtemplateRefExtractor)(4, Tree_ng_container_5_p_scroller_1_ng_container_4_Template, 3, 0, "ng-container", 10);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵstyleMap(ɵɵpureFunction1(9, _c02, ctx_r0.scrollHeight !== "flex" ? ctx_r0.scrollHeight : void 0));
    ɵɵproperty("items", ctx_r0.serializedValue)("tabindex", -1)("scrollHeight", ctx_r0.scrollHeight !== "flex" ? void 0 : "100%")("itemSize", ctx_r0.virtualScrollItemSize || ctx_r0._virtualNodeHeight)("lazy", ctx_r0.lazy)("options", ctx_r0.virtualScrollOptions);
    ɵɵadvance(4);
    ɵɵproperty("ngIf", ctx_r0.loaderTemplate || ctx_r0._loaderTemplate);
  }
}
function Tree_ng_container_5_ng_container_2_ul_3_p_treeNode_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelement(0, "p-treeNode", 32);
  }
  if (rf & 2) {
    const node_r12 = ctx.$implicit;
    const firstChild_r13 = ctx.first;
    const lastChild_r14 = ctx.last;
    const index_r15 = ctx.index;
    const ctx_r0 = ɵɵnextContext(4);
    ɵɵproperty("node", node_r12)("firstChild", firstChild_r13)("lastChild", lastChild_r14)("index", index_r15)("level", 0)("loadingMode", ctx_r0.loadingMode);
  }
}
function Tree_ng_container_5_ng_container_2_ul_3_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "ul", 30);
    ɵɵtemplate(1, Tree_ng_container_5_ng_container_2_ul_3_p_treeNode_1_Template, 1, 6, "p-treeNode", 31);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(3);
    ɵɵattribute("aria-label", ctx_r0.ariaLabel)("aria-labelledby", ctx_r0.ariaLabelledBy);
    ɵɵadvance();
    ɵɵproperty("ngForOf", ctx_r0.getRootNode())("ngForTrackBy", ctx_r0.trackBy.bind(ctx_r0));
  }
}
function Tree_ng_container_5_ng_container_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵelementStart(1, "div", 28, 5);
    ɵɵtemplate(3, Tree_ng_container_5_ng_container_2_ul_3_Template, 2, 4, "ul", 29);
    ɵɵelementEnd();
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵstyleProp("max-height", ctx_r0.scrollHeight);
    ɵɵadvance(2);
    ɵɵproperty("ngIf", ctx_r0.getRootNode());
  }
}
function Tree_ng_container_5_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtemplate(1, Tree_ng_container_5_p_scroller_1_Template, 5, 11, "p-scroller", 22)(2, Tree_ng_container_5_ng_container_2_Template, 4, 3, "ng-container", 10);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵadvance();
    ɵɵproperty("ngIf", ctx_r0.virtualScroll);
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r0.virtualScroll);
  }
}
function Tree_div_6_ng_container_1_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainerStart(0);
    ɵɵtext(1);
    ɵɵelementContainerEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext(2);
    ɵɵadvance();
    ɵɵtextInterpolate1(" ", ctx_r0.emptyMessageLabel, " ");
  }
}
function Tree_div_6_2_ng_template_0_Template(rf, ctx) {
}
function Tree_div_6_2_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵtemplate(0, Tree_div_6_2_ng_template_0_Template, 0, 0, "ng-template", null, 6, ɵɵtemplateRefExtractor);
  }
}
function Tree_div_6_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementStart(0, "div", 33);
    ɵɵtemplate(1, Tree_div_6_ng_container_1_Template, 2, 1, "ng-container", 34)(2, Tree_div_6_2_Template, 2, 0, null, 9);
    ɵɵelementEnd();
  }
  if (rf & 2) {
    const ctx_r0 = ɵɵnextContext();
    ɵɵadvance();
    ɵɵproperty("ngIf", !ctx_r0.emptyMessageTemplate && !ctx_r0._emptyMessageTemplate)("ngIfElse", ctx_r0.emptyFilter);
    ɵɵadvance();
    ɵɵproperty("ngTemplateOutlet", ctx_r0.emptyMessageTemplate || ctx_r0._emptyMessageTemplate);
  }
}
function Tree_ng_container_7_Template(rf, ctx) {
  if (rf & 1) {
    ɵɵelementContainer(0);
  }
}
var UITreeNode = class _UITreeNode extends BaseComponent {
  static ICON_CLASS = "p-tree-node-icon ";
  rowNode;
  node;
  parentNode;
  root;
  index;
  firstChild;
  lastChild;
  level;
  indentation;
  itemSize;
  loadingMode;
  tree = inject(forwardRef(() => Tree));
  timeout;
  draghoverPrev;
  draghoverNext;
  draghoverNode;
  get selected() {
    return this.tree.selectionMode === "single" || this.tree.selectionMode === "multiple" ? this.isSelected() : void 0;
  }
  get checked() {
    return this.tree.selectionMode === "checkbox" ? this.isSelected() : void 0;
  }
  get nodeClass() {
    return this.tree._componentStyle.classes.node({
      instance: this
    });
  }
  get nodeContentClass() {
    return this.tree._componentStyle.classes.nodeContent({
      instance: this
    });
  }
  get selectable() {
    return this.node.selectable === false ? false : this.tree.selectionMode != null;
  }
  ngOnInit() {
    super.ngOnInit();
    this.node.parent = this.parentNode;
    const nativeElement = this.tree.el.nativeElement;
    const pDialogWrapper = nativeElement.closest("p-dialog");
    if (this.parentNode && !pDialogWrapper) {
      this.setAllNodesTabIndexes();
      this.tree.syncNodeOption(this.node, this.tree.value, "parent", this.tree.getNodeWithKey(this.parentNode.key, this.tree.value));
    }
  }
  getIcon() {
    let icon;
    if (this.node.icon) icon = this.node.icon;
    else icon = this.node.expanded && this.node.children && this.node.children?.length ? this.node.expandedIcon : this.node.collapsedIcon;
    return _UITreeNode.ICON_CLASS + " " + icon + " p-tree-node-icon";
  }
  isLeaf() {
    return this.tree.isNodeLeaf(this.node);
  }
  toggle(event) {
    if (this.node.expanded) this.collapse(event);
    else this.expand(event);
    event.stopPropagation();
  }
  expand(event) {
    this.node.expanded = true;
    if (this.tree.virtualScroll) {
      this.tree.updateSerializedValue();
      this.focusVirtualNode();
    }
    this.tree.onNodeExpand.emit({
      originalEvent: event,
      node: this.node
    });
  }
  collapse(event) {
    this.node.expanded = false;
    if (this.tree.virtualScroll) {
      this.tree.updateSerializedValue();
      this.focusVirtualNode();
    }
    this.tree.onNodeCollapse.emit({
      originalEvent: event,
      node: this.node
    });
  }
  onNodeClick(event) {
    this.tree.onNodeClick(event, this.node);
    event.preventDefault();
  }
  onNodeKeydown(event) {
    if (event.key === "Enter") {
      this.tree.onNodeClick(event, this.node);
    }
  }
  onNodeTouchEnd() {
    this.tree.onNodeTouchEnd();
  }
  onNodeRightClick(event) {
    this.tree.onNodeRightClick(event, this.node);
  }
  isSelected() {
    return this.tree.isSelected(this.node);
  }
  isSameNode(event) {
    return event.currentTarget && (event.currentTarget.isSameNode(event.target) || event.currentTarget.isSameNode(event.target.closest('[role="treeitem"]')));
  }
  onDropPoint(event, position) {
    event.preventDefault();
    let dragNode = this.tree.dragNode;
    let dragNodeIndex = this.tree.dragNodeIndex;
    let dragNodeScope = this.tree.dragNodeScope;
    let isValidDropPointIndex = this.tree.dragNodeTree === this.tree ? position === 1 || dragNodeIndex !== this.index - 1 : true;
    if (this.tree.allowDrop(dragNode, this.node, dragNodeScope) && isValidDropPointIndex) {
      let dropParams = __spreadValues({}, this.createDropPointEventMetadata(position));
      if (this.tree.validateDrop) {
        this.tree.onNodeDrop.emit({
          originalEvent: event,
          dragNode,
          dropNode: this.node,
          index: this.index,
          accept: () => {
            this.processPointDrop(dropParams);
          }
        });
      } else {
        this.processPointDrop(dropParams);
        this.tree.onNodeDrop.emit({
          originalEvent: event,
          dragNode,
          dropNode: this.node,
          index: this.index
        });
      }
    }
    this.draghoverPrev = false;
    this.draghoverNext = false;
  }
  processPointDrop(event) {
    let newNodeList = event.dropNode.parent ? event.dropNode.parent.children : this.tree.value;
    event.dragNodeSubNodes.splice(event.dragNodeIndex, 1);
    let dropIndex = this.index;
    if (event.position < 0) {
      dropIndex = event.dragNodeSubNodes === newNodeList ? event.dragNodeIndex > event.index ? event.index : event.index - 1 : event.index;
      newNodeList.splice(dropIndex, 0, event.dragNode);
    } else {
      dropIndex = newNodeList.length;
      newNodeList.push(event.dragNode);
    }
    this.tree.dragDropService.stopDrag({
      node: event.dragNode,
      subNodes: event.dropNode.parent ? event.dropNode.parent.children : this.tree.value,
      index: event.dragNodeIndex
    });
  }
  createDropPointEventMetadata(position) {
    return {
      dragNode: this.tree.dragNode,
      dragNodeIndex: this.tree.dragNodeIndex,
      dragNodeSubNodes: this.tree.dragNodeSubNodes,
      dropNode: this.node,
      index: this.index,
      position
    };
  }
  onDropPointDragOver(event) {
    event.dataTransfer.dropEffect = "move";
    event.preventDefault();
  }
  onDropPointDragEnter(event, position) {
    if (this.tree.allowDrop(this.tree.dragNode, this.node, this.tree.dragNodeScope)) {
      if (position < 0) this.draghoverPrev = true;
      else this.draghoverNext = true;
    }
  }
  onDropPointDragLeave(event) {
    this.draghoverPrev = false;
    this.draghoverNext = false;
  }
  onDragStart(event) {
    if (this.tree.draggableNodes && this.node.draggable !== false) {
      event.dataTransfer.setData("text", "data");
      this.tree.dragDropService.startDrag({
        tree: this,
        node: this.node,
        subNodes: this.node?.parent ? this.node.parent.children : this.tree.value,
        index: this.index,
        scope: this.tree.draggableScope
      });
    } else {
      event.preventDefault();
    }
  }
  onDragStop(event) {
    this.tree.dragDropService.stopDrag({
      node: this.node,
      subNodes: this.node?.parent ? this.node.parent.children : this.tree.value,
      index: this.index
    });
  }
  onDropNodeDragOver(event) {
    event.dataTransfer.dropEffect = "move";
    if (this.tree.droppableNodes) {
      event.preventDefault();
      event.stopPropagation();
    }
  }
  onDropNode(event) {
    if (this.tree.droppableNodes && this.node?.droppable !== false) {
      let dragNode = this.tree.dragNode;
      if (this.tree.allowDrop(dragNode, this.node, this.tree.dragNodeScope)) {
        let dropParams = __spreadValues({}, this.createDropNodeEventMetadata());
        if (this.tree.validateDrop) {
          this.tree.onNodeDrop.emit({
            originalEvent: event,
            dragNode,
            dropNode: this.node,
            index: this.index,
            accept: () => {
              this.processNodeDrop(dropParams);
            }
          });
        } else {
          this.processNodeDrop(dropParams);
          this.tree.onNodeDrop.emit({
            originalEvent: event,
            dragNode,
            dropNode: this.node,
            index: this.index
          });
        }
      }
    }
    event.preventDefault();
    event.stopPropagation();
    this.draghoverNode = false;
  }
  createDropNodeEventMetadata() {
    return {
      dragNode: this.tree.dragNode,
      dragNodeIndex: this.tree.dragNodeIndex,
      dragNodeSubNodes: this.tree.dragNodeSubNodes,
      dropNode: this.node
    };
  }
  processNodeDrop(event) {
    let dragNodeIndex = event.dragNodeIndex;
    event.dragNodeSubNodes.splice(dragNodeIndex, 1);
    if (event.dropNode.children) event.dropNode.children.push(event.dragNode);
    else event.dropNode.children = [event.dragNode];
    this.tree.dragDropService.stopDrag({
      node: event.dragNode,
      subNodes: event.dropNode.parent ? event.dropNode.parent.children : this.tree.value,
      index: dragNodeIndex
    });
  }
  onDropNodeDragEnter(event) {
    if (this.tree.droppableNodes && this.node?.droppable !== false && this.tree.allowDrop(this.tree.dragNode, this.node, this.tree.dragNodeScope)) {
      this.draghoverNode = true;
    }
  }
  onDropNodeDragLeave(event) {
    if (this.tree.droppableNodes) {
      let rect = event.currentTarget.getBoundingClientRect();
      if (event.x > rect.left + rect.width || event.x < rect.left || event.y >= Math.floor(rect.top + rect.height) || event.y < rect.top) {
        this.draghoverNode = false;
      }
    }
  }
  onKeyDown(event) {
    if (!this.isSameNode(event) || this.tree.contextMenu && this.tree.contextMenu.containerViewChild?.nativeElement.style.display === "block") {
      return;
    }
    switch (event.code) {
      case "ArrowDown":
        this.onArrowDown(event);
        break;
      case "ArrowUp":
        this.onArrowUp(event);
        break;
      case "ArrowRight":
        this.onArrowRight(event);
        break;
      case "ArrowLeft":
        this.onArrowLeft(event);
        break;
      case "Enter":
      case "Space":
      case "NumpadEnter":
        this.onEnter(event);
        break;
      case "Tab":
        this.setAllNodesTabIndexes();
        break;
      default:
        break;
    }
  }
  onArrowUp(event) {
    const nodeElement = event.target.getAttribute("data-pc-section") === "toggler" ? event.target.closest('[role="treeitem"]') : event.target.parentElement;
    if (nodeElement.previousElementSibling) {
      this.focusRowChange(nodeElement, nodeElement.previousElementSibling, this.findLastVisibleDescendant(nodeElement.previousElementSibling));
    } else {
      let parentNodeElement = this.getParentNodeElement(nodeElement);
      if (parentNodeElement) {
        this.focusRowChange(nodeElement, parentNodeElement);
      }
    }
    event.preventDefault();
  }
  onArrowDown(event) {
    const nodeElement = event.target.getAttribute("data-pc-section") === "toggler" ? event.target.closest('[role="treeitem"]') : event.target;
    const listElement = nodeElement.children[1];
    if (listElement && listElement.children.length > 0) {
      this.focusRowChange(nodeElement, listElement.children[0]);
    } else {
      if (nodeElement.parentElement.nextElementSibling) {
        this.focusRowChange(nodeElement, nodeElement.parentElement.nextElementSibling);
      } else {
        let nextSiblingAncestor = this.findNextSiblingOfAncestor(nodeElement.parentElement);
        if (nextSiblingAncestor) {
          this.focusRowChange(nodeElement, nextSiblingAncestor);
        }
      }
    }
    event.preventDefault();
  }
  onArrowRight(event) {
    if (!this.node?.expanded && !this.tree.isNodeLeaf(this.node)) {
      this.expand(event);
      event.currentTarget.tabIndex = -1;
      setTimeout(() => {
        this.onArrowDown(event);
      }, 1);
    }
    event.preventDefault();
  }
  onArrowLeft(event) {
    const nodeElement = event.target.getAttribute("data-pc-section") === "toggler" ? event.target.closest('[role="treeitem"]') : event.target;
    if (this.level === 0 && !this.node?.expanded) {
      return false;
    }
    if (this.node?.expanded) {
      this.collapse(event);
      return;
    }
    let parentNodeElement = this.getParentNodeElement(nodeElement.parentElement);
    if (parentNodeElement) {
      this.focusRowChange(event.currentTarget, parentNodeElement);
    }
    event.preventDefault();
  }
  onEnter(event) {
    this.tree.onNodeClick(event, this.node);
    this.setTabIndexForSelectionMode(event, this.tree.nodeTouched);
    event.preventDefault();
  }
  setAllNodesTabIndexes() {
    const nodes = find(this.tree.el.nativeElement, ".p-tree-node");
    const hasSelectedNode = [...nodes].some((node) => node.getAttribute("aria-selected") === "true" || node.getAttribute("aria-checked") === "true");
    [...nodes].forEach((node) => {
      node.tabIndex = -1;
    });
    if (hasSelectedNode) {
      const selectedNodes = [...nodes].filter((node) => node.getAttribute("aria-selected") === "true" || node.getAttribute("aria-checked") === "true");
      selectedNodes[0].tabIndex = 0;
      return;
    }
    if (nodes.length) {
      [...nodes][0].tabIndex = 0;
    }
  }
  setTabIndexForSelectionMode(event, nodeTouched) {
    if (this.tree.selectionMode !== null) {
      const elements = [...find(this.tree.el.nativeElement, '[role="treeitem"]')];
      event.currentTarget.tabIndex = nodeTouched === false ? -1 : 0;
      if (elements.every((element) => element.tabIndex === -1)) {
        elements[0].tabIndex = 0;
      }
    }
  }
  findNextSiblingOfAncestor(nodeElement) {
    let parentNodeElement = this.getParentNodeElement(nodeElement);
    if (parentNodeElement) {
      if (parentNodeElement.nextElementSibling) return parentNodeElement.nextElementSibling;
      else return this.findNextSiblingOfAncestor(parentNodeElement);
    } else {
      return null;
    }
  }
  findLastVisibleDescendant(nodeElement) {
    const listElement = Array.from(nodeElement.children).find((el) => hasClass(el, "p-tree-node"));
    const childrenListElement = listElement?.children[1];
    if (childrenListElement && childrenListElement.children.length > 0) {
      const lastChildElement = childrenListElement.children[childrenListElement.children.length - 1];
      return this.findLastVisibleDescendant(lastChildElement);
    } else {
      return nodeElement;
    }
  }
  getParentNodeElement(nodeElement) {
    const parentNodeElement = nodeElement.parentElement?.parentElement?.parentElement;
    return parentNodeElement?.tagName === "P-TREENODE" ? parentNodeElement : null;
  }
  focusNode(element) {
    if (this.tree.droppableNodes) element.children[1].focus();
    else element.children[0].focus();
  }
  focusRowChange(firstFocusableRow, currentFocusedRow, lastVisibleDescendant) {
    firstFocusableRow.tabIndex = "-1";
    currentFocusedRow.children[0].tabIndex = "0";
    this.focusNode(lastVisibleDescendant || currentFocusedRow);
  }
  focusVirtualNode() {
    this.timeout = setTimeout(() => {
      let node = findSingle(document.body, `[data-id="${this.node?.key ?? this.node?.data}"]`);
      focus(node);
    }, 1);
  }
  static ɵfac = /* @__PURE__ */ (() => {
    let ɵUITreeNode_BaseFactory;
    return function UITreeNode_Factory(__ngFactoryType__) {
      return (ɵUITreeNode_BaseFactory || (ɵUITreeNode_BaseFactory = ɵɵgetInheritedFactory(_UITreeNode)))(__ngFactoryType__ || _UITreeNode);
    };
  })();
  static ɵcmp = ɵɵdefineComponent({
    type: _UITreeNode,
    selectors: [["p-treeNode"]],
    inputs: {
      rowNode: "rowNode",
      node: "node",
      parentNode: "parentNode",
      root: [2, "root", "root", booleanAttribute],
      index: [2, "index", "index", numberAttribute],
      firstChild: [2, "firstChild", "firstChild", booleanAttribute],
      lastChild: [2, "lastChild", "lastChild", booleanAttribute],
      level: [2, "level", "level", numberAttribute],
      indentation: [2, "indentation", "indentation", numberAttribute],
      itemSize: [2, "itemSize", "itemSize", numberAttribute],
      loadingMode: "loadingMode"
    },
    standalone: true,
    features: [ɵɵInputTransformsFeature, ɵɵInheritDefinitionFeature, ɵɵStandaloneFeature],
    decls: 1,
    vars: 1,
    consts: [["icon", ""], ["class", "p-tree-node-droppoint", 3, "ngClass", "drop", "dragover", "dragenter", "dragleave", 4, "ngIf"], ["role", "treeitem", 3, "keydown", "ngClass", "ngStyle"], [3, "click", "contextmenu", "touchend", "drop", "dragover", "dragenter", "dragleave", "dragstart", "dragend", "ngClass", "draggable"], ["type", "button", "pRipple", "", "tabindex", "-1", 1, "p-tree-node-toggle-button", 3, "click"], [4, "ngIf"], ["class", "p-tree-node-toggle-icon", 4, "ngIf"], ["styleClass", "p-tree-node-checkbox", 3, "ngModel", "binary", "indeterminate", "disabled", "variant", "tabindex", 4, "ngIf"], [3, "class", 4, "ngIf"], [1, "p-tree-node-label"], ["class", "p-tree-node-children", "style", "display: none;", "role", "group", 3, "display", 4, "ngIf"], [1, "p-tree-node-droppoint", 3, "drop", "dragover", "dragenter", "dragleave", "ngClass"], [3, "styleClass", 4, "ngIf"], [3, "styleClass"], [1, "p-tree-node-toggle-icon"], [4, "ngTemplateOutlet", "ngTemplateOutletContext"], ["styleClass", "p-tree-node-checkbox", 3, "ngModel", "binary", "indeterminate", "disabled", "variant", "tabindex"], ["role", "group", 1, "p-tree-node-children", 2, "display", "none"], [3, "node", "parentNode", "firstChild", "lastChild", "index", "itemSize", "level", "loadingMode", 4, "ngFor", "ngForOf", "ngForTrackBy"], [3, "node", "parentNode", "firstChild", "lastChild", "index", "itemSize", "level", "loadingMode"]],
    template: function UITreeNode_Template(rf, ctx) {
      if (rf & 1) {
        ɵɵtemplate(0, UITreeNode_Conditional_0_Template, 13, 29);
      }
      if (rf & 2) {
        ɵɵconditional(ctx.node ? 0 : -1);
      }
    },
    dependencies: [_UITreeNode, CommonModule, NgClass, NgForOf, NgIf, NgTemplateOutlet, NgStyle, Ripple, Checkbox, FormsModule, NgControlStatus, NgModel, ChevronRightIcon, ChevronDownIcon, SpinnerIcon, SharedModule],
    encapsulation: 2
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(UITreeNode, [{
    type: Component,
    args: [{
      selector: "p-treeNode",
      standalone: true,
      imports: [CommonModule, Ripple, Checkbox, FormsModule, ChevronRightIcon, ChevronDownIcon, SpinnerIcon, SharedModule],
      template: `
        @if (node) {
            <li
                *ngIf="tree.droppableNodes"
                class="p-tree-node-droppoint"
                [attr.aria-hidden]="true"
                [ngClass]="{ 'p-tree-node-droppoint-active': draghoverPrev }"
                (drop)="onDropPoint($event, -1)"
                (dragover)="onDropPointDragOver($event)"
                (dragenter)="onDropPointDragEnter($event, -1)"
                (dragleave)="onDropPointDragLeave($event)"
            ></li>
            <li
                [ngClass]="nodeClass"
                [ngStyle]="{ height: itemSize + 'px' }"
                [style]="node.style"
                [attr.aria-label]="node.label"
                [attr.aria-checked]="checked"
                [attr.aria-setsize]="node.children ? node.children.length : 0"
                [attr.aria-selected]="selected"
                [attr.aria-expanded]="node.expanded"
                [attr.aria-posinset]="index + 1"
                [attr.aria-level]="level + 1"
                [attr.tabindex]="index === 0 ? 0 : -1"
                [attr.data-id]="node.key"
                role="treeitem"
                (keydown)="onKeyDown($event)"
            >
                <div
                    [ngClass]="nodeContentClass"
                    [style.paddingLeft]="level * indentation + 'rem'"
                    (click)="onNodeClick($event)"
                    (contextmenu)="onNodeRightClick($event)"
                    (touchend)="onNodeTouchEnd()"
                    (drop)="onDropNode($event)"
                    (dragover)="onDropNodeDragOver($event)"
                    (dragenter)="onDropNodeDragEnter($event)"
                    (dragleave)="onDropNodeDragLeave($event)"
                    [draggable]="tree.draggableNodes"
                    (dragstart)="onDragStart($event)"
                    (dragend)="onDragStop($event)"
                >
                    <button type="button" [attr.data-pc-section]="'toggler'" class="p-tree-node-toggle-button" (click)="toggle($event)" pRipple tabindex="-1">
                        <ng-container *ngIf="!tree.togglerIconTemplate && !tree._togglerIconTemplate">
                            <ng-container *ngIf="!node.loading">
                                <ChevronRightIcon *ngIf="!node.expanded" [styleClass]="'p-tree-node-toggle-icon'" />
                                <ChevronDownIcon *ngIf="node.expanded" [styleClass]="'p-tree-node-toggle-icon'" />
                            </ng-container>
                            <ng-container *ngIf="loadingMode === 'icon' && node.loading">
                                <SpinnerIcon [styleClass]="'pi-spin p-tree-node-toggle-icon'" />
                            </ng-container>
                        </ng-container>
                        <span *ngIf="tree.togglerIconTemplate || tree._togglerIconTemplate" class="p-tree-node-toggle-icon">
                            <ng-template *ngTemplateOutlet="tree.togglerIconTemplate || tree._togglerIconTemplate; context: { $implicit: node.expanded }"></ng-template>
                        </span>
                    </button>

                    <p-checkbox
                        [ngModel]="isSelected()"
                        styleClass="p-tree-node-checkbox"
                        [binary]="true"
                        [indeterminate]="node.partialSelected"
                        *ngIf="tree.selectionMode == 'checkbox'"
                        [disabled]="node.selectable === false"
                        [variant]="tree?.config.inputStyle() === 'filled' ? 'filled' : 'outlined' || tree?.config.inputVariant() === 'filled' ? 'filled' : 'outlined'"
                        [attr.data-p-partialchecked]="node.partialSelected"
                        [tabindex]="-1"
                    >
                        <ng-container *ngIf="tree.checkboxIconTemplate || tree._checkboxIconTemplate">
                            <ng-template #icon>
                                <ng-template
                                    *ngTemplateOutlet="
                                        tree.checkboxIconTemplate || tree._checkboxIconTemplate;
                                        context: {
                                            $implicit: isSelected(),
                                            partialSelected: node.partialSelected,
                                            class: 'p-tree-node-checkbox'
                                        }
                                    "
                                ></ng-template>
                            </ng-template>
                        </ng-container>
                    </p-checkbox>

                    <span [class]="getIcon()" *ngIf="node.icon || node.expandedIcon || node.collapsedIcon"></span>
                    <span class="p-tree-node-label">
                        <span *ngIf="!tree.getTemplateForNode(node)">{{ node.label }}</span>
                        <span *ngIf="tree.getTemplateForNode(node)">
                            <ng-container *ngTemplateOutlet="tree.getTemplateForNode(node); context: { $implicit: node }"></ng-container>
                        </span>
                    </span>
                </div>
                <ul class="p-tree-node-children" style="display: none;" *ngIf="!tree.virtualScroll && node.children && node.expanded" [style.display]="node.expanded ? 'block' : 'none'" role="group">
                    <p-treeNode
                        *ngFor="let childNode of node.children; let firstChild = first; let lastChild = last; let index = index; trackBy: tree.trackBy.bind(this)"
                        [node]="childNode"
                        [parentNode]="node"
                        [firstChild]="firstChild"
                        [lastChild]="lastChild"
                        [index]="index"
                        [itemSize]="itemSize"
                        [level]="level + 1"
                        [loadingMode]="loadingMode"
                    ></p-treeNode>
                </ul>
            </li>

            <li
                *ngIf="tree.droppableNodes && lastChild"
                class="p-tree-node-droppoint"
                [ngClass]="{ 'p-tree-node-droppoint-active': draghoverNext }"
                (drop)="onDropPoint($event, 1)"
                [attr.aria-hidden]="true"
                (dragover)="onDropPointDragOver($event)"
                (dragenter)="onDropPointDragEnter($event, 1)"
                (dragleave)="onDropPointDragLeave($event)"
            ></li>
        }
    `,
      encapsulation: ViewEncapsulation$1.None
    }]
  }], null, {
    rowNode: [{
      type: Input
    }],
    node: [{
      type: Input
    }],
    parentNode: [{
      type: Input
    }],
    root: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    index: [{
      type: Input,
      args: [{
        transform: numberAttribute
      }]
    }],
    firstChild: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    lastChild: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    level: [{
      type: Input,
      args: [{
        transform: numberAttribute
      }]
    }],
    indentation: [{
      type: Input,
      args: [{
        transform: numberAttribute
      }]
    }],
    itemSize: [{
      type: Input,
      args: [{
        transform: numberAttribute
      }]
    }],
    loadingMode: [{
      type: Input
    }]
  });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && ɵsetClassDebugInfo(UITreeNode, {
    className: "UITreeNode"
  });
})();
var Tree = class _Tree extends BaseComponent {
  dragDropService;
  /**
   * An array of treenodes.
   * @group Props
   */
  value;
  /**
   * Defines the selection mode.
   * @group Props
   */
  selectionMode;
  /**
   * Loading mode display.
   * @group Props
   */
  loadingMode = "mask";
  /**
   * A single treenode instance or an array to refer to the selections.
   * @group Props
   */
  selection;
  /**
   * Inline style of the component.
   * @group Props
   */
  style;
  /**
   * Style class of the component.
   * @group Props
   */
  styleClass;
  /**
   * Context menu instance.
   * @group Props
   */
  contextMenu;
  /**
   * Scope of the draggable nodes to match a droppableScope.
   * @group Props
   */
  draggableScope;
  /**
   * Scope of the droppable nodes to match a draggableScope.
   * @group Props
   */
  droppableScope;
  /**
   * Whether the nodes are draggable.
   * @group Props
   */
  draggableNodes;
  /**
   * Whether the nodes are droppable.
   * @group Props
   */
  droppableNodes;
  /**
   * Defines how multiple items can be selected, when true metaKey needs to be pressed to select or unselect an item and when set to false selection of each item can be toggled individually. On touch enabled devices, metaKeySelection is turned off automatically.
   * @group Props
   */
  metaKeySelection = false;
  /**
   * Whether checkbox selections propagate to ancestor nodes.
   * @group Props
   */
  propagateSelectionUp = true;
  /**
   * Whether checkbox selections propagate to descendant nodes.
   * @group Props
   */
  propagateSelectionDown = true;
  /**
   * Displays a loader to indicate data load is in progress.
   * @group Props
   */
  loading;
  /**
   * The icon to show while indicating data load is in progress.
   * @group Props
   */
  loadingIcon;
  /**
   * Text to display when there is no data.
   * @group Props
   */
  emptyMessage = "";
  /**
   * Used to define a string that labels the tree.
   * @group Props
   */
  ariaLabel;
  /**
   * Defines a string that labels the toggler icon for accessibility.
   * @group Props
   */
  togglerAriaLabel;
  /**
   * Establishes relationships between the component and label(s) where its value should be one or more element IDs.
   * @group Props
   */
  ariaLabelledBy;
  /**
   * When enabled, drop can be accepted or rejected based on condition defined at onNodeDrop.
   * @group Props
   */
  validateDrop;
  /**
   * When specified, displays an input field to filter the items.
   * @group Props
   */
  filter;
  /**
   * When filtering is enabled, filterBy decides which field or fields (comma separated) to search against.
   * @group Props
   */
  filterBy = "label";
  /**
   * Mode for filtering valid values are "lenient" and "strict". Default is lenient.
   * @group Props
   */
  filterMode = "lenient";
  /**
   * Mode for filtering valid values are "lenient" and "strict". Default is lenient.
   * @group Props
   */
  filterOptions;
  /**
   * Placeholder text to show when filter input is empty.
   * @group Props
   */
  filterPlaceholder;
  /**
   * Values after the tree nodes are filtered.
   * @group Props
   */
  filteredNodes;
  /**
   * Locale to use in filtering. The default locale is the host environment's current locale.
   * @group Props
   */
  filterLocale;
  /**
   * Height of the scrollable viewport.
   * @group Props
   */
  scrollHeight;
  /**
   * Defines if data is loaded and interacted with in lazy manner.
   * @group Props
   */
  lazy = false;
  /**
   * Whether the data should be loaded on demand during scroll.
   * @group Props
   */
  virtualScroll;
  /**
   * Height of an item in the list for VirtualScrolling.
   * @group Props
   */
  virtualScrollItemSize;
  /**
   * Whether to use the scroller feature. The properties of scroller component can be used like an object in it.
   * @group Props
   */
  virtualScrollOptions;
  /**
   * Indentation factor for spacing of the nested node when virtual scrolling is enabled.
   * @group Props
   */
  indentation = 1.5;
  /**
   * Custom templates of the component.
   * @group Props
   */
  _templateMap;
  /**
   * Function to optimize the node list rendering, default algorithm checks for object identity.
   * @group Props
   */
  trackBy = (index, item) => item;
  /**
   * Highlights the node on select.
   * @group Props
   */
  highlightOnSelect = false;
  /**
   * Height of the node.
   * @group Props
   * @deprecated use virtualScrollItemSize property instead.
   */
  _virtualNodeHeight;
  get virtualNodeHeight() {
    return this._virtualNodeHeight;
  }
  set virtualNodeHeight(val) {
    this._virtualNodeHeight = val;
    console.log("The virtualNodeHeight property is deprecated, use virtualScrollItemSize property instead.");
  }
  /**
   * Callback to invoke on selection change.
   * @param {(TreeNode<any> | TreeNode<any>[] | null)} event - Custom selection change event.
   * @group Emits
   */
  selectionChange = new EventEmitter();
  /**
   * Callback to invoke when a node is selected.
   * @param {TreeNodeSelectEvent} event - Node select event.
   * @group Emits
   */
  onNodeSelect = new EventEmitter();
  /**
   * Callback to invoke when a node is unselected.
   * @param {TreeNodeUnSelectEvent} event - Node unselect event.
   * @group Emits
   */
  onNodeUnselect = new EventEmitter();
  /**
   * Callback to invoke when a node is expanded.
   * @param {TreeNodeExpandEvent} event - Node expand event.
   * @group Emits
   */
  onNodeExpand = new EventEmitter();
  /**
   * Callback to invoke when a node is collapsed.
   * @param {TreeNodeCollapseEvent} event - Node collapse event.
   * @group Emits
   */
  onNodeCollapse = new EventEmitter();
  /**
   * Callback to invoke when a node is selected with right click.
   * @param {onNodeContextMenuSelect} event - Node context menu select event.
   * @group Emits
   */
  onNodeContextMenuSelect = new EventEmitter();
  /**
   * Callback to invoke when a node is dropped.
   * @param {TreeNodeDropEvent} event - Node drop event.
   * @group Emits
   */
  onNodeDrop = new EventEmitter();
  /**
   * Callback to invoke in lazy mode to load new data.
   * @param {TreeLazyLoadEvent} event - Custom lazy load event.
   * @group Emits
   */
  onLazyLoad = new EventEmitter();
  /**
   * Callback to invoke in virtual scroll mode when scroll position changes.
   * @param {TreeScrollEvent} event - Custom scroll event.
   * @group Emits
   */
  onScroll = new EventEmitter();
  /**
   * Callback to invoke in virtual scroll mode when scroll position and item's range in view changes.
   * @param {TreeScrollIndexChangeEvent} event - Scroll index change event.
   * @group Emits
   */
  onScrollIndexChange = new EventEmitter();
  /**
   * Callback to invoke when data is filtered.
   * @param {TreeFilterEvent} event - Custom filter event.
   * @group Emits
   */
  onFilter = new EventEmitter();
  /**
   * Filter template.
   * @group Templates
   */
  filterTemplate;
  /**
   * Node template.
   * @group Templates
   */
  nodeTemplate;
  /**
   * Header template.
   * @group Templates
   */
  headerTemplate;
  /**
   * Footer template.
   * @group Templates
   */
  footerTemplate;
  /**
   * Loader template.
   * @group Templates
   */
  loaderTemplate;
  /**
   * Empty message template.
   * @group Templates
   */
  emptyMessageTemplate;
  /**
   * Toggler icon template.
   * @group Templates
   */
  togglerIconTemplate;
  /**
   * Checkbox icon template.
   * @group Templates
   */
  checkboxIconTemplate;
  /**
   * Loading icon template.
   * @group Templates
   */
  loadingIconTemplate;
  /**
   * Filter icon template.
   * @group Templates
   */
  filterIconTemplate;
  filterViewChild;
  scroller;
  wrapperViewChild;
  templates;
  _headerTemplate;
  _emptyMessageTemplate;
  _footerTemplate;
  _loaderTemplate;
  _togglerIconTemplate;
  _checkboxIconTemplate;
  _loadingIconTemplate;
  _filterIconTemplate;
  _filterTemplate;
  ngAfterContentInit() {
    if (this.templates.length) {
      this._templateMap = {};
    }
    this.templates.forEach((item) => {
      switch (item.getType()) {
        case "header":
          this._headerTemplate = item.template;
          break;
        case "empty":
          this._emptyMessageTemplate = item.template;
          break;
        case "footer":
          this._footerTemplate = item.template;
          break;
        case "loader":
          this._loaderTemplate = item.template;
          break;
        case "togglericon":
          this._togglerIconTemplate = item.template;
          break;
        case "checkboxicon":
          this._checkboxIconTemplate = item.template;
          break;
        case "loadingicon":
          this._loadingIconTemplate = item.template;
          break;
        case "filtericon":
          this._filterIconTemplate = item.template;
          break;
        case "filter":
          this._filterTemplate = item.template;
          break;
        default:
          this._templateMap[item.name] = item.template;
          break;
      }
    });
  }
  serializedValue;
  nodeTouched;
  dragNodeTree;
  dragNode;
  dragNodeSubNodes;
  dragNodeIndex;
  dragNodeScope;
  dragHover;
  dragStartSubscription;
  dragStopSubscription;
  _componentStyle = inject(TreeStyle);
  constructor(dragDropService) {
    super();
    this.dragDropService = dragDropService;
  }
  ngOnInit() {
    super.ngOnInit();
    if (this.filterBy) {
      this.filterOptions = {
        filter: (value) => this._filter(value),
        reset: () => this.resetFilter()
      };
    }
    if (this.droppableNodes) {
      this.dragStartSubscription = this.dragDropService.dragStart$.subscribe((event) => {
        this.dragNodeTree = event.tree;
        this.dragNode = event.node;
        this.dragNodeSubNodes = event.subNodes;
        this.dragNodeIndex = event.index;
        this.dragNodeScope = event.scope;
      });
      this.dragStopSubscription = this.dragDropService.dragStop$.subscribe((event) => {
        this.dragNodeTree = null;
        this.dragNode = null;
        this.dragNodeSubNodes = null;
        this.dragNodeIndex = null;
        this.dragNodeScope = null;
        this.dragHover = false;
      });
    }
  }
  ngOnChanges(simpleChange) {
    super.ngOnChanges(simpleChange);
    if (simpleChange.value) {
      this.updateSerializedValue();
      if (this.hasFilterActive()) {
        this._filter(this.filterViewChild.nativeElement.value);
      }
    }
  }
  get containerClass() {
    return this._componentStyle.classes.root({
      instance: this
    });
  }
  get emptyMessageLabel() {
    return this.emptyMessage || this.config.getTranslation(TranslationKeys.EMPTY_MESSAGE);
  }
  updateSerializedValue() {
    this.serializedValue = [];
    this.serializeNodes(null, this.getRootNode(), 0, true);
  }
  serializeNodes(parent, nodes, level, visible) {
    if (nodes && nodes.length) {
      for (let node of nodes) {
        node.parent = parent;
        const rowNode = {
          node,
          parent,
          level,
          visible: visible && (parent ? parent.expanded : true)
        };
        this.serializedValue.push(rowNode);
        if (rowNode.visible && node.expanded) {
          this.serializeNodes(node, node.children, level + 1, rowNode.visible);
        }
      }
    }
  }
  onNodeClick(event, node) {
    let eventTarget = event.target;
    if (hasClass(eventTarget, "p-tree-toggler") || hasClass(eventTarget, "p-tree-toggler-icon")) {
      return;
    } else if (this.selectionMode) {
      if (node.selectable === false) {
        node.style = "--p-focus-ring-color: none;";
        return;
      } else {
        node.style = "--p-focus-ring-color: var(--primary-color)";
      }
      if (this.hasFilteredNodes()) {
        node = this.getNodeWithKey(node.key, this.filteredNodes);
        if (!node) {
          return;
        }
      }
      let index = this.findIndexInSelection(node);
      let selected = index >= 0;
      if (this.isCheckboxSelectionMode()) {
        if (selected) {
          if (this.propagateSelectionDown) this.propagateDown(node, false);
          else this.selection = this.selection.filter((val, i) => i != index);
          if (this.propagateSelectionUp && node.parent) {
            this.propagateUp(node.parent, false);
          }
          this.selectionChange.emit(this.selection);
          this.onNodeUnselect.emit({
            originalEvent: event,
            node
          });
        } else {
          if (this.propagateSelectionDown) this.propagateDown(node, true);
          else this.selection = [...this.selection || [], node];
          if (this.propagateSelectionUp && node.parent) {
            this.propagateUp(node.parent, true);
          }
          this.selectionChange.emit(this.selection);
          this.onNodeSelect.emit({
            originalEvent: event,
            node
          });
        }
      } else {
        let metaSelection = this.nodeTouched ? false : this.metaKeySelection;
        if (metaSelection) {
          let metaKey = event.metaKey || event.ctrlKey;
          if (selected && metaKey) {
            if (this.isSingleSelectionMode()) {
              this.selectionChange.emit(null);
            } else {
              this.selection = this.selection.filter((val, i) => i != index);
              this.selectionChange.emit(this.selection);
            }
            this.onNodeUnselect.emit({
              originalEvent: event,
              node
            });
          } else {
            if (this.isSingleSelectionMode()) {
              this.selectionChange.emit(node);
            } else if (this.isMultipleSelectionMode()) {
              this.selection = !metaKey ? [] : this.selection || [];
              this.selection = [...this.selection, node];
              this.selectionChange.emit(this.selection);
            }
            this.onNodeSelect.emit({
              originalEvent: event,
              node
            });
          }
        } else {
          if (this.isSingleSelectionMode()) {
            if (selected) {
              this.selection = null;
              this.onNodeUnselect.emit({
                originalEvent: event,
                node
              });
            } else {
              this.selection = node;
              setTimeout(() => {
                this.onNodeSelect.emit({
                  originalEvent: event,
                  node
                });
              });
            }
          } else {
            if (selected) {
              this.selection = this.selection.filter((val, i) => i != index);
              this.onNodeUnselect.emit({
                originalEvent: event,
                node
              });
            } else {
              this.selection = [...this.selection || [], node];
              setTimeout(() => {
                this.onNodeSelect.emit({
                  originalEvent: event,
                  node
                });
              });
            }
          }
          this.selectionChange.emit(this.selection);
        }
      }
    }
    this.nodeTouched = false;
  }
  onNodeTouchEnd() {
    this.nodeTouched = true;
  }
  onNodeRightClick(event, node) {
    if (this.contextMenu) {
      let eventTarget = event.target;
      if (eventTarget.className && eventTarget.className.indexOf("p-tree-toggler") === 0) {
        return;
      } else {
        let index = this.findIndexInSelection(node);
        let selected = index >= 0;
        if (!selected) {
          if (this.isSingleSelectionMode()) this.selectionChange.emit(node);
          else this.selectionChange.emit([node]);
        }
        this.contextMenu.show(event);
        this.onNodeContextMenuSelect.emit({
          originalEvent: event,
          node
        });
      }
    }
  }
  findIndexInSelection(node) {
    let index = -1;
    if (this.selectionMode && this.selection) {
      if (this.isSingleSelectionMode()) {
        let areNodesEqual = this.selection.key && this.selection.key === node.key || this.selection == node;
        index = areNodesEqual ? 0 : -1;
      } else {
        for (let i = 0; i < this.selection.length; i++) {
          let selectedNode = this.selection[i];
          let areNodesEqual = selectedNode.key && selectedNode.key === node.key || selectedNode == node;
          if (areNodesEqual) {
            index = i;
            break;
          }
        }
      }
    }
    return index;
  }
  syncNodeOption(node, parentNodes, option, value) {
    const _node = this.hasFilteredNodes() ? this.getNodeWithKey(node.key, parentNodes) : null;
    if (_node) {
      _node[option] = value || node[option];
    }
  }
  hasFilteredNodes() {
    return this.filter && this.filteredNodes && this.filteredNodes.length;
  }
  hasFilterActive() {
    return this.filter && this.filterViewChild?.nativeElement?.value.length > 0;
  }
  getNodeWithKey(key, nodes) {
    for (let node of nodes) {
      if (node.key === key) {
        return node;
      }
      if (node.children) {
        let matchedNode = this.getNodeWithKey(key, node.children);
        if (matchedNode) {
          return matchedNode;
        }
      }
    }
  }
  propagateUp(node, select) {
    if (node.children && node.children.length) {
      let selectedCount = 0;
      let childPartialSelected = false;
      for (let child of node.children) {
        if (this.isSelected(child)) {
          selectedCount++;
        } else if (child.partialSelected) {
          childPartialSelected = true;
        }
      }
      if (select && selectedCount == node.children.length) {
        this.selection = [...this.selection || [], node];
        node.partialSelected = false;
      } else {
        if (!select) {
          let index = this.findIndexInSelection(node);
          if (index >= 0) {
            this.selection = this.selection.filter((val, i) => i != index);
          }
        }
        if (childPartialSelected || selectedCount > 0 && selectedCount != node.children.length) node.partialSelected = true;
        else node.partialSelected = false;
      }
      this.syncNodeOption(node, this.filteredNodes, "partialSelected");
    }
    let parent = node.parent;
    if (parent) {
      this.propagateUp(parent, select);
    }
  }
  propagateDown(node, select) {
    let index = this.findIndexInSelection(node);
    if (select && index == -1) {
      this.selection = [...this.selection || [], node];
    } else if (!select && index > -1) {
      this.selection = this.selection.filter((val, i) => i != index);
    }
    node.partialSelected = false;
    this.syncNodeOption(node, this.filteredNodes, "partialSelected");
    if (node.children && node.children.length) {
      for (let child of node.children) {
        this.propagateDown(child, select);
      }
    }
  }
  isSelected(node) {
    return this.findIndexInSelection(node) != -1;
  }
  isSingleSelectionMode() {
    return this.selectionMode && this.selectionMode == "single";
  }
  isMultipleSelectionMode() {
    return this.selectionMode && this.selectionMode == "multiple";
  }
  isCheckboxSelectionMode() {
    return this.selectionMode && this.selectionMode == "checkbox";
  }
  isNodeLeaf(node) {
    return node.leaf == false ? false : !(node.children && node.children.length);
  }
  getRootNode() {
    return this.filteredNodes ? this.filteredNodes : this.value;
  }
  getTemplateForNode(node) {
    if (this._templateMap) return node.type ? this._templateMap[node.type] : this._templateMap["default"];
    else return null;
  }
  onDragOver(event) {
    if (this.droppableNodes && (!this.value || this.value.length === 0)) {
      event.dataTransfer.dropEffect = "move";
      event.preventDefault();
    }
  }
  onDrop(event) {
    if (this.droppableNodes && (!this.value || this.value.length === 0)) {
      event.preventDefault();
      let dragNode = this.dragNode;
      if (this.allowDrop(dragNode, null, this.dragNodeScope)) {
        let dragNodeIndex = this.dragNodeIndex;
        this.value = this.value || [];
        if (this.validateDrop) {
          this.onNodeDrop.emit({
            originalEvent: event,
            dragNode,
            dropNode: null,
            index: dragNodeIndex,
            accept: () => {
              this.processTreeDrop(dragNode, dragNodeIndex);
            }
          });
        } else {
          this.onNodeDrop.emit({
            originalEvent: event,
            dragNode,
            dropNode: null,
            index: dragNodeIndex
          });
          this.processTreeDrop(dragNode, dragNodeIndex);
        }
      }
    }
  }
  processTreeDrop(dragNode, dragNodeIndex) {
    this.dragNodeSubNodes.splice(dragNodeIndex, 1);
    this.value.push(dragNode);
    this.dragDropService.stopDrag({
      node: dragNode
    });
  }
  onDragEnter() {
    if (this.droppableNodes && this.allowDrop(this.dragNode, null, this.dragNodeScope)) {
      this.dragHover = true;
    }
  }
  onDragLeave(event) {
    if (this.droppableNodes) {
      let rect = event.currentTarget.getBoundingClientRect();
      if (event.x > rect.left + rect.width || event.x < rect.left || event.y > rect.top + rect.height || event.y < rect.top) {
        this.dragHover = false;
      }
    }
  }
  allowDrop(dragNode, dropNode, dragNodeScope) {
    if (!dragNode) {
      return false;
    } else if (this.isValidDragScope(dragNodeScope)) {
      let allow = true;
      if (dropNode) {
        if (dragNode === dropNode) {
          allow = false;
        } else {
          let parent = dropNode.parent;
          while (parent != null) {
            if (parent === dragNode) {
              allow = false;
              break;
            }
            parent = parent.parent;
          }
        }
      }
      return allow;
    } else {
      return false;
    }
  }
  isValidDragScope(dragScope) {
    let dropScope = this.droppableScope;
    if (dropScope) {
      if (typeof dropScope === "string") {
        if (typeof dragScope === "string") return dropScope === dragScope;
        else if (Array.isArray(dragScope)) return dragScope.indexOf(dropScope) != -1;
      } else if (Array.isArray(dropScope)) {
        if (typeof dragScope === "string") {
          return dropScope.indexOf(dragScope) != -1;
        } else if (Array.isArray(dragScope)) {
          for (let s of dropScope) {
            for (let ds of dragScope) {
              if (s === ds) {
                return true;
              }
            }
          }
        }
      }
      return false;
    } else {
      return true;
    }
  }
  _filter(value) {
    let filterValue = value;
    if (filterValue === "") {
      this.filteredNodes = null;
    } else {
      this.filteredNodes = [];
      const searchFields = this.filterBy.split(",");
      const filterText = removeAccents(filterValue).toLocaleLowerCase(this.filterLocale);
      const isStrictMode = this.filterMode === "strict";
      for (let node of this.value) {
        let copyNode = __spreadValues({}, node);
        let paramsWithoutNode = {
          searchFields,
          filterText,
          isStrictMode
        };
        if (isStrictMode && (this.findFilteredNodes(copyNode, paramsWithoutNode) || this.isFilterMatched(copyNode, paramsWithoutNode)) || !isStrictMode && (this.isFilterMatched(copyNode, paramsWithoutNode) || this.findFilteredNodes(copyNode, paramsWithoutNode))) {
          this.filteredNodes.push(copyNode);
        }
      }
    }
    this.updateSerializedValue();
    this.onFilter.emit({
      filter: filterValue,
      filteredValue: this.filteredNodes
    });
  }
  /**
   * Resets filter.
   * @group Method
   */
  resetFilter() {
    this.filteredNodes = null;
    if (this.filterViewChild && this.filterViewChild.nativeElement) {
      this.filterViewChild.nativeElement.value = "";
    }
  }
  /**
   * Scrolls to virtual index.
   * @param {number} number - Index to be scrolled.
   * @group Method
   */
  scrollToVirtualIndex(index) {
    this.virtualScroll && this.scroller?.scrollToIndex(index);
  }
  /**
   * Scrolls to virtual index.
   * @param {ScrollToOptions} options - Scroll options.
   * @group Method
   */
  scrollTo(options) {
    if (this.virtualScroll) {
      this.scroller?.scrollTo(options);
    } else if (this.wrapperViewChild && this.wrapperViewChild.nativeElement) {
      if (this.wrapperViewChild.nativeElement.scrollTo) {
        this.wrapperViewChild.nativeElement.scrollTo(options);
      } else {
        this.wrapperViewChild.nativeElement.scrollLeft = options.left;
        this.wrapperViewChild.nativeElement.scrollTop = options.top;
      }
    }
  }
  findFilteredNodes(node, paramsWithoutNode) {
    if (node) {
      let matched = false;
      if (node.children) {
        let childNodes = [...node.children];
        node.children = [];
        for (let childNode of childNodes) {
          let copyChildNode = __spreadValues({}, childNode);
          if (this.isFilterMatched(copyChildNode, paramsWithoutNode)) {
            matched = true;
            node.children.push(copyChildNode);
          }
        }
      }
      if (matched) {
        node.expanded = true;
        return true;
      }
    }
  }
  isFilterMatched(node, params) {
    let {
      searchFields,
      filterText,
      isStrictMode
    } = params;
    let matched = false;
    for (let field of searchFields) {
      let fieldValue = removeAccents(String(resolveFieldData(node, field))).toLocaleLowerCase(this.filterLocale);
      if (fieldValue.indexOf(filterText) > -1) {
        matched = true;
      }
    }
    if (!matched || isStrictMode && !this.isNodeLeaf(node)) {
      matched = this.findFilteredNodes(node, {
        searchFields,
        filterText,
        isStrictMode
      }) || matched;
    }
    return matched;
  }
  getIndex(options, index) {
    const getItemOptions = options["getItemOptions"];
    return getItemOptions ? getItemOptions(index).index : index;
  }
  getBlockableElement() {
    return this.el.nativeElement.children[0];
  }
  ngOnDestroy() {
    if (this.dragStartSubscription) {
      this.dragStartSubscription.unsubscribe();
    }
    if (this.dragStopSubscription) {
      this.dragStopSubscription.unsubscribe();
    }
    super.ngOnDestroy();
  }
  static ɵfac = function Tree_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _Tree)(ɵɵdirectiveInject(TreeDragDropService, 8));
  };
  static ɵcmp = ɵɵdefineComponent({
    type: _Tree,
    selectors: [["p-tree"]],
    contentQueries: function Tree_ContentQueries(rf, ctx, dirIndex) {
      if (rf & 1) {
        ɵɵcontentQuery(dirIndex, _c4, 4);
        ɵɵcontentQuery(dirIndex, _c5, 4);
        ɵɵcontentQuery(dirIndex, _c6, 4);
        ɵɵcontentQuery(dirIndex, _c7, 4);
        ɵɵcontentQuery(dirIndex, _c8, 4);
        ɵɵcontentQuery(dirIndex, _c9, 4);
        ɵɵcontentQuery(dirIndex, _c10, 4);
        ɵɵcontentQuery(dirIndex, _c11, 4);
        ɵɵcontentQuery(dirIndex, _c122, 4);
        ɵɵcontentQuery(dirIndex, _c13, 4);
        ɵɵcontentQuery(dirIndex, PrimeTemplate, 4);
      }
      if (rf & 2) {
        let _t;
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.filterTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.nodeTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.headerTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.footerTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.loaderTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.emptyMessageTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.togglerIconTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.checkboxIconTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.loadingIconTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.filterIconTemplate = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.templates = _t);
      }
    },
    viewQuery: function Tree_Query(rf, ctx) {
      if (rf & 1) {
        ɵɵviewQuery(_c4, 5);
        ɵɵviewQuery(_c14, 5);
        ɵɵviewQuery(_c15, 5);
      }
      if (rf & 2) {
        let _t;
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.filterViewChild = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.scroller = _t.first);
        ɵɵqueryRefresh(_t = ɵɵloadQuery()) && (ctx.wrapperViewChild = _t.first);
      }
    },
    inputs: {
      value: "value",
      selectionMode: "selectionMode",
      loadingMode: "loadingMode",
      selection: "selection",
      style: "style",
      styleClass: "styleClass",
      contextMenu: "contextMenu",
      draggableScope: "draggableScope",
      droppableScope: "droppableScope",
      draggableNodes: [2, "draggableNodes", "draggableNodes", booleanAttribute],
      droppableNodes: [2, "droppableNodes", "droppableNodes", booleanAttribute],
      metaKeySelection: [2, "metaKeySelection", "metaKeySelection", booleanAttribute],
      propagateSelectionUp: [2, "propagateSelectionUp", "propagateSelectionUp", booleanAttribute],
      propagateSelectionDown: [2, "propagateSelectionDown", "propagateSelectionDown", booleanAttribute],
      loading: [2, "loading", "loading", booleanAttribute],
      loadingIcon: "loadingIcon",
      emptyMessage: "emptyMessage",
      ariaLabel: "ariaLabel",
      togglerAriaLabel: "togglerAriaLabel",
      ariaLabelledBy: "ariaLabelledBy",
      validateDrop: [2, "validateDrop", "validateDrop", booleanAttribute],
      filter: [2, "filter", "filter", booleanAttribute],
      filterBy: "filterBy",
      filterMode: "filterMode",
      filterOptions: "filterOptions",
      filterPlaceholder: "filterPlaceholder",
      filteredNodes: "filteredNodes",
      filterLocale: "filterLocale",
      scrollHeight: "scrollHeight",
      lazy: [2, "lazy", "lazy", booleanAttribute],
      virtualScroll: [2, "virtualScroll", "virtualScroll", booleanAttribute],
      virtualScrollItemSize: [2, "virtualScrollItemSize", "virtualScrollItemSize", numberAttribute],
      virtualScrollOptions: "virtualScrollOptions",
      indentation: [2, "indentation", "indentation", numberAttribute],
      _templateMap: "_templateMap",
      trackBy: "trackBy",
      highlightOnSelect: [2, "highlightOnSelect", "highlightOnSelect", booleanAttribute],
      virtualNodeHeight: "virtualNodeHeight"
    },
    outputs: {
      selectionChange: "selectionChange",
      onNodeSelect: "onNodeSelect",
      onNodeUnselect: "onNodeUnselect",
      onNodeExpand: "onNodeExpand",
      onNodeCollapse: "onNodeCollapse",
      onNodeContextMenuSelect: "onNodeContextMenuSelect",
      onNodeDrop: "onNodeDrop",
      onLazyLoad: "onLazyLoad",
      onScroll: "onScroll",
      onScrollIndexChange: "onScrollIndexChange",
      onFilter: "onFilter"
    },
    standalone: true,
    features: [ɵɵProvidersFeature([TreeStyle]), ɵɵInputTransformsFeature, ɵɵInheritDefinitionFeature, ɵɵNgOnChangesFeature, ɵɵStandaloneFeature],
    decls: 8,
    vars: 10,
    consts: [["filter", ""], ["scroller", ""], ["content", ""], ["treeNode", ""], ["loader", ""], ["wrapper", ""], ["emptyFilter", ""], [3, "drop", "dragover", "dragenter", "dragleave", "ngClass", "ngStyle"], ["class", "p-tree-mask p-overlay-mask", 4, "ngIf"], [4, "ngTemplateOutlet"], [4, "ngIf"], ["class", "p-tree-empty-message", 4, "ngIf"], [1, "p-tree-mask", "p-overlay-mask"], [3, "class", 4, "ngIf"], [3, "spin", "styleClass", 4, "ngIf"], ["class", "p-tree-loading-icon", 4, "ngIf"], [3, "spin", "styleClass"], [1, "p-tree-loading-icon"], [4, "ngTemplateOutlet", "ngTemplateOutletContext"], ["pInputText", "", "type", "search", "autocomplete", "off", 1, "p-tree-filter-input", 3, "keydown.enter", "input"], ["class", "p-tree-filter-icon", 4, "ngIf"], [1, "p-tree-filter-icon"], ["styleClass", "p-tree-root", 3, "items", "tabindex", "style", "scrollHeight", "itemSize", "lazy", "options", "onScroll", "onScrollIndexChange", "onLazyLoad", 4, "ngIf"], ["styleClass", "p-tree-root", 3, "onScroll", "onScrollIndexChange", "onLazyLoad", "items", "tabindex", "scrollHeight", "itemSize", "lazy", "options"], ["class", "p-tree-root-children", "role", "tree", 3, "ngClass", "style", 4, "ngIf"], ["role", "tree", 1, "p-tree-root-children", 3, "ngClass"], [3, "level", "rowNode", "node", "parentNode", "firstChild", "lastChild", "index", "itemSize", "indentation", "loadingMode", 4, "ngFor", "ngForOf", "ngForTrackBy"], [3, "level", "rowNode", "node", "parentNode", "firstChild", "lastChild", "index", "itemSize", "indentation", "loadingMode"], [1, "p-tree-root"], ["class", "p-tree-root-children", "role", "tree", 4, "ngIf"], ["role", "tree", 1, "p-tree-root-children"], [3, "node", "firstChild", "lastChild", "index", "level", "loadingMode", 4, "ngFor", "ngForOf", "ngForTrackBy"], [3, "node", "firstChild", "lastChild", "index", "level", "loadingMode"], [1, "p-tree-empty-message"], [4, "ngIf", "ngIfElse"]],
    template: function Tree_Template(rf, ctx) {
      if (rf & 1) {
        ɵɵelementStart(0, "div", 7);
        ɵɵlistener("drop", function Tree_Template_div_drop_0_listener($event) {
          return ctx.onDrop($event);
        })("dragover", function Tree_Template_div_dragover_0_listener($event) {
          return ctx.onDragOver($event);
        })("dragenter", function Tree_Template_div_dragenter_0_listener() {
          return ctx.onDragEnter();
        })("dragleave", function Tree_Template_div_dragleave_0_listener($event) {
          return ctx.onDragLeave($event);
        });
        ɵɵtemplate(1, Tree_div_1_Template, 3, 2, "div", 8)(2, Tree_ng_container_2_Template, 1, 0, "ng-container", 9)(3, Tree_Conditional_3_Template, 1, 4, "ng-container")(4, Tree_Conditional_4_Template, 1, 1, "p-iconField")(5, Tree_ng_container_5_Template, 3, 2, "ng-container", 10)(6, Tree_div_6_Template, 3, 3, "div", 11)(7, Tree_ng_container_7_Template, 1, 0, "ng-container", 9);
        ɵɵelementEnd();
      }
      if (rf & 2) {
        let tmp_6_0;
        ɵɵclassMap(ctx.styleClass);
        ɵɵproperty("ngClass", ctx.containerClass)("ngStyle", ctx.style);
        ɵɵadvance();
        ɵɵproperty("ngIf", ctx.loading && ctx.loadingMode === "mask");
        ɵɵadvance();
        ɵɵproperty("ngTemplateOutlet", ctx.headerTemplate || ctx._headerTemplate);
        ɵɵadvance();
        ɵɵconditional(ctx.filterTemplate || ctx._filterTemplate ? 3 : 4);
        ɵɵadvance(2);
        ɵɵproperty("ngIf", (tmp_6_0 = ctx.getRootNode()) == null ? null : tmp_6_0.length);
        ɵɵadvance();
        ɵɵproperty("ngIf", !ctx.loading && (ctx.getRootNode() == null || ctx.getRootNode().length === 0));
        ɵɵadvance();
        ɵɵproperty("ngTemplateOutlet", ctx.footerTemplate || ctx._footerTemplate);
      }
    },
    dependencies: [CommonModule, NgClass, NgForOf, NgIf, NgTemplateOutlet, NgStyle, Scroller, SharedModule, SearchIcon, SpinnerIcon, InputText, FormsModule, IconField, InputIcon, UITreeNode],
    encapsulation: 2
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(Tree, [{
    type: Component,
    args: [{
      selector: "p-tree",
      standalone: true,
      imports: [CommonModule, Scroller, SharedModule, SearchIcon, SpinnerIcon, InputText, FormsModule, IconField, InputIcon, UITreeNode],
      template: `
        <div [ngClass]="containerClass" [ngStyle]="style" [class]="styleClass" (drop)="onDrop($event)" (dragover)="onDragOver($event)" (dragenter)="onDragEnter()" (dragleave)="onDragLeave($event)">
            <div class="p-tree-mask p-overlay-mask" *ngIf="loading && loadingMode === 'mask'">
                <i *ngIf="loadingIcon" [class]="'p-tree-loading-icon pi-spin ' + loadingIcon"></i>
                <ng-container *ngIf="!loadingIcon">
                    <SpinnerIcon *ngIf="!loadingIconTemplate && !_loadingIconTemplate" [spin]="true" [styleClass]="'p-tree-loading-icon'" />
                    <span *ngIf="loadingIconTemplate || _loadingIconTemplate" class="p-tree-loading-icon">
                        <ng-template *ngTemplateOutlet="loadingIconTemplate || _loadingIconTemplate"></ng-template>
                    </span>
                </ng-container>
            </div>
            <ng-container *ngTemplateOutlet="headerTemplate || _headerTemplate"></ng-container>
            @if (filterTemplate || _filterTemplate) {
                <ng-container *ngTemplateOutlet="filterTemplate || _filterTemplate; context: { $implicit: filterOptions }"></ng-container>
            } @else {
                <p-iconField *ngIf="filter">
                    <input #filter pInputText type="search" autocomplete="off" class="p-tree-filter-input" [attr.placeholder]="filterPlaceholder" (keydown.enter)="$event.preventDefault()" (input)="_filter($event.target.value)" />
                    <p-inputIcon>
                        <SearchIcon *ngIf="!filterIconTemplate && !_filterIconTemplate" class="p-tree-filter-icon" />
                        <span *ngIf="filterIconTemplate || _filterIconTemplate">
                            <ng-template *ngTemplateOutlet="filterIconTemplate || _filterIconTemplate"></ng-template>
                        </span>
                    </p-inputIcon>
                </p-iconField>
            }

            <ng-container *ngIf="getRootNode()?.length">
                <p-scroller
                    #scroller
                    *ngIf="virtualScroll"
                    [items]="serializedValue"
                    [tabindex]="-1"
                    styleClass="p-tree-root"
                    [style]="{ height: scrollHeight !== 'flex' ? scrollHeight : undefined }"
                    [scrollHeight]="scrollHeight !== 'flex' ? undefined : '100%'"
                    [itemSize]="virtualScrollItemSize || _virtualNodeHeight"
                    [lazy]="lazy"
                    (onScroll)="onScroll.emit($event)"
                    (onScrollIndexChange)="onScrollIndexChange.emit($event)"
                    (onLazyLoad)="onLazyLoad.emit($event)"
                    [options]="virtualScrollOptions"
                >
                    <ng-template #content let-items let-scrollerOptions="options">
                        <ul *ngIf="items" class="p-tree-root-children" [ngClass]="scrollerOptions.contentStyleClass" [style]="scrollerOptions.contentStyle" role="tree" [attr.aria-label]="ariaLabel" [attr.aria-labelledby]="ariaLabelledBy">
                            <p-treeNode
                                #treeNode
                                *ngFor="let rowNode of items; let firstChild = first; let lastChild = last; let index = index; trackBy: trackBy"
                                [level]="rowNode.level"
                                [rowNode]="rowNode"
                                [node]="rowNode.node"
                                [parentNode]="rowNode.parent"
                                [firstChild]="firstChild"
                                [lastChild]="lastChild"
                                [index]="getIndex(scrollerOptions, index)"
                                [itemSize]="scrollerOptions.itemSize"
                                [indentation]="indentation"
                                [loadingMode]="loadingMode"
                            ></p-treeNode>
                        </ul>
                    </ng-template>
                    <ng-container *ngIf="loaderTemplate || _loaderTemplate">
                        <ng-template #loader let-scrollerOptions="options">
                            <ng-container *ngTemplateOutlet="loaderTemplate || _loaderTemplate; context: { options: scrollerOptions }"></ng-container>
                        </ng-template>
                    </ng-container>
                </p-scroller>
                <ng-container *ngIf="!virtualScroll">
                    <div #wrapper class="p-tree-root" [style.max-height]="scrollHeight">
                        <ul class="p-tree-root-children" *ngIf="getRootNode()" role="tree" [attr.aria-label]="ariaLabel" [attr.aria-labelledby]="ariaLabelledBy">
                            <p-treeNode
                                *ngFor="let node of getRootNode(); let firstChild = first; let lastChild = last; let index = index; trackBy: trackBy.bind(this)"
                                [node]="node"
                                [firstChild]="firstChild"
                                [lastChild]="lastChild"
                                [index]="index"
                                [level]="0"
                                [loadingMode]="loadingMode"
                            ></p-treeNode>
                        </ul>
                    </div>
                </ng-container>
            </ng-container>

            <div class="p-tree-empty-message" *ngIf="!loading && (getRootNode() == null || getRootNode().length === 0)">
                <ng-container *ngIf="!emptyMessageTemplate && !_emptyMessageTemplate; else emptyFilter">
                    {{ emptyMessageLabel }}
                </ng-container>
                <ng-template #emptyFilter *ngTemplateOutlet="emptyMessageTemplate || _emptyMessageTemplate"></ng-template>
            </div>
            <ng-container *ngTemplateOutlet="footerTemplate || _footerTemplate"></ng-container>
        </div>
    `,
      changeDetection: ChangeDetectionStrategy.Default,
      encapsulation: ViewEncapsulation$1.None,
      providers: [TreeStyle]
    }]
  }], () => [{
    type: TreeDragDropService,
    decorators: [{
      type: Optional
    }]
  }], {
    value: [{
      type: Input
    }],
    selectionMode: [{
      type: Input
    }],
    loadingMode: [{
      type: Input
    }],
    selection: [{
      type: Input
    }],
    style: [{
      type: Input
    }],
    styleClass: [{
      type: Input
    }],
    contextMenu: [{
      type: Input
    }],
    draggableScope: [{
      type: Input
    }],
    droppableScope: [{
      type: Input
    }],
    draggableNodes: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    droppableNodes: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    metaKeySelection: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    propagateSelectionUp: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    propagateSelectionDown: [{
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
    emptyMessage: [{
      type: Input
    }],
    ariaLabel: [{
      type: Input
    }],
    togglerAriaLabel: [{
      type: Input
    }],
    ariaLabelledBy: [{
      type: Input
    }],
    validateDrop: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    filter: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    filterBy: [{
      type: Input
    }],
    filterMode: [{
      type: Input
    }],
    filterOptions: [{
      type: Input
    }],
    filterPlaceholder: [{
      type: Input
    }],
    filteredNodes: [{
      type: Input
    }],
    filterLocale: [{
      type: Input
    }],
    scrollHeight: [{
      type: Input
    }],
    lazy: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    virtualScroll: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    virtualScrollItemSize: [{
      type: Input,
      args: [{
        transform: numberAttribute
      }]
    }],
    virtualScrollOptions: [{
      type: Input
    }],
    indentation: [{
      type: Input,
      args: [{
        transform: numberAttribute
      }]
    }],
    _templateMap: [{
      type: Input
    }],
    trackBy: [{
      type: Input
    }],
    highlightOnSelect: [{
      type: Input,
      args: [{
        transform: booleanAttribute
      }]
    }],
    virtualNodeHeight: [{
      type: Input
    }],
    selectionChange: [{
      type: Output
    }],
    onNodeSelect: [{
      type: Output
    }],
    onNodeUnselect: [{
      type: Output
    }],
    onNodeExpand: [{
      type: Output
    }],
    onNodeCollapse: [{
      type: Output
    }],
    onNodeContextMenuSelect: [{
      type: Output
    }],
    onNodeDrop: [{
      type: Output
    }],
    onLazyLoad: [{
      type: Output
    }],
    onScroll: [{
      type: Output
    }],
    onScrollIndexChange: [{
      type: Output
    }],
    onFilter: [{
      type: Output
    }],
    filterTemplate: [{
      type: ContentChild,
      args: ["filter", {
        descendants: false
      }]
    }],
    nodeTemplate: [{
      type: ContentChild,
      args: ["node", {
        descendants: false
      }]
    }],
    headerTemplate: [{
      type: ContentChild,
      args: ["header", {
        descendants: false
      }]
    }],
    footerTemplate: [{
      type: ContentChild,
      args: ["footer", {
        descendants: false
      }]
    }],
    loaderTemplate: [{
      type: ContentChild,
      args: ["loader", {
        descendants: false
      }]
    }],
    emptyMessageTemplate: [{
      type: ContentChild,
      args: ["empty", {
        descendants: false
      }]
    }],
    togglerIconTemplate: [{
      type: ContentChild,
      args: ["togglericon", {
        descendants: false
      }]
    }],
    checkboxIconTemplate: [{
      type: ContentChild,
      args: ["checkboxicon", {
        descendants: false
      }]
    }],
    loadingIconTemplate: [{
      type: ContentChild,
      args: ["loadingicon", {
        descendants: false
      }]
    }],
    filterIconTemplate: [{
      type: ContentChild,
      args: ["filtericon", {
        descendants: false
      }]
    }],
    filterViewChild: [{
      type: ViewChild,
      args: ["filter"]
    }],
    scroller: [{
      type: ViewChild,
      args: ["scroller"]
    }],
    wrapperViewChild: [{
      type: ViewChild,
      args: ["wrapper"]
    }],
    templates: [{
      type: ContentChildren,
      args: [PrimeTemplate]
    }]
  });
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && ɵsetClassDebugInfo(Tree, {
    className: "Tree"
  });
})();
var TreeModule = class _TreeModule {
  static ɵfac = function TreeModule_Factory(__ngFactoryType__) {
    return new (__ngFactoryType__ || _TreeModule)();
  };
  static ɵmod = ɵɵdefineNgModule({
    type: _TreeModule
  });
  static ɵinj = ɵɵdefineInjector({
    imports: [Tree, SharedModule, SharedModule]
  });
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(TreeModule, [{
    type: NgModule,
    args: [{
      imports: [Tree, SharedModule],
      exports: [Tree, SharedModule]
    }]
  }], null, null);
})();
export {
  Tree,
  TreeClasses,
  TreeModule,
  TreeStyle,
  UITreeNode
};
//# sourceMappingURL=primeng_tree.js.map
