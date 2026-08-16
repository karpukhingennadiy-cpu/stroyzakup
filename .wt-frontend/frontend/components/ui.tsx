import { forwardRef, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode } from "react";

/**
 * UI-примитивы по дизайн-системе Kimi (components-web/button.md, form.md).
 * Централизованные метрики: высота, радиус, типографика, иконки, отступы.
 */

type ButtonVariant = "primary" | "secondary" | "outline";
type ButtonSize = 26 | 32 | 44;

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  danger?: boolean;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

// Метрики из спецификации Button: size → height/radius/text/icon
const sizeStyles: Record<ButtonSize, string> = {
  44: "h-11 min-w-[72px] px-[14px] rounded-[var(--radius-lg)] text-base font-medium gap-1.5 [&_svg]:w-5 [&_svg]:h-5",
  32: "h-8 min-w-[62px] px-2.5 rounded-[var(--radius-md)] text-sm font-medium gap-1 [&_svg]:w-[18px] [&_svg]:h-[18px]",
  26: "h-[26px] min-w-[52px] px-2 rounded-[var(--radius-sm)] text-xs font-medium gap-1 [&_svg]:w-4 [&_svg]:h-4",
};

function variantStyles(variant: ButtonVariant, danger: boolean): string {
  if (danger) {
    if (variant === "primary")
      return "bg-[var(--danger)] text-white hover:brightness-110 active:brightness-95";
    // secondary/outline danger — поверхность нейтральная, текст danger
    return variant === "outline"
      ? "border border-[var(--separator)] bg-transparent text-[var(--danger)] hover:bg-[var(--fill-1)]"
      : "bg-[var(--fill-1)] text-[var(--danger)] hover:bg-[var(--fill-2)]";
  }
  switch (variant) {
    case "primary":
      // color.labels.primary fill + инверсный текст (brand.kimiDark)
      return "bg-[var(--label-primary)] text-[var(--bg-primary)] hover:opacity-85 active:opacity-90";
    case "outline":
      return "border border-[var(--separator)] bg-transparent text-[var(--label-primary)] hover:bg-[var(--fill-1)]";
    default:
      return "bg-[var(--fill-1)] text-[var(--label-primary)] hover:bg-[var(--fill-2)]";
  }
}

function Spinner() {
  return (
    <span
      aria-hidden="true"
      className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin shrink-0"
    />
  );
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", size = 32, danger = false, loading = false, leftIcon, rightIcon, disabled, className = "", children, type, ...rest },
  ref
) {
  const inactive = disabled || loading;
  return (
    <button
      ref={ref}
      type={type || "button"}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={[
        "inline-flex items-center justify-center shrink-0 select-none",
        "transition-[background-color,color,opacity,transform] duration-150 ease-kimi-out",
        "active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-[var(--accent)] focus-visible:outline-offset-2",
        sizeStyles[size],
        variantStyles(variant, danger),
        inactive ? "opacity-50 pointer-events-none" : "",
        className,
      ].join(" ")}
      {...rest}
    >
      {loading ? <Spinner /> : leftIcon}
      {children && <span className="truncate">{children}</span>}
      {!loading && rightIcon}
    </button>
  );
});

/** Кнопка-ссылка для навигации (a11y: <a> для навигации, <button> для действий). */
export function buttonClass(opts?: { variant?: ButtonVariant; size?: ButtonSize; danger?: boolean; className?: string }): string {
  const { variant = "secondary", size = 32, danger = false, className = "" } = opts || {};
  return [
    "inline-flex items-center justify-center shrink-0 select-none no-underline",
    "transition-[background-color,color,opacity,transform] duration-150 ease-kimi-out",
    "active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-[var(--accent)] focus-visible:outline-offset-2",
    sizeStyles[size],
    variantStyles(variant, danger),
    className,
  ].join(" ");
}

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  id: string;
  hint?: string;
}

/** Поле формы: label связан с input через htmlFor/id (a11y). */
export function Field({ label, id, hint, className = "", ...rest }: FieldProps) {
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-label-1 mb-1.5">
          {label}
        </label>
      )}
      <input id={id} className="field-input" {...rest} />
      {hint && <p className="mt-1 text-xs text-label-3">{hint}</p>}
    </div>
  );
}

interface CardProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  padding?: boolean;
}

/** Карточка: container для сгруппированного контента (card.md). */
export function Card({ title, subtitle, icon, children, className = "", padding = true }: CardProps) {
  return (
    <section className={"surface-card overflow-hidden " + className}>
      {(title || icon) && (
        <header className="px-6 py-4 border-b border-separator bg-[var(--fill-1)]">
          <div className="flex items-center gap-3">
            {icon && (
              <div className="w-10 h-10 rounded-[var(--radius-md)] bg-[var(--fill-2)] flex items-center justify-center text-label-2 shrink-0">
                {icon}
              </div>
            )}
            <div className="min-w-0">
              <h2 className="font-medium text-label-1 text-base truncate">{title}</h2>
              {subtitle && <p className="text-xs text-label-3 mt-0.5">{subtitle}</p>}
            </div>
          </div>
        </header>
      )}
      <div className={padding ? "p-6" : ""}>{children}</div>
    </section>
  );
}

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "accent";

const badgeTones: Record<BadgeTone, string> = {
  neutral: "bg-[var(--fill-2)] text-[var(--label-secondary)]",
  success: "bg-[var(--success-soft)] text-[var(--success)]",
  warning: "bg-[var(--warning-soft)] text-[var(--warning)]",
  danger: "bg-[var(--danger-soft)] text-[var(--danger)]",
  accent: "bg-[var(--accent-soft)] text-[var(--accent)]",
};

/** Тег/бейдж: typography.webUI.c1Emphasized, radius.xxs (мелкий элемент). */
export function Badge({ tone = "neutral", children, className = "" }: { tone?: BadgeTone; children: ReactNode; className?: string }) {
  return (
    <span className={"inline-flex items-center px-1.5 py-0.5 rounded-[var(--radius-xs)] text-xs font-medium " + badgeTones[tone] + " " + className}>
      {children}
    </span>
  );
}
