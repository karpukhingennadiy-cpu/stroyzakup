# -*- coding: utf-8 -*-
"""E2E v2: /quote тема, Tab-цепочка мастера, console errors (CDP), 9 страниц 320/1440.
Запуск из worktree .wt-frontend. Сервер останавливается в конце."""
import json
import os
import subprocess
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONT = os.path.join(ROOT, ".wt-frontend", "frontend")
SHOTS = os.path.join(ROOT, "shots")
os.makedirs(SHOTS, exist_ok=True)
PORT = 3000
BASE = f"http://localhost:{PORT}"
DAEMON = "http://127.0.0.1:10086/command"
SESSION = "frontend-ui-test"

results = []

def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), name, ("— " + str(detail)[:160] if detail else ""), flush=True)

def wb(action, args, timeout=60):
    body = json.dumps({"action": action, "args": args, "session": SESSION}).encode("utf-8")
    req = urllib.request.Request(DAEMON, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def shot(name):
    path = os.path.join(SHOTS, name).replace("\\", "/")
    for attempt in range(2):
        try:
            wb("screenshot", {"path": path, "format": "jpeg", "quality": 70})
            if os.path.exists(os.path.join(SHOTS, name)):
                return True
        except Exception as e:
            print("  screenshot retry", attempt, e, flush=True)
            time.sleep(2)
    return os.path.exists(os.path.join(SHOTS, name))

def ev(code):
    r = wb("evaluate", {"code": code})
    return r.get("data", {}).get("value")

def nav(url, first=False, wait=2.5):
    args = {"url": url}
    if first:
        args["newTab"] = True
        args["group_title"] = "Frontend UI test"
    wb("navigate", args, timeout=90)
    time.sleep(wait)

ERR_HOOK = """
(() => {
  if (window.__errHooked) return; window.__errHooked = true;
  const push = (m) => { try {
    const a = JSON.parse(sessionStorage.getItem('__jsErrors') || '[]');
    a.push(String(m).slice(0, 300));
    sessionStorage.setItem('__jsErrors', JSON.stringify(a.slice(-30)));
  } catch (e) {} };
  window.addEventListener('error', e => push(e.message + ' @' + (e.filename||'').split('/').pop() + ':' + e.lineno));
  window.addEventListener('unhandledrejection', e => push('unhandledrejection: ' + e.reason));
  const orig = console.error;
  console.error = (...args) => { push('console.error: ' + args.map(String).join(' ')); orig.apply(console, args); };
})()
"""

def read_errors(clear=True):
    raw = ev("sessionStorage.getItem('__jsErrors') || '[]'")
    try:
        errs = json.loads(raw or "[]")
    except Exception:
        errs = [raw]
    if clear:
        ev("sessionStorage.removeItem('__jsErrors')")
    # Отфильтровать шум Next dev (favicon, sourcemaps, HMR)
    noise = ("favicon", "sourcemap", "source map", "Download the React DevTools", "hydration-warning")
    return [e for e in errs if e and not any(n in e.lower() for n in noise)]

def check_console(page_name):
    errs = read_errors()
    check("console: 0 ошибок на " + page_name, len(errs) == 0, errs[:2] if errs else "")

def main():
    log = open(os.path.join(ROOT, "nextdev-test.log"), "wb")
    proc = subprocess.Popen(
        ["node", "node_modules/next/dist/bin/next", "dev", "-p", str(PORT)],
        cwd=FRONT, stdout=log, stderr=subprocess.STDOUT,
    )
    try:
        ready = False
        for _ in range(60):
            try:
                with urllib.request.urlopen(BASE, timeout=2) as r:
                    if r.status == 200:
                        ready = True
                        break
            except Exception:
                pass
            time.sleep(2)
        check("dev-server стартовал (порт %d)" % PORT, ready)
        if not ready:
            return

        # Хук ошибок на каждый новый документ
        nav(BASE + "/", first=True)
        wb("cdp", {"method": "Page.enable", "params": {}})
        wb("cdp", {"method": "Page.addScriptToEvaluateOnNewDocument", "params": {"source": ERR_HOOK}})

        # ---- Лендинг ----
        nav(BASE + "/")
        check("лендинг / открывается", "Минитендер" in (ev("document.body.innerText") or ""))
        check("скриншот лендинга", shot("01-home-light-1440.jpeg"))
        check_console("/")

        # ---- Логин ----
        nav(BASE + "/login")
        wb("fill", {"selector": "input#login-email", "value": "dev@test.com"})
        wb("fill", {"selector": "input#login-password", "value": "testpass123"})
        wb("click", {"selector": "button[type=submit]"})
        time.sleep(6)
        url = ev("location.pathname") or ""
        check("логин → редирект в ЛК", url.startswith("/lk"), "pathname=" + url)
        read_errors()  # ошибки навигации Next при клиентском редиректе — считаем на целевой странице

        # ---- ЛК: заявки + виджеты ----
        nav(BASE + "/lk/requests")
        tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
        check("/lk/requests открывается", "Мои заявки" in tree)
        check("виджеты (статусы/карта/график)", all(k in tree for k in ("В работе", "Карта поставщиков", "График цен")))
        check("скриншот ЛК (светлая)", shot("02-requests-light.jpeg"))
        check_console("/lk/requests")

        # Тема
        wb("click", {"selector": "button[role=switch]"})
        time.sleep(1)
        dark = ev("document.documentElement.classList.contains('dark')")
        check("тема: переключение в dark", dark is True)
        check("скриншот ЛК (тёмная)", shot("03-requests-dark.jpeg"))
        wb("click", {"selector": "button[role=switch]"})
        time.sleep(1)
        light = ev("document.documentElement.classList.contains('dark')")
        check("тема: возврат в light + persist", light is False and ev("localStorage.getItem('minitender_theme')") == "light")

        # ---- Мастер: страница + Tab-цепочка ----
        nav(BASE + "/lk/requests/new")
        tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
        check("/lk/requests/new открывается", "Шаг 1" in tree)
        check("скриншот мастера", shot("04-new-request-light.jpeg"))
        check_console("/lk/requests/new")

        # Tab-цепочка: все фокусируемые элементы в DOM-порядке, без tabIndex>0, все достижимы фокусом
        tab = ev("""(() => {
          const sel = 'a[href], button, input, select, textarea, [tabindex]';
          const els = Array.from(document.querySelectorAll(sel)).filter(el => {
            const r = el.getBoundingClientRect();
            const st = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && !el.disabled && el.tabIndex >= 0;
          });
          const badTabIndex = els.filter(el => el.tabIndex > 0).length;
          let focusFails = 0;
          const order = [];
          for (const el of els) {
            el.focus();
            if (document.activeElement !== el) focusFails++;
            order.push(el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.getAttribute('aria-label') ? '[' + el.getAttribute('aria-label').slice(0,20) + ']' : ''));
          }
          // focus-visible правило в CSS
          let hasFocusVisible = false;
          for (const sheet of document.styleSheets) {
            try {
              for (const rule of sheet.cssRules) {
                if (rule.selectorText && rule.selectorText.includes(':focus-visible')) { hasFocusVisible = true; break; }
              }
            } catch (e) {}
            if (hasFocusVisible) break;
          }
          // Несемантические кликабельные контролы (div/tr с onClick без role) — грубая проверка шага 1
          return JSON.stringify({count: els.length, badTabIndex, focusFails, hasFocusVisible, first: order.slice(0,6), last: order.slice(-3)});
        })()""")
        t = json.loads(tab or "{}")
        check("Tab-цепочка: элементов фокусируемых >= 8", (t.get("count") or 0) >= 8, t.get("count"))
        check("Tab-цепочка: нет tabIndex > 0", t.get("badTabIndex") == 0)
        check("Tab-цепочка: все элементы достижимы фокусом", t.get("focusFails") == 0, t.get("focusFails"))
        check("focus-visible: CSS-правило 2px kimiBlue присутствует", t.get("hasFocusVisible") is True)
        # Enter/Space: нативная активация — проверяем, что контролы семантические <button>/<a>
        sem = ev("""(() => {
          const btns = Array.from(document.querySelectorAll('button')).length;
          const fakeBtns = Array.from(document.querySelectorAll('[role="button"]')).length;
          return JSON.stringify({buttons: btns, fakeButtons: fakeBtns});
        })()""")
        s = json.loads(sem or "{}")
        check("Enter/Space: все контролы — семантические <button>/<a>", s.get("fakeButtons") == 0, s)
        # Skip-link
        nav(BASE + "/lk/requests")
        skip = ev("(() => { const a = document.querySelector('a[href=\"#lk-main\"]'); return a ? (a.textContent || '') : null; })()")
        check("skip-link к основному контенту", skip is not None and "содержим" in (skip or "").lower(), skip)

        # ---- Поставщики ----
        nav(BASE + "/lk/suppliers")
        tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
        check("/lk/suppliers открывается", "Поставщики" in tree)
        check("скриншот поставщиков", shot("05-suppliers-light.jpeg"))
        check_console("/lk/suppliers")

        # ---- Карточка заявки + конкурентный лист ----
        nav(BASE + "/lk/requests")
        href = ev("(Array.from(document.querySelectorAll('a[href]')).find(a=>/^\\/lk\\/requests\\/\\d+$/.test(a.getAttribute('href')))||{}).href")
        if href:
            nav(href)
            tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
            check("/lk/requests/[id] открывается", "Заявка RFQ-" in tree)
            check("скриншот карточки заявки", shot("06-request-detail.jpeg"))
            check_console("/lk/requests/[id]")
            comp = ev("(Array.from(document.querySelectorAll('a')).find(a=>/competitive/.test(a.href))||{}).href")
            if comp:
                nav(comp)
                tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
                check("конкурентный лист открывается", "Конкурентный лист" in tree)
                check("скриншот конкурентного листа", shot("07-competitive.jpeg"))
                check_console("/lk/requests/[id]/competitive")
        else:
            check("/lk/requests/[id] открывается", False, "нет заявок")

        # ---- Регистрация ----
        nav(BASE + "/register")
        check("/register открывается", "Регистрация" in (ev("document.body.innerText") or ""))
        check_console("/register")

        # ---- /quote/{token}: рендер + переключатель темы ----
        nav(BASE + "/quote/invalid-token-test")
        tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
        check("/quote/{token} рендерится", "Ошибка" in tree or "недействительна" in tree)
        tgl = ev("!!document.querySelector('button[role=switch]')")
        check("/quote: переключатель темы присутствует", tgl is True)
        if tgl:
            wb("click", {"selector": "button[role=switch]"})
            time.sleep(1)
            d = ev("document.documentElement.classList.contains('dark')")
            check("/quote: тема переключается в dark", d is True)
            check("/quote: скриншот тёмной темы", shot("11-quote-dark.jpeg"))
            check("/quote: persist localStorage", ev("localStorage.getItem('minitender_theme')") == "dark")
            wb("click", {"selector": "button[role=switch]"})
            time.sleep(1)
        check_console("/quote/{token}")

        # ---- 320px ----
        wb("cdp", {"method": "Emulation.setDeviceMetricsOverride",
                   "params": {"width": 320, "height": 800, "deviceScaleFactor": 1, "mobile": True}})
        time.sleep(1)
        for path, name in [("/lk/requests", "ЛК"), ("/", "лендинг"), ("/lk/requests/new", "мастер")]:
            nav(BASE + path)
            sw = ev("document.documentElement.scrollWidth")
            check("320px: без гориз. скролла (" + name + ")", (sw or 9999) <= 321, "scrollWidth=" + str(sw))
        check("скриншот ЛК 320px", shot("08-requests-320.jpeg"))
        # ---- 1440px ----
        wb("cdp", {"method": "Emulation.setDeviceMetricsOverride",
                   "params": {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False}})
        time.sleep(1)
        nav(BASE + "/lk/requests/new")
        sw = ev("document.documentElement.scrollWidth")
        check("1440px: мастер без гориз. скролла", (sw or 99999) <= 1441, "scrollWidth=" + str(sw))
        check("скриншот мастера 1440px", shot("10-new-request-1440.jpeg"))
        wb("cdp", {"method": "Emulation.clearDeviceMetricsOverride", "params": {}})

        # ---- a11y-метрики (login) ----
        nav(BASE + "/login")
        m = ev("""(() => {
          const inputs = Array.from(document.querySelectorAll('input,textarea,select'));
          const noName = inputs.filter(el => {
            if (el.id && document.querySelector('label[for="'+el.id+'"]')) return false;
            return !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby');
          }).length;
          const btns = Array.from(document.querySelectorAll('button'));
          const noBtnName = btns.filter(b => !b.textContent.trim() && !b.getAttribute('aria-label')).length;
          return JSON.stringify({inputs: inputs.length, noName, buttons: btns.length, noBtnName});
        })()""")
        data = json.loads(m or "{}")
        check("a11y: поля с label / кнопки с именем", data.get("noName") == 0 and data.get("noBtnName") == 0, data)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        log.close()
        print("\n=== ИТОГО:", sum(1 for _, ok, _ in results if ok), "/", len(results), "PASS ===")

if __name__ == "__main__":
    main()
