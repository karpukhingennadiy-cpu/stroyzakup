# Changelog — Frontend UI/UX (PR #3)

## Новое
- Тёмная/светлая тема с переключателем и persist в localStorage
- Dashboard-виджеты: статусы заявок, карта поставщиков, график цен
- Переключатель темы на публичной странице /quote/{token}
- Skip-link для перехода к основному контенту

## Исправлено
- Мобильная адаптивность (320px): таблицы → карточки-формы
- Лендинг: убран горизонтальный скролл (<380px)
- Inline-стили на /quote/{token} → Tailwind + компоненты
- Формы: связь label с input через htmlFor/id
- Мобильное меню: закрытие по Escape + aria-expanded

## Доступность (WCAG 2.1 AA)
- Контраст ≥4.5:1 (скорректированы danger/success/warning)
- aria-labels на иконочных кнопках
- Клавиатурная навигация (Tab/Enter/Escape)
- Фокус-индикаторы (2px kimiBlue)

## Тестирование
- WebBridge: 45/45 PASS
- Breakpoints: 320/768/1024/1440px
- Скриншоты: shots/01–11.jpeg
