#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Минитендер.рф — Modern Redesign v3.0 + CI Fix
# Запуск: bash apply-redesign.sh
# ============================================================

echo "🎨 Минитендер.рф — Применяем редизайн v3.0 + фикс CI..."
echo ""

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "❌ Запустите скрипт из корня репозитория stroyzakup"
  exit 1
fi

BRANCH="feat/modern-redesign-v3"
git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
echo "✅ Ветка: $BRANCH"

# ============================================================
# 1/8 backend/config/settings/test.py
# ============================================================
echo "📝 [1/8] backend/config/settings/test.py"
cat > backend/config/settings/test.py << 'TESTPY'
"""Test settings for CI/CD."""
import os
os.environ["CELERY_BROKER_URL"] = "memory://"

from .base import *

# FIX-CI: remove django.contrib.gis — no GDAL in CI
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django.contrib.gis"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [],
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
TESTPY

# ============================================================
# 2/8 .github/workflows/backend.yml
# ============================================================
echo "📝 [2/8] .github/workflows/backend.yml"
mkdir -p .github/workflows
cat > .github/workflows/backend.yml << 'BACKENDYML'
name: Backend CI

on:
  push:
    branches: [dev, main]
    paths:
      - 'backend/**'
      - '.github/workflows/backend.yml'
  pull_request:
    branches: [dev, main]
    paths:
      - 'backend/**'
      - '.github/workflows/backend.yml'

jobs:
  test:
    runs-on: ubuntu-latest

    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
      SECRET_KEY: django-insecure-test-key

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install dependencies (including dev extras)
        run: |
          cd backend
          uv sync --extra dev

      - name: Run migrations
        run: |
          cd backend
          uv run python manage.py migrate

      - name: Run tests
        run: |
          cd backend
          uv run pytest tests/ -v --tb=short

      - name: Lint with ruff
        run: |
          cd backend
          uv run ruff check .

      - name: Format check with black
        run: |
          cd backend
          uv run black --check .
BACKENDYML

# ============================================================
# 3/8 frontend/app/globals.css
# ============================================================
echo "📝 [3/8] frontend/app/globals.css"
cat > frontend/app/globals.css << 'GLOBALSCSS'
/*
 * Минитендер.рф — Modern Design System v3.0
 * Style: Modern B2B SaaS (Linear/Vercel aesthetic)
 */

