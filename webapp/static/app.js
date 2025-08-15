async function fetchListings() {
    const res = await fetch('/api/listings');
    return await res.json();
}

function renderListings(listings) {
    const container = document.getElementById('listings');
    container.innerHTML = '';
    listings.forEach(prop => {
        // Hide listings with missing info or broken links
        if (!prop.title || !prop.location || !prop.link || prop.link.includes('propertytracker-webapp')) return;
        const card = document.createElement('div');
        card.className = 'property-card';
        // Ensure link starts with http/https
        let link = prop.link;
        if (link && !/^https?:\/\//i.test(link)) {
            link = 'https://' + link;
        }
        card.innerHTML = `
            <div class="property-title">${prop.title}</div>
            <div class="property-details">Location: ${prop.location} | Price: ${typeof prop.price === 'number' ? 'R' + prop.price.toLocaleString() : prop.price} | GBP: £${prop.price_gbp !== undefined && prop.price_gbp !== null ? prop.price_gbp.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'N/A'} | Agency: ${prop.agency}</div>
            <div class="property-details">Date: ${prop.date} | <a class="property-link" href="${link}" target="_blank" rel="noopener noreferrer">View Listing</a></div>
            <div class="property-status">Status: ${prop.status}${prop.sold ? ' (Sold)' : ''}</div>
        `;
        container.appendChild(card);
    });
}

function sortListings(listings, key) {
    if (key === 'price_asc') {
        return listings.slice().sort((a, b) => {
            let aPrice = typeof a.price === 'number' ? a.price : parseFloat(a.price) || Number.MAX_VALUE;
            let bPrice = typeof b.price === 'number' ? b.price : parseFloat(b.price) || Number.MAX_VALUE;
            return aPrice - bPrice;
        });
    }
    if (key === 'price_desc') {
        return listings.slice().sort((a, b) => {
            let aPrice = typeof a.price === 'number' ? a.price : parseFloat(a.price) || Number.MIN_VALUE;
            let bPrice = typeof b.price === 'number' ? b.price : parseFloat(b.price) || Number.MIN_VALUE;
            return bPrice - aPrice;
        });
    }
    if (key === 'title_az') {
        return listings.slice().sort((a, b) => a.title.localeCompare(b.title));
    }
    if (key === 'title_za') {
        return listings.slice().sort((a, b) => b.title.localeCompare(a.title));
    }
    if (key === 'date') {
        return listings.slice().sort((a, b) => new Date(b.date) - new Date(a.date));
    }
    return listings;
}

document.getElementById('refreshBtn').onclick = async () => {
    // Trigger backend refresh (scrape live)
    await fetch('/api/refresh', { method: 'POST' });
    // Now reload listings
    const listings = await fetchListings();
    applyFilterSort(listings);
};

document.getElementById('sortSelect').onchange = async (e) => {
    const listings = await fetchListings();
    applyFilterSort(listings);
};

document.getElementById('filterInput').oninput = async (e) => {
    const listings = await fetchListings();
    applyFilterSort(listings);
};

async function applyFilterSort(listings) {
    const filterVal = document.getElementById('filterInput').value.toLowerCase();
    const sortKey = document.getElementById('sortSelect').value;
    let filtered = listings.filter(prop =>
        prop.location.toLowerCase().includes(filterVal) ||
        prop.agency.toLowerCase().includes(filterVal)
    );
    filtered = sortListings(filtered, sortKey);
    renderListings(filtered);
}

window.onload = async () => {
    const listings = await fetchListings();
    applyFilterSort(listings);
};
