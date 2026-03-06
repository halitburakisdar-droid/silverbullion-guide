// Free metals price API — no CORS issues
// Uses metals-api.com free public endpoint & fallback
async function fetchPrices() {
    let agPrice = null, auPrice = null;

    // Try metals.live (public, no key, no CORS)
    try {
        const r = await fetch('https://api.metals.live/v1/spot/silver,gold');
        if (r.ok) {
            const data = await r.json();
            data.forEach(item => {
                if (item.silver) agPrice = parseFloat(item.silver);
                if (item.gold)   auPrice  = parseFloat(item.gold);
            });
        }
    } catch {}

    // Fallback: frankfurter.app for XAG/XAU rates
    if (!agPrice) {
        try {
            const r = await fetch('https://api.frankfurter.app/latest?from=XAG&to=USD');
            if (r.ok) {
                const d = await r.json();
                agPrice = 1 / parseFloat(d.rates.USD);
            }
        } catch {}
    }

    if (agPrice) {
        const ag = '$' + agPrice.toFixed(2);
        ['ag-usd','t-ag','t-ag2'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = ag;
        });
    }

    if (auPrice) {
        const au = '$' + auPrice.toFixed(0);
        ['au-usd','t-au','t-au2'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = au;
        });
    }

    if (agPrice && auPrice) {
        const ratio = (auPrice / agPrice).toFixed(1) + ':1';
        ['gsr','t-gsr','t-gsr2'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = ratio;
        });
    }
}

fetchPrices();