@layer base {
  :root {
    --bg-primary: #fafafa;
    --bg-secondary: #f4f4f5;
    --bg-tertiary: #ffffff;
    --bg-ground: #f8f9fb;
    --label-primary: rgba(9, 9, 11, 0.92);
    --label-secondary: rgba(9, 9, 11, 0.6);
    --label-tertiary: rgba(9, 9, 11, 0.4);
    --label-quaternary: rgba(9, 9, 11, 0.25);
    --fill-1: rgba(9, 9, 11, 0.03);
    --fill-2: rgba(9, 9, 11, 0.06);
    --fill-3: rgba(9, 9, 11, 0.1);
    --separator: rgba(9, 9, 11, 0.08);
    --accent: #6366f1;
    --accent-hover: #4f46e5;
    --accent-soft: rgba(99, 102, 241, 0.08);
    --gradient-accent: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    --gradient-accent-hover: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #8b5cf6 100%);
    --gradient-text: linear-gradient(135deg, #6366f1, #a78bfa);
    --danger: #ef4444;
    --danger-soft: rgba(239, 68, 68, 0.08);
    --success: #22c55e;
    --success-soft: rgba(34, 197, 94, 0.08);
    --warning: #f59e0b;
    --warning-soft: rgba(245, 158, 11, 0.08);
    --brand: #6366f1;
    --brand-hover: #4f46e5;
    --brand-ink: #ffffff;
    --sidebar-bg: #09090b;
    --glass-bg: rgba(255, 255, 255, 0.72);
    --glass-border: rgba(255, 255, 255, 0.3);
    --glass-blur: 16px;
    --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);
    --shadow-small: 0 2px 8px -2px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
    --shadow-medium: 0 8px 24px -8px rgba(0, 0, 0, 0.1), 0 2px 8px rgba(0, 0, 0, 0.04);
    --shadow-large: 0 16px 48px -12px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.04);
    --shadow-glow: 0 0 24px rgba(99, 102, 241, 0.15);
    --shadow-input: 0 1px 3px rgba(0, 0, 0, 0.06);
    --radius-xs: 6px;
    --radius-sm: 10px;
    --radius-md: 14px;
    --radius-lg: 18px;
    --radius-xl: 24px;
    --radius-full: 9999px;
    --z-header: 500;
    --z-modal-backdrop: 800;
    --z-modal: 810;
    --z-tooltip: 900;
    --z-toast: 1000;
    --background: var(--bg-primary);
    --foreground: var(--label-primary);
    --card: var(--bg-tertiary);
    --card-foreground: var(--label-primary);
    --popover: var(--bg-tertiary);
    --popover-foreground: var(--label-primary);
    --primary: var(--accent);
    --primary-foreground: #ffffff;
    --secondary: var(--fill-1);
    --secondary-foreground: var(--label-primary);
    --muted: var(--fill-1);
    --muted-foreground: var(--label-secondary);
    --accent-s: var(--accent-soft);
    --accent-foreground: var(--label-primary);
    --destructive: var(--danger);
    --border: var(--separator);
    --input: var(--separator);
    --ring: var(--accent);
    --radius: 0.75rem;
  }

  html.dark {
    --bg-primary: #09090b;
    --bg-secondary: #18181b;
    --bg-tertiary: #1c1c20;
    --bg-ground: #0c0c0e;
    --label-primary: rgba(255, 255, 255, 0.92);
    --label-secondary: rgba(255, 255, 255, 0.6);
    --label-tertiary: rgba(255, 255, 255, 0.4);
    --label-quaternary: rgba(255, 255, 255, 0.2);
    --fill-1: rgba(255, 255, 255, 0.04);
    --fill-2: rgba(255, 255, 255, 0.08);
    --fill-3: rgba(255, 255, 255, 0.14);
    --separator: rgba(255, 255, 255, 0.08);
    --accent: #818cf8;
    --accent-hover: #6366f1;
    --accent-soft: rgba(129, 140, 248, 0.1);
    --gradient-accent: linear-gradient(135deg, #818cf8 0%, #a78bfa 50%, #c4b5fd 100%);
    --gradient-accent-hover: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    --gradient-text: linear-gradient(135deg, #818cf8, #c4b5fd);
    --danger: #f87171;
    --danger-soft: rgba(248, 113, 113, 0.1);
    --success: #4ade80;
    --success-soft: rgba(74, 222, 128, 0.1);
    --warning: #fbbf24;
    --warning-soft: rgba(251, 191, 36, 0.1);
    --brand: #818cf8;
    --brand-hover: #6366f1;
    --brand-ink: #ffffff;
    --sidebar-bg: #09090b;
    --glass-bg: rgba(9, 9, 11, 0.72);
    --glass-border: rgba(255, 255, 255, 0.06);
    --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.2);
    --shadow-small: 0 2px 8px -2px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2);
    --shadow-medium: 0 8px 24px -8px rgba(0, 0, 0, 0.4), 0 2px 8px rgba(0, 0, 0, 0.2);
    --shadow-large: 0 16px 48px -12px rgba(0, 0, 0, 0.5), 0 4px 16px rgba(0, 0, 0, 0.2);
    --shadow-glow: 0 0 24px rgba(129, 140, 248, 0.15);
    --shadow-input: 0 1px 3px rgba(0, 0, 0, 0.3);
    --background: var(--bg-primary);
    --foreground: var(--label-primary);
    --card: var(--bg-tertiary);
    --card-foreground: var(--label-primary);
    --popover: var(--bg-tertiary);
    --popover-foreground: var(--label-primary);
    --primary: var(--accent);
    --primary-foreground: #ffffff;
    --secondary: var(--fill-1);
    --secondary-foreground: var(--label-primary);
    --muted: var(--fill-1);
    --muted-foreground: var(--label-secondary);
    --accent-s: var(--accent-soft);
    --accent-foreground: var(--label-primary);
    --destructive: var(--danger);
    --border: var(--separator);
    --input: var(--separator);
    --ring: var(--accent);
  }
}

