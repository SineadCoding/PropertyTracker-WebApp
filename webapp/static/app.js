async function fetchListings() {
    const res = await fetch('/api/listings');
    return await res.json();
}

function renderListings(listings) {
    const container = document.getElementById('listings');
    container.innerHTML = '';
    listings.forEach(prop => {
        // Only hide listings with no title AND no location
        if (!prop.title && !prop.location) return;
        const card = document.createElement('div');
        card.className = 'property-card';
        // Ensure link starts with http/https
        let link = prop.link;
        if (link && !/^https?:\/\//i.test(link)) {
            link = 'https://' + link;
        }
        card.innerHTML = `
            <div class="property-title">${prop.title || 'No Title'}</div>
            <div class="property-details">Location: ${prop.location || 'Unknown'} | Price: ${typeof prop.price === 'number' ? 'R' + prop.price.toLocaleString() : prop.price} | GBP: £${prop.price_gbp !== undefined && prop.price_gbp !== null ? prop.price_gbp.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'N/A'} | Agency: ${prop.agency || 'Unknown'}</div>
            <div class="property-details">Date: ${prop.date} | <a class="property-link" href="${link || '#'}" target="_blank" rel="noopener noreferrer">View Listing</a></div>
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
    // Show loading indicator
    const container = document.getElementById('listings');
    container.innerHTML = '<div class="loading">Refreshing listings, please wait...</div>';
    await fetch('/api/refresh', { method: 'POST' });
    // Wait 5 seconds for backend to finish scraping
    setTimeout(async () => {
        const listings = await fetchListings();
        applyFilterSort(listings);
    }, 5000);
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
    if (filtered.length === 0) {
        document.getElementById('listings').innerHTML = '<div class="no-listings">No properties found. Please try again later or refresh.</div>';
    } else {
        renderListings(filtered);
    }
}

window.onload = async () => {
    const listings = await fetchListings();
    applyFilterSort(listings);
};
