(() => {
    const feedback = document.getElementById('global-feedback');
    let feedbackTimer;

    function showFeedback(message, isError = false) {
        if (!feedback) return;
        feedback.textContent = message;
        feedback.classList.toggle('is-error', isError);
        feedback.classList.add('is-visible');
        window.clearTimeout(feedbackTimer);
        feedbackTimer = window.setTimeout(() => feedback.classList.remove('is-visible'), 2800);
    }

    function formatMoney(value) {
        return new Intl.NumberFormat('ru-RU', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value) + ' ₽';
    }

    function setCartCount(count) {
        const badge = document.getElementById('nav-cart-count');
        if (!badge) return;
        badge.textContent = count;
        badge.hidden = count < 1;
    }

    function recalculateVisibleTotal() {
        const inputs = document.querySelectorAll('#cart-items-region input[data-unit-price]');
        if (!inputs.length) return;
        let totalCents = 0;
        inputs.forEach((input) => {
            const quantity = Math.max(1, Number.parseInt(input.value, 10) || 1);
            const unitCents = Math.round(Number.parseFloat(input.dataset.unitPrice) * 100);
            const lineCents = unitCents * quantity;
            totalCents += lineCents;
            const lineTotal = input.closest('.checkout-item')?.querySelector('[data-line-total]');
            if (lineTotal) lineTotal.textContent = formatMoney(lineCents / 100);
        });
        const totalText = formatMoney(totalCents / 100);
        const total = document.getElementById('cart-grand-total');
        const buttonTotal = document.getElementById('checkout-button-total');
        if (total) total.textContent = totalText;
        if (buttonTotal) buttonTotal.textContent = totalText;
    }

    async function submitCartForm(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                },
            });
            const result = await response.json();
            if (!response.ok || !result.ok) {
                throw new Error(result.message || 'Не удалось обновить корзину. Попробуйте ещё раз.');
            }

            const region = document.getElementById('cart-items-region');
            if (region && result.items_html !== undefined) region.innerHTML = result.items_html;
            setCartCount(result.item_count);

            const total = document.getElementById('cart-grand-total');
            const buttonTotal = document.getElementById('checkout-button-total');
            const count = document.getElementById('cart-item-count');
            if (total) total.textContent = formatMoney(Number(result.total));
            if (buttonTotal) buttonTotal.textContent = formatMoney(Number(result.total));
            if (count) count.textContent = `${result.item_count} шт.`;

            const checkoutButton = document.querySelector('.checkout-submit');
            if (checkoutButton) checkoutButton.disabled = !result.has_items;
            if (submitButton && !submitButton.closest('.checkout-submit')) submitButton.disabled = false;
            showFeedback(result.message);
        } catch (error) {
            showFeedback(error.message || 'Ошибка соединения. Проверьте интернет и повторите попытку.', true);
            if (submitButton) submitButton.disabled = false;
        }
    }

    document.addEventListener('submit', (event) => {
        const form = event.target.closest('form[data-cart-action]');
        if (!form) return;
        event.preventDefault();
        submitCartForm(form);
    });

    document.addEventListener('click', (event) => {
        const step = event.target.closest('[data-quantity-step]');
        if (!step) return;
        const form = step.closest('form');
        const input = form?.querySelector('input[name="quantity"]');
        if (!input) return;
        const current = Number.parseInt(input.value, 10) || 1;
        const min = Number.parseInt(input.min, 10) || 1;
        const max = Number.parseInt(input.max, 10) || 99;
        input.value = String(Math.min(max, Math.max(min, current + Number(step.dataset.quantityStep))));
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    });

    let updateTimer;
    document.addEventListener('input', (event) => {
        const input = event.target.closest('#cart-items-region input[data-unit-price]');
        if (!input) return;
        recalculateVisibleTotal();
        window.clearTimeout(updateTimer);
        updateTimer = window.setTimeout(() => {
            const form = input.closest('form[data-cart-action]');
            if (form && input.value !== '') form.requestSubmit();
        }, 500);
    });

    document.addEventListener('change', (event) => {
        const input = event.target.closest('#cart-items-region input[data-unit-price]');
        if (!input) return;
        window.clearTimeout(updateTimer);
        const form = input.closest('form[data-cart-action]');
        if (form && input.value !== '') form.requestSubmit();
    });

    recalculateVisibleTotal();
})();
