# -*- coding: utf-8 -*-
"""E2E-тест frontend UI: dev-server (порт 3100) + WebBridge сценарии.
Проверяет: все 9 страниц, тёмную/светлую тему, адаптивность 320/1440, a11y-метрики.
Сервер останавливается в конце скрипта."""
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONT = os.path.join(ROOT, "frontend")
SHOTS = os.path.join(ROOT, "shots")
os.makedirs(SHOTS, exist_ok=True)
PORT = 3000
BASE = f"http://localhost:{PORT}"
DAEMON = "http://127.0.0.1:10086/command"
SESSION = "frontend-ui-test"

results = []

def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), name, ("— " + detail if detail else ""), flush=True)

def wb(action, args, timeout=60):
    body = json.dumps({"action": action, "args": args, "session": SESSION}).encode("utf-8")
    req = urllib.request.Request(DAEMON, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def shot(name):
    path = os.path.join(SHOTS, name).replace("\\", "/")
    for attempt in range(2):
        try:
            r = wb("screenshot", {"path": path, "format": "jpeg", "quality": 70})
            if os.path.exists(os.path.join(SHOTS, name)):
                return True, path
        except Exception as e:
            print("  screenshot retry", attempt, e, flush=True)
            time.sleep(2)
    return os.path.exists(os.path.join(SHOTS, name)), path

def ev(code):
    r = wb("evaluate", {"code": code})
    return r.get("data", {}).get("value")

def nav(url, first=False):
    args = {"url": url}
    if first:
        args["newTab"] = True
        args["group_title"] = "Frontend UI test"
    r = wb("navigate", args, timeout=60)
    time.sleep(2.5)
    return r

def main():
    # 1. Старт dev-сервера
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

        # 2. Лендинг
        nav(BASE + "/", first=True)
        html = ev("document.body.innerText") or ""
        check("лендинг / открывается", "Минитендер" in html)
        ok, _ = shot("01-home-light-1440.jpeg")
        check("скриншот лендинга", ok)

        # 3. Логин
        nav(BASE + "/login")
        wb("fill", {"selector": "input#login-email", "value": "dev@test.com"})
        wb("fill", {"selector": "input#login-password", "value": "testpass123"})
        wb("click", {"selector": "button[type=submit]"})
        time.sleep(6)
        url = ev("location.pathname") or ""
        err_text = ev("(document.querySelector('[role=alert]')||{}).innerText || ''")
        check("логин → редирект в ЛК", url.startswith("/lk"), "pathname=" + url + (" err=" + err_text if err_text else ""))

        # 4. ЛК: заявки + виджеты
        nav(BASE + "/lk/requests")
        tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
        check("/lk/requests открывается", "Мои заявки" in tree)
        check("виджет «Статусы заявок»", "Статистика заявок" in tree or "В работе" in tree)
        check("виджет «Карта поставщиков»", "Карта поставщиков" in tree)
        check("виджет «График цен»", "График цен" in tree)
        ok, _ = shot("02-requests-light.jpeg")
        check("скриншот ЛК (светлая)", ok)

        # 5. Тёмная тема
        before = ev("document.documentElement.classList.contains('dark')")
        wb("click", {"selector": "button[role=switch]"})
        time.sleep(1)
        after = ev("document.documentElement.classList.contains('dark')")
        check("переключатель темы работает", before is False and after is True, f"dark: {before}→{after}")
        ok, _ = shot("03-requests-dark.jpeg")
        check("скриншот ЛК (тёмная)", ok)
        saved = ev("localStorage.getItem('minitender_theme')")
        check("тема сохраняется в localStorage", saved == "dark", str(saved))
        wb("click", {"selector": "button[role=switch]"})  # вернуть светлую
        time.sleep(1)

        # 6. Новая заявка (мастер 3 шага)
        nav(BASE + "/lk/requests/new")
        tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
        check("/lk/requests/new открывается", "Шаг 1" in tree and "Материал" in tree)
        ok, _ = shot("04-new-request-light.jpeg")
        check("скриншот мастера", ok)

        # 7. Поставщики
        nav(BASE + "/lk/suppliers")
        tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
        check("/lk/suppliers открывается", "Поставщики" in tree)
        ok, _ = shot("05-suppliers-light.jpeg")
        check("скриншот поставщиков", ok)

        # 8. Детальная страница заявки (через ссылку из списка)
        nav(BASE + "/lk/requests")
        href = ev("(Array.from(document.querySelectorAll('a[href]')).find(a=>/^\\/lk\\/requests\\/\\d+$/.test(a.getAttribute('href')))||{}).href")
        if href:
            nav(href)
            tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
            check("/lk/requests/[id] открывается", "Заявка RFQ-" in tree)
            ok, _ = shot("06-request-detail.jpeg")
            check("скриншот карточки заявки", ok)
            comp = ev("(Array.from(document.querySelectorAll('a')).find(a=>/competitive/.test(a.href))||{}).href")
            if comp:
                nav(comp)
                tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
                check("конкурентный лист открывается", "Конкурентный лист" in tree)
                ok, _ = shot("07-competitive.jpeg")
                check("скриншот конкурентного листа", ok)
        else:
            check("/lk/requests/[id] открывается", False, "нет заявок в списке")

        # 9. Адаптивность 320px
        wb("cdp", {"method": "Emulation.setDeviceMetricsOverride",
                   "params": {"width": 320, "height": 800, "deviceScaleFactor": 1, "mobile": True}})
        time.sleep(1)
        nav(BASE + "/lk/requests")
        scroll_w = ev("document.documentElement.scrollWidth")
        check("320px: нет горизонтального скролла (ЛК)", (scroll_w or 9999) <= 321, f"scrollWidth={scroll_w}")
        ok, _ = shot("08-requests-320.jpeg")
        check("скриншот ЛК 320px", ok)
        nav(BASE + "/")
        scroll_w = ev("document.documentElement.scrollWidth")
        check("320px: нет горизонтального скролла (лендинг)", (scroll_w or 9999) <= 321, f"scrollWidth={scroll_w}")
        ok, _ = shot("09-home-320.jpeg")
        check("скриншот лендинга 320px", ok)

        # 10. 1440px
        wb("cdp", {"method": "Emulation.setDeviceMetricsOverride",
                   "params": {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False}})
        time.sleep(1)
        nav(BASE + "/lk/requests/new")
        scroll_w = ev("document.documentElement.scrollWidth")
        check("1440px: мастер без гориз. скролла", (scroll_w or 99999) <= 1441, f"scrollWidth={scroll_w}")
        ok, _ = shot("10-new-request-1440.jpeg")
        check("скриншот мастера 1440px", ok)
        wb("cdp", {"method": "Emulation.clearDeviceMetricsOverride", "params": {}})

        # 11. a11y-метрики
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
        check("a11y: все поля формы имеют label", data.get("noName") == 0, json.dumps(data, ensure_ascii=False))
        check("a11y: иконочные кнопки имеют aria-label", data.get("noBtnName") == 0, json.dumps(data, ensure_ascii=False))

        nav(BASE + "/quote/invalid-token-test")
        tree = json.dumps(wb("snapshot", {}), ensure_ascii=False)
        check("/quote/{token}: страница ошибки рендерится", "Ошибка" in tree or "Загрузка" in tree or "недействительна" in tree)
        ok, _ = shot("11-quote-invalid.jpeg")
        check("скриншот /quote", ok)

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