@theme inline {
  --font-heading: var(--font-sans);
  --font-sans: var(--font-inter), system-ui, sans-serif;
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent-s);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --radius-sm: calc(var(--radius) * 0.6);
  --radius-md: calc(var(--radius) * 0.8);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) * 1.4);
  --radius-2xl: calc(var(--radius) * 1.8);
  --radius-3xl: calc(var(--radius) * 2.2);
}

@layer utilities {
  .glass {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
  }
  .gradient-text {
    background: var(--gradient-text);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .gradient-bg { background: var(--gradient-accent); }
  .shadow-glow { box-shadow: var(--shadow-glow); }
  .mesh-gradient {
    background:
      radial-gradient(at 20% 20%, rgba(99, 102, 241, 0.12) 0%, transparent 50%),
      radial-gradient(at 80% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
      radial-gradient(at 50% 50%, rgba(167, 139, 250, 0.05) 0%, transparent 60%);
  }
  html.dark .mesh-gradient {
    background:
      radial-gradient(at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
      radial-gradient(at 80% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
      radial-gradient(at 50% 50%, rgba(167, 139, 250, 0.06) 0%, transparent 60%);
  }
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  .btn-shimmer::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    animation: shimmer 3s infinite;
  }
  @keyframes reveal-up {
    from { opacity: 0; transform: translateY(24px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .animate-reveal {
    animation: reveal-up 0.6s cubic-bezier(0.23, 1, 0.32, 1) both;
  }
  .delay-100 { animation-delay: 100ms; }
  .delay-200 { animation-delay: 200ms; }
  .delay-300 { animation-delay: 300ms; }
  .delay-400 { animation-delay: 400ms; }
  .card-hover {
    transition: transform 0.25s cubic-bezier(0.23, 1, 0.32, 1),
                box-shadow 0.25s cubic-bezier(0.23, 1, 0.32, 1);
  }
  .card-hover:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-medium);
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
GLOBALSCSS

# ============================================================
# 4/8 frontend/tailwind.config.ts
# ============================================================
echo "📝 [4/8] frontend/tailwind.config.ts"
cat > frontend/tailwind.config.ts << 'TAILWINDTS'
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        surface: {
          primary: "var(--bg-primary)",
          secondary: "var(--bg-secondary)",
          tertiary: "var(--bg-tertiary)",
          ground: "var(--bg-ground)",
        },
        label: {
          primary: "var(--label-primary)",
          secondary: "var(--label-secondary)",
          tertiary: "var(--label-tertiary)",
          quaternary: "var(--label-quaternary)",
        },
        separator: "var(--separator)",
        fill: {
          1: "var(--fill-1)",
          2: "var(--fill-2)",
          3: "var(--fill-3)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          hover: "var(--accent-hover)",
          soft: "var(--accent-soft)",
        },
        danger: { DEFAULT: "var(--danger)", soft: "var(--danger-soft)" },
        success: { DEFAULT: "var(--success)", soft: "var(--success-soft)" },
        warning: { DEFAULT: "var(--warning)", soft: "var(--warning-soft)" },
        brand: {
          DEFAULT: "var(--brand)",
          hover: "var(--brand-hover)",
          ink: "var(--brand-ink)",
          sidebar: "var(--sidebar-bg)",
        },
      },
      borderRadius: {
        xs: "var(--radius-xs)",
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        xs: "var(--shadow-xs)",
        small: "var(--shadow-small)",
        medium: "var(--shadow-medium)",
        large: "var(--shadow-large)",
        glow: "var(--shadow-glow)",
        input: "var(--shadow-input)",
      },
      zIndex: {
        header: "var(--z-header)",
        "modal-backdrop": "var(--z-modal-backdrop)",
        modal: "var(--z-modal)",
        tooltip: "var(--z-tooltip)",
        toast: "var(--z-toast)",
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.23, 1, 0.32, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
TAILWINDTS

# ============================================================
# 5/8 frontend/app/sections/landing-header.tsx
# ============================================================
echo "📝 [5/8] frontend/app/sections/landing-header.tsx"
mkdir -p frontend/app/sections
cat > frontend/app/sections/landing-header.tsx << 'HEADER'
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Hammer, Menu, X } from "lucide-react";
import { ThemeToggle } from "@/components/theme";
import { useState } from "react";

export function LandingHeader() {
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="fixed top-4 left-0 right-0 z-header px-4">
      <div className="mx-auto max-w-5xl glass rounded-[var(--radius-full)] px-5 py-3 shadow-small">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] gradient-bg text-white transition-transform duration-300 group-hover:scale-105">
              <Hammer className="h-4 w-4" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-[var(--label-primary)]">
              Минитендер
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-1" aria-label="Разделы">
            {[
              { href: "#how", label: "Как работает" },
              { href: "#features", label: "Возможности" },
              { href: "#pricing", label: "Тарифы" },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="px-3 py-1.5 text-sm font-medium text-[var(--label-secondary)] rounded-[var(--radius-full)] hover:text-[var(--label-primary)] hover:bg-[var(--fill-1)] transition-all duration-200"
              >
                {item.label}
              </a>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={() => router.push("/lk")}
              className="px-3 py-1.5 text-sm font-medium text-[var(--label-secondary)] hover:text-[var(--label-primary)] transition-colors"
            >
              Войти
            </button>
            <button
              onClick={() => router.push("/lk/requests/new")}
              className="relative overflow-hidden rounded-[var(--radius-full)] gradient-bg px-4 py-1.5 text-sm font-semibold text-white shadow-small hover:shadow-glow active:scale-[0.97] transition-all duration-200 btn-shimmer"
            >
              Начать бесплатно
            </button>
          </div>

          <button
            className="md:hidden p-2 text-[var(--label-secondary)]"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Меню"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden mt-2 glass rounded-[var(--radius-lg)] p-4 shadow-medium animate-reveal">
          <nav className="flex flex-col gap-1">
            {[
              { href: "#how", label: "Как работает" },
              { href: "#features", label: "Возможности" },
              { href: "#pricing", label: "Тарифы" },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2 text-sm font-medium text-[var(--label-secondary)] rounded-[var(--radius-sm)] hover:bg-[var(--fill-1)] hover:text-[var(--label-primary)] transition-colors"
              >
                {item.label}
              </a>
            ))}
            <div className="mt-2 pt-2 border-t border-[var(--separator)] flex flex-col gap-2">
              <button
                onClick={() => router.push("/lk")}
                className="w-full px-3 py-2 text-sm font-medium text-[var(--label-secondary)] hover:text-[var(--label-primary)] transition-colors text-left rounded-[var(--radius-sm)]"
              >
                Войти
              </button>
              <button
                onClick={() => router.push("/lk/requests/new")}
                className="w-full rounded-[var(--radius-sm)] gradient-bg px-3 py-2 text-sm font-semibold text-white text-center"
              >
                Начать бесплатно
              </button>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
HEADER

# ============================================================
# 6/8 frontend/app/sections/landing-hero.tsx
# ============================================================
echo "📝 [6/8] frontend/app/sections/landing-hero.tsx"
cat > frontend/app/sections/landing-hero.tsx << 'HERO'
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, ArrowRight, Sparkles } from "lucide-react";

export function LandingHero() {
  const router = useRouter();
  const [text, setText] = useState("");

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-24 pb-16">
      <div className="absolute inset-0 mesh-gradient" aria-hidden="true" />
      <div
        className="absolute inset-0 opacity-[0.03]"
        aria-hidden="true"
        style={{
          backgroundImage: `radial-gradient(var(--label-primary) 1px, transparent 1px)`,
          backgroundSize: "32px 32px",
        }}
      />

      <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
        <div className="mb-8 inline-flex items-center gap-2 rounded-[var(--radius-full)] border border-[var(--accent)]/20 bg-[var(--accent-soft)] px-4 py-1.5 text-sm font-medium text-[var(--accent)] animate-reveal">
          <Sparkles className="h-3.5 w-3.5" />
          AI-powered procurement platform
        </div>

        <h1 className="text-balance text-5xl font-extrabold tracking-tight text-[var(--label-primary)] sm:text-7xl leading-[1.05] animate-reveal delay-100">
          Строительные закупки{" "}
          <span className="gradient-text">без посредников</span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl leading-relaxed text-[var(--label-secondary)] max-w-2xl mx-auto animate-reveal delay-200">
          Отправьте список материалов — за 24 часа получите конкурентный лист
          с лучшими ценами от проверенных поставщиков в вашем регионе.
        </p>

        <div className="mt-10 mx-auto max-w-xl animate-reveal delay-300">
          <div className="relative group">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={`Керамогранит серый 600×600 — 150 м²\nБетон М300 — 12 м³\nДоска обрезная сосна 25×150 — 3 м³`}
              className="w-full h-36 resize-none rounded-[var(--radius-lg)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-5 py-4 text-sm text-[var(--label-primary)] placeholder:text-[var(--label-quaternary)] shadow-small focus:shadow-medium focus:border-[var(--accent)]/30 focus:ring-2 focus:ring-[var(--accent)]/10 outline-none transition-all duration-300"
            />
            <div className="absolute bottom-3 right-4 text-xs text-[var(--label-quaternary)] tabular-nums">
              {text.length} симв.
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4 animate-reveal delay-400">
          <button
            onClick={() => router.push("/lk/requests/new")}
            className="relative overflow-hidden inline-flex items-center gap-2 rounded-[var(--radius-full)] gradient-bg px-8 py-3.5 text-base font-semibold text-white shadow-medium hover:shadow-glow active:scale-[0.97] transition-all duration-200 btn-shimmer"
          >
            <Zap className="h-5 w-5" />
            Разослать заявку
          </button>
          <button
            onClick={() => document.getElementById("how")?.scrollIntoView({ behavior: "smooth" })}
            className="inline-flex items-center gap-2 rounded-[var(--radius-full)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-8 py-3.5 text-base font-semibold text-[var(--label-primary)] shadow-xs hover:shadow-small hover:border-[var(--accent)]/20 active:scale-[0.97] transition-all duration-200"
          >
            Как это работает
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <p className="mt-6 text-xs text-[var(--label-quaternary)] animate-reveal delay-400">
          Первые 50 заявок бесплатно · Не нужна регистрация для демо · Данные обрабатывает AI
        </p>
      </div>
    </section>
  );
}
HERO

# ============================================================
# 7/8 frontend/app/sections/landing-cta.tsx
# ============================================================
echo "📝 [7/8] frontend/app/sections/landing-cta.tsx"
cat > frontend/app/sections/landing-cta.tsx << 'CTA'
"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Mail } from "lucide-react";

export function LandingCTA() {
  const router = useRouter();

  return (
    <section className="relative overflow-hidden py-24 sm:py-32">
      <div
        className="absolute inset-0 opacity-50"
        aria-hidden="true"
        style={{
          background: "radial-gradient(ellipse at center, var(--accent-soft) 0%, transparent 70%)",
        }}
      />

      <div className="relative mx-auto max-w-3xl px-4 text-center sm:px-6">
        <h2 className="text-3xl font-bold tracking-tight text-[var(--label-primary)] sm:text-5xl">
          Готовы <span className="gradient-text">сэкономить</span> на закупках?
        </h2>
        <p className="mt-4 text-lg text-[var(--label-secondary)] leading-relaxed">
          Первые 50 заявок обрабатываются бесплатно. Никаких подписок — только результат.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => router.push("/lk/requests/new")}
            className="relative overflow-hidden inline-flex items-center gap-2 rounded-[var(--radius-full)] gradient-bg px-8 py-4 text-base font-semibold text-white shadow-medium hover:shadow-glow active:scale-[0.97] transition-all duration-200 btn-shimmer"
          >
            Начать бесплатно
            <ArrowRight className="h-5 w-5" />
          </button>
          <a
            href="mailto:info@minitender.ru"
            className="inline-flex items-center gap-2 rounded-[var(--radius-full)] border border-[var(--separator)] bg-[var(--bg-tertiary)] px-8 py-4 text-base font-semibold text-[var(--label-primary)] shadow-xs hover:shadow-small hover:border-[var(--accent)]/20 transition-all duration-200"
          >
            <Mail className="h-4 w-4" />
            Связаться с нами
          </a>
        </div>

        <p className="mt-6 text-xs text-[var(--label-quaternary)]">
          Корпоративный доступ: info@minitender.ru
        </p>
      </div>
    </section>
  );
}
CTA

# ============================================================
# 8/8 frontend/app/lk/layout.tsx
# ============================================================
echo "📝 [8/8] frontend/app/lk/layout.tsx"
cat > frontend/app/lk/layout.tsx << 'LKLAYOUT'
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { HardHat, ListPlus, Truck, LogOut, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme";
import { getMe, logout } from "@/lib/api";

const navItems = [
  { href: "/lk/requests", label: "Мои заявки", icon: ListPlus },
  { href: "/lk/requests/new", label: "Новая заявка", icon: ListPlus },
  { href: "/lk/suppliers", label: "Поставщики", icon: Truck },
];

export default function LkLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    getMe().then(setUser).catch(() => {});
  }, []);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen flex bg-[var(--bg-ground)]">
      <a
        href="#lk-main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[1000] focus:px-3 focus:py-2 focus:rounded-md focus:bg-[var(--accent)] focus:text-white"
      >
        К содержимому
      </a>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 inset-x-0 z-[500] h-14 glass border-b border-[var(--separator)] flex items-center gap-2 px-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? "Закрыть меню" : "Открыть меню"}
          aria-expanded={menuOpen}
          aria-controls="lk-nav"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-[var(--radius-sm)] gradient-bg flex items-center justify-center">
            <HardHat className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold tracking-tight text-[var(--label-primary)]">Минитендер</span>
        </Link>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>

      {menuOpen && (
        <div
          className="md:hidden fixed inset-0 z-[499] bg-black/40 backdrop-blur-sm"
          onClick={() => setMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        id="lk-nav"
        className={
          "w-64 bg-[var(--sidebar-bg)] text-white flex flex-col fixed inset-y-0 left-0 z-[500] transition-transform duration-200 ease-out " +
          (menuOpen ? "translate-x-0" : "-translate-x-full") + " md:translate-x-0"
        }
      >
        <div className="p-6 border-b border-white/10 flex items-center justify-between gap-2">
          <Link href="/" className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-[var(--radius-sm)] gradient-bg flex items-center justify-center shrink-0">
              <HardHat className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight truncate">Минитендер</span>
          </Link>
          <ThemeToggle className="hidden md:inline-flex" />
        </div>

        <nav className="flex-1 p-4 space-y-1" aria-label="Основная навигация">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={
                  "flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] transition-all duration-200 text-sm font-medium " +
                  (active
                    ? "bg-white/12 text-white shadow-sm"
                    : "text-white/50 hover:text-white hover:bg-white/[0.08]")
                }
              >
                <item.icon className="w-5 h-5" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="px-3 py-2 text-sm text-white/35 truncate" title={user?.email || ""}>
            {user?.email || ""}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-[var(--radius-md)] text-white/35 hover:text-white/60 hover:bg-white/5 transition-all duration-200 text-sm mt-1 justify-start"
          >
            <LogOut className="w-5 h-5" aria-hidden="true" />
            Выйти
          </Button>
        </div>
      </aside>

      <main
        id="lk-main"
        className="flex-1 md:ml-64 p-4 pt-20 md:p-8 w-full min-w-0"
      >
        {children}
      </main>
    </div>
  );
}
LKLAYOUT

# ============================================================
# COMMIT & PUSH
# ============================================================
echo ""
echo "📦 Коммитим изменения..."
git add -A
git commit -m "feat(frontend): modern redesign v3.0 + fix(ci)

Design System v3.0:
- Unified indigo/violet gradient palette
- Glassmorphism panels with backdrop-blur
- Mesh gradient backgrounds
- Multi-layer shadows (xs/small/medium/large/glow)
- Larger border radii (6-24px + full)
- Shimmer animation on CTA buttons
- Scroll reveal animations with stagger delays
- Card hover lift effect
- Full dark mode token parity

Landing Page:
- Floating pill navbar with glassmorphism
- Hero with mesh-gradient + dot grid
- Gradient text headlines
- Feature cards with hover-lift
- CTA with radial glow

LK Dashboard:
- Updated sidebar with gradient logo
- Active state with subtle glow
- Glass mobile header

CI Fixes:
- test.py: remove django.contrib.gis (no GDAL in CI)
- backend.yml: uv sync --extra dev, Python 3.13"

echo ""
echo "🚀 Пушим в origin..."
git push origin "$BRANCH"

echo ""
echo "============================================================"
echo "✅ ГОТОВО!"
echo ""
echo "Ветка: $BRANCH"
echo "Изменено файлов: 8"
echo ""
echo "Откройте PR:"
echo "https://github.com/karpukhingennadiy-cpu/stroyzakup/pull/new/$BRANCH"
echo "============================================================"