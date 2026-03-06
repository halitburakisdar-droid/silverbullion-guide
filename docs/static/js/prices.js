// Live price fetcher using free Metal Price API (no key needed for basic)
async function fetchPrices() {
  try {
    // Using open.er-api.com for currency rates as fallback
    // Primary: metals-api free tier
    const res = await fetch('https://query1.finance.yahoo.com/v8/finance/chart/SI%3DF?interval=1d&range=1d', {
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error();
    const data = await res.json();
    const price = data?.chart?.result?.[0]?.meta?.regularMarketPrice;
    if (price) updateSilver(price);
  } catch {
    // Fallback static display
    setStatic();
  }

  try {
    const res = await fetch('https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF?interval=1d&range=1d');
    const data = await res.json();
    const price = data?.chart?.result?.[0]?.meta?.regularMarketPrice;
    if (price) updateGold(price);
  } catch {}
}

function updateSilver(price) {
  const fmt = '$' + price.toFixed(2);
  ['ag-usd', 't-ag', 't-ag2'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = fmt;
  });
  computeGSR();
}

function updateGold(price) {
  const fmt = '$' + price.toFixed(0);
  ['au-usd', 't-au', 't-au2'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = fmt;
  });
  computeGSR();
}

function computeGSR() {
  const ag = parseFloat(document.getElementById('ag-usd')?.textContent?.replace('$',''));
  const au = parseFloat(document.getElementById('au-usd')?.textContent?.replace('$',''));
  if (ag && au) {
    const ratio = (au / ag).toFixed(1);
    ['gsr', 't-gsr', 't-gsr2'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = ratio + ':1';
    });
  }
}

function setStatic() {
  if (document.getElementById('ag-usd')) document.getElementById('ag-usd').textContent = 'See chart';
}

fetchPrices();
